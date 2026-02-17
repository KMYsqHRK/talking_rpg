"""
Pygame RPG酒場 勧誘シーン GUI
Party_invitation.py の Phi2DialogueSimulator と統合
"""

import pygame
import sys
import os
import threading
from typing import Dict, List, Optional, Tuple

from Party_invitation import Phi2DialogueSimulator, MAX_TURNS

# ============================================
# 定数
# ============================================

WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
FPS = 30

# レイアウト
LEFT_PANEL_W = 380
RIGHT_PANEL_X = LEFT_PANEL_W
RIGHT_PANEL_W = WINDOW_WIDTH - LEFT_PANEL_W
PADDING = 20

# ポートレート
PORTRAIT_W = 250
PORTRAIT_H = 320

# カラーパレット（中世酒場風）
C_WOOD = (101, 67, 33)
C_WOOD_DARK = (61, 43, 31)
C_WOOD_LIGHT = (139, 90, 43)
C_PARCHMENT = (245, 235, 220)
C_PARCHMENT_DARK = (220, 200, 170)
C_GOLD = (255, 215, 0)
C_GOLD_DIM = (180, 150, 30)
C_CHARCOAL = (40, 40, 40)
C_WHITE = (255, 255, 255)
C_BLACK = (0, 0, 0)
C_USER_BG = (170, 195, 220)
C_NPC_BG = (220, 200, 175)
C_GREEN = (76, 175, 80)
C_RED = (211, 47, 47)
C_ORANGE = (255, 152, 0)
C_YELLOW = (255, 235, 59)
C_GREY = (160, 160, 160)
C_INPUT_BG = (255, 250, 240)
C_FIRELIGHT = (255, 147, 41)


# ============================================
# UIButton
# ============================================

class UIButton:
    """再利用可能なボタン"""

    def __init__(self, rect: pygame.Rect, text: str,
                 color: Tuple, hover_color: Tuple,
                 text_color: Tuple = C_CHARCOAL,
                 disabled_color: Tuple = C_GREY):
        self.rect = rect
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.text_color = text_color
        self.disabled_color = disabled_color
        self.enabled = True

    def draw(self, surface: pygame.Surface, font: pygame.font.Font):
        mouse = pygame.mouse.get_pos()
        if not self.enabled:
            bg = self.disabled_color
        elif self.rect.collidepoint(mouse):
            bg = self.hover_color
        else:
            bg = self.color

        # ボタン本体
        pygame.draw.rect(surface, bg, self.rect, border_radius=6)
        pygame.draw.rect(surface, C_WOOD_DARK, self.rect, 2, border_radius=6)

        # テキスト
        txt = font.render(self.text, True,
                          self.text_color if self.enabled else C_WHITE)
        txt_rect = txt.get_rect(center=self.rect.center)
        surface.blit(txt, txt_rect)

    def clicked(self, pos: Tuple[int, int]) -> bool:
        return self.enabled and self.rect.collidepoint(pos)


# ============================================
# TavernGUI
# ============================================

class TavernGUI:
    """メインのタバーン勧誘GUIクラス"""

    # 状態
    ST_LOADING = "loading"
    ST_WAITING = "waiting"
    ST_GREETING = "greeting"
    ST_TALKING = "talking"
    ST_GENERATING = "generating"
    ST_JUDGING = "judging"
    ST_VERDICT = "verdict"

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("RPG Tavern - Party Recruitment")
        self.clock = pygame.time.Clock()

        # フォント初期化
        self._init_fonts()

        # アセット読み込み
        self._load_assets()

        # 状態
        self.state = self.ST_LOADING
        self.character: Optional[Dict] = None
        self.turn_count = 0
        self.messages: List[Dict] = []  # {speaker, text, is_user}
        self.input_text = ""
        self.input_active = True
        self.scroll_offset = 0
        self.max_scroll = 0

        # 判定結果
        self.verdict_result: Optional[bool] = None
        self.verdict_prob = 0.0
        self.verdict_details: Dict = {}
        self.verdict_frame = 0

        # AI応答スレッド
        self._ai_busy = False
        self._ai_response: Optional[str] = None

        # ボタン
        self.btn_new = UIButton(
            pygame.Rect(LEFT_PANEL_W // 2 - 90, 700, 180, 50),
            "New Character", C_GOLD, C_GOLD_DIM, C_CHARCOAL
        )
        self.btn_send = UIButton(
            pygame.Rect(WINDOW_WIDTH - PADDING - 100,
                        WINDOW_HEIGHT - 100, 100, 40),
            "Send", C_GOLD, C_GOLD_DIM, C_CHARCOAL
        )

        # Simulator読み込み（バックグラウンド）
        self.simulator: Optional[Phi2DialogueSimulator] = None
        self._loading_thread = threading.Thread(target=self._load_simulator,
                                                daemon=True)
        self._loading_thread.start()

    # ---------- 初期化ヘルパー ----------

    def _init_fonts(self):
        """フォント初期化"""
        # システムフォント検索
        candidates = ["notosanscjkjp", "notosans", "dejavusans",
                       "liberationsans", "arial", "freesans"]
        font_name = None
        for name in candidates:
            if pygame.font.match_font(name):
                font_name = name
                break

        if font_name:
            path = pygame.font.match_font(font_name)
            self.font_title = pygame.font.Font(path, 32)
            self.font_header = pygame.font.Font(path, 22)
            self.font_body = pygame.font.Font(path, 18)
            self.font_small = pygame.font.Font(path, 14)
            self.font_stat = pygame.font.Font(path, 16)
        else:
            self.font_title = pygame.font.Font(None, 36)
            self.font_header = pygame.font.Font(None, 26)
            self.font_body = pygame.font.Font(None, 20)
            self.font_small = pygame.font.Font(None, 16)
            self.font_stat = pygame.font.Font(None, 18)

    def _load_assets(self):
        """画像アセット読み込み"""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        portrait_path = os.path.join(base_dir, "img", "mage-man.png")

        if os.path.exists(portrait_path):
            raw = pygame.image.load(portrait_path).convert_alpha()
            self.portrait_img = pygame.transform.smoothscale(
                raw, (PORTRAIT_W, PORTRAIT_H))
        else:
            # フォールバック: プレースホルダー
            self.portrait_img = pygame.Surface((PORTRAIT_W, PORTRAIT_H))
            self.portrait_img.fill(C_WOOD_DARK)

    def _load_simulator(self):
        """バックグラウンドでPhi-2モデルをロード"""
        self.simulator = Phi2DialogueSimulator(use_gpu=True)
        self.state = self.ST_WAITING

    # ---------- 描画メソッド ----------

    def _draw_background(self):
        """タバーン風の背景"""
        self.screen.fill(C_WOOD)

        # 木目調の横線
        for y in range(0, WINDOW_HEIGHT, 40):
            c = (C_WOOD[0] - 8, C_WOOD[1] - 5, C_WOOD[2] - 3)
            pygame.draw.line(self.screen, c, (0, y), (WINDOW_WIDTH, y))

        # 左パネル背景
        left_bg = pygame.Surface((LEFT_PANEL_W, WINDOW_HEIGHT), pygame.SRCALPHA)
        left_bg.fill((*C_WOOD_DARK, 180))
        self.screen.blit(left_bg, (0, 0))

        # 右パネル背景
        right_bg = pygame.Surface((RIGHT_PANEL_W, WINDOW_HEIGHT), pygame.SRCALPHA)
        right_bg.fill((*C_WOOD_DARK, 120))
        self.screen.blit(right_bg, (LEFT_PANEL_W, 0))

        # パネル境界線
        pygame.draw.line(self.screen, C_GOLD_DIM,
                         (LEFT_PANEL_W, 0), (LEFT_PANEL_W, WINDOW_HEIGHT), 2)

        # タイトルバー
        title_rect = pygame.Rect(0, 0, WINDOW_WIDTH, 50)
        pygame.draw.rect(self.screen, C_WOOD_DARK, title_rect)
        pygame.draw.line(self.screen, C_GOLD,
                         (0, 50), (WINDOW_WIDTH, 50), 2)
        title = self.font_title.render("Tavern Recruitment", True, C_GOLD)
        self.screen.blit(title, (WINDOW_WIDTH // 2 - title.get_width() // 2, 8))

    def _draw_portrait(self):
        """キャラクター肖像画"""
        x = LEFT_PANEL_W // 2 - PORTRAIT_W // 2
        y = 70

        if self.character:
            # 額縁
            frame = pygame.Rect(x - 6, y - 6,
                                PORTRAIT_W + 12, PORTRAIT_H + 12)
            pygame.draw.rect(self.screen, C_GOLD, frame, 3, border_radius=4)
            self.screen.blit(self.portrait_img, (x, y))
        else:
            # プレースホルダー
            frame = pygame.Rect(x - 6, y - 6,
                                PORTRAIT_W + 12, PORTRAIT_H + 12)
            pygame.draw.rect(self.screen, C_GREY, frame, 2, border_radius=4)
            placeholder = pygame.Surface((PORTRAIT_W, PORTRAIT_H))
            placeholder.fill(C_WOOD_DARK)
            q = self.font_title.render("?", True, C_GREY)
            placeholder.blit(q, (PORTRAIT_W // 2 - q.get_width() // 2,
                                 PORTRAIT_H // 2 - q.get_height() // 2))
            self.screen.blit(placeholder, (x, y))

    def _draw_character_info(self):
        """右パネル上部: キャラクター情報"""
        if not self.character:
            hint = self.font_body.render(
                'Click "New Character" to begin.', True, C_PARCHMENT)
            self.screen.blit(hint, (RIGHT_PANEL_X + PADDING, 80))
            return

        ch = self.character
        x = RIGHT_PANEL_X + PADDING
        y = 65

        # 名前
        name_surf = self.font_header.render(ch['name'], True, C_GOLD)
        self.screen.blit(name_surf, (x, y))
        y += 30

        # 職業・役割
        job_str = f"{ch['job']}  ({ch['role']})"
        job_surf = self.font_body.render(job_str, True, C_PARCHMENT)
        self.screen.blit(job_surf, (x, y))
        y += 24

        # 性格
        pers_str = f"Personality: {ch['personality']} - {ch['personality_desc']}"
        for line in self._wrap_text(pers_str, self.font_small,
                                    RIGHT_PANEL_W - PADDING * 2):
            surf = self.font_small.render(line, True, C_PARCHMENT_DARK)
            self.screen.blit(surf, (x, y))
            y += 18

        # 武器・能力
        y += 4
        wep = self.font_small.render(
            f"Weapon: {ch['weapon']}   |   Abilities: {ch['abilities']}",
            True, C_PARCHMENT_DARK)
        self.screen.blit(wep, (x, y))
        y += 22

        # ステータスバッジ
        self._draw_stats_badges(x, y, ch)

    def _draw_stats_badges(self, x: int, y: int, ch: Dict):
        """ステータスバッジ（6項目を横並び）"""
        stats = [
            ("HP", ch['hp']), ("ATK", ch['atk']), ("DEF", ch['def']),
            ("WIS", ch['wis']), ("LUC", ch['luc']), ("AGI", ch['agi']),
        ]
        badge_w = 80
        badge_h = 28
        gap = 8

        for i, (label, val) in enumerate(stats):
            bx = x + i * (badge_w + gap)
            rect = pygame.Rect(bx, y, badge_w, badge_h)

            # バッジ背景
            pygame.draw.rect(self.screen, C_WOOD_DARK, rect, border_radius=4)
            pygame.draw.rect(self.screen, C_GOLD_DIM, rect, 1, border_radius=4)

            # 値の色
            if val > 0:
                val_color = C_GREEN
                val_str = f"+{val}"
            elif val < 0:
                val_color = C_RED
                val_str = str(val)
            else:
                val_color = C_WHITE
                val_str = "0"

            txt = self.font_stat.render(f"{label} {val_str}", True, val_color)
            txt_rect = txt.get_rect(center=rect.center)
            self.screen.blit(txt, txt_rect)

    def _draw_dialogue(self):
        """会話履歴エリア（スクロール対応）"""
        area_x = RIGHT_PANEL_X + PADDING
        area_y = 220
        area_w = RIGHT_PANEL_W - PADDING * 2
        area_h = WINDOW_HEIGHT - 220 - 120  # 入力欄+ステータス分を引く

        # 背景パネル
        bg_rect = pygame.Rect(area_x - 5, area_y - 5, area_w + 10, area_h + 10)
        pygame.draw.rect(self.screen, (*C_WOOD_DARK, 200), bg_rect,
                         border_radius=6)
        pygame.draw.rect(self.screen, C_GOLD_DIM, bg_rect, 1, border_radius=6)

        # クリッピング
        clip_rect = pygame.Rect(area_x, area_y, area_w, area_h)
        self.screen.set_clip(clip_rect)

        # メッセージ描画
        msg_y = area_y + 8 - self.scroll_offset
        bubble_pad = 10
        max_text_w = area_w - 80

        total_height = 0
        for msg in self.messages:
            lines = self._wrap_text(msg['text'], self.font_body, max_text_w)
            line_h = self.font_body.get_linesize()
            bubble_h = len(lines) * line_h + bubble_pad * 2 + 4
            speaker_h = 18

            if msg['is_user']:
                # ユーザー: 右寄せ
                bubble_w = min(max_text_w + bubble_pad * 2,
                               max(self.font_body.size(l)[0] for l in lines)
                               + bubble_pad * 2)
                bx = area_x + area_w - bubble_w - 8
                bg_color = C_USER_BG
                # スピーカーラベル
                sp = self.font_small.render("You", True, C_PARCHMENT_DARK)
                if area_y <= msg_y + total_height <= area_y + area_h:
                    self.screen.blit(sp, (bx + bubble_w - sp.get_width(),
                                         msg_y + total_height))
            else:
                # NPC: 左寄せ
                bubble_w = min(max_text_w + bubble_pad * 2,
                               max(self.font_body.size(l)[0] for l in lines)
                               + bubble_pad * 2)
                bx = area_x + 8
                bg_color = C_NPC_BG
                name = msg['speaker']
                sp = self.font_small.render(name, True, C_GOLD)
                if area_y <= msg_y + total_height <= area_y + area_h:
                    self.screen.blit(sp, (bx, msg_y + total_height))

            total_height += speaker_h

            # 吹き出し
            bubble_rect = pygame.Rect(bx, msg_y + total_height,
                                      bubble_w, bubble_h)
            pygame.draw.rect(self.screen, bg_color, bubble_rect,
                             border_radius=8)
            pygame.draw.rect(self.screen, C_WOOD, bubble_rect, 1,
                             border_radius=8)

            # テキスト
            ty = msg_y + total_height + bubble_pad
            for line in lines:
                txt = self.font_body.render(line, True, C_CHARCOAL)
                self.screen.blit(txt, (bx + bubble_pad, ty))
                ty += line_h

            total_height += bubble_h + 10

        # スクロール上限を記録
        self.max_scroll = max(0, total_height - area_h + 20)

        self.screen.set_clip(None)

        # スクロールバー
        if self.max_scroll > 0:
            bar_x = area_x + area_w + 2
            bar_h = max(20, int(area_h * area_h / (total_height + 1)))
            bar_ratio = self.scroll_offset / self.max_scroll if self.max_scroll else 0
            bar_y = area_y + int(bar_ratio * (area_h - bar_h))
            pygame.draw.rect(self.screen, C_GOLD_DIM,
                             (bar_x, bar_y, 6, bar_h), border_radius=3)

    def _draw_input_area(self):
        """テキスト入力エリア"""
        ix = RIGHT_PANEL_X + PADDING
        iy = WINDOW_HEIGHT - 100
        iw = RIGHT_PANEL_W - PADDING * 2 - 120
        ih = 40

        can_type = self.state in (self.ST_GREETING, self.ST_TALKING)

        # 入力ボックス
        input_rect = pygame.Rect(ix, iy, iw, ih)
        bg = C_INPUT_BG if can_type else C_GREY
        pygame.draw.rect(self.screen, bg, input_rect, border_radius=4)
        pygame.draw.rect(self.screen, C_WOOD_DARK, input_rect, 2,
                         border_radius=4)

        # テキスト
        if can_type and self.input_text:
            txt = self.font_body.render(self.input_text, True, C_CHARCOAL)
            # クリッピングで枠内に収める
            self.screen.set_clip(input_rect.inflate(-8, -4))
            self.screen.blit(txt, (ix + 8, iy + 10))
            self.screen.set_clip(None)
        elif can_type:
            ph = self.font_body.render("Type your message...", True, C_GREY)
            self.screen.blit(ph, (ix + 8, iy + 10))

        # カーソル点滅
        if can_type and (pygame.time.get_ticks() // 500) % 2 == 0:
            cx = ix + 8 + self.font_body.size(self.input_text)[0]
            cx = min(cx, ix + iw - 8)
            pygame.draw.line(self.screen, C_CHARCOAL,
                             (cx, iy + 8), (cx, iy + ih - 8), 2)

        # Send ボタン
        self.btn_send.enabled = can_type and len(self.input_text.strip()) > 0
        self.btn_send.rect.topleft = (ix + iw + 10, iy)
        self.btn_send.draw(self.screen, self.font_body)

    def _draw_turn_counter(self):
        """左パネル: ターンカウンター"""
        if not self.character or self.state in (self.ST_WAITING, self.ST_LOADING):
            return

        x = LEFT_PANEL_W // 2
        y = 420

        remaining = max(0, MAX_TURNS - (self.turn_count - 1))

        # ラベル
        label = self.font_small.render("Turns remaining", True, C_PARCHMENT_DARK)
        self.screen.blit(label, (x - label.get_width() // 2, y))

        # 残りターン数の色
        if remaining >= 3:
            color = C_GREEN
        elif remaining == 2:
            color = C_YELLOW
        elif remaining == 1:
            color = C_ORANGE
        else:
            color = C_RED

        num = self.font_title.render(str(remaining), True, color)
        self.screen.blit(num, (x - num.get_width() // 2, y + 22))

        # ドットインジケーター
        dot_y = y + 62
        for i in range(MAX_TURNS):
            cx = x - (MAX_TURNS * 12) // 2 + i * 24 + 12
            if i < remaining:
                pygame.draw.circle(self.screen, color, (cx, dot_y), 8)
            else:
                pygame.draw.circle(self.screen, C_GREY, (cx, dot_y), 8)
            pygame.draw.circle(self.screen, C_WOOD_DARK, (cx, dot_y), 8, 2)

    def _draw_status_bar(self):
        """画面下部: ステータスバー"""
        bar_rect = pygame.Rect(RIGHT_PANEL_X, WINDOW_HEIGHT - 45,
                               RIGHT_PANEL_W, 45)
        pygame.draw.rect(self.screen, C_WOOD_DARK, bar_rect)
        pygame.draw.line(self.screen, C_GOLD_DIM,
                         (RIGHT_PANEL_X, WINDOW_HEIGHT - 45),
                         (WINDOW_WIDTH, WINDOW_HEIGHT - 45), 1)

        if self.state == self.ST_LOADING:
            txt = "Loading Phi-2 model... please wait"
        elif self.state == self.ST_WAITING:
            txt = 'Click "New Character" to meet an adventurer'
        elif self.state == self.ST_GENERATING:
            txt = "Thinking..."
        elif self.state == self.ST_JUDGING:
            txt = "Evaluating recruitment..."
        elif self.state == self.ST_VERDICT:
            txt = "Verdict shown. Meet another character?"
        else:
            remaining = max(0, MAX_TURNS - (self.turn_count - 1))
            txt = f"Talk to recruit this character. {remaining} turn(s) left."

        surf = self.font_small.render(txt, True, C_PARCHMENT_DARK)
        self.screen.blit(surf, (RIGHT_PANEL_X + PADDING, WINDOW_HEIGHT - 32))

    def _draw_verdict_overlay(self):
        """判定結果オーバーレイアニメーション"""
        if self.state != self.ST_VERDICT:
            return

        self.verdict_frame += 1
        alpha = min(200, self.verdict_frame * 6)

        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)

        if self.verdict_result:
            overlay.fill((76, 175, 80, alpha))
            main_text = "Recruited!"
            main_color = C_WHITE
        else:
            overlay.fill((211, 47, 47, alpha))
            main_text = "Declined..."
            main_color = C_WHITE

        self.screen.blit(overlay, (0, 0))

        # テキスト（フェードイン後）
        if self.verdict_frame > 15:
            # メインテキスト
            big_font = pygame.font.Font(
                pygame.font.match_font("notosans") or
                pygame.font.match_font("dejavusans"),
                64) if pygame.font.match_font("notosans") or \
                       pygame.font.match_font("dejavusans") \
                else pygame.font.Font(None, 72)

            txt = big_font.render(main_text, True, main_color)
            tx = WINDOW_WIDTH // 2 - txt.get_width() // 2
            ty = WINDOW_HEIGHT // 2 - 60
            self.screen.blit(txt, (tx, ty))

            # 確率
            prob_str = f"YES: {self.verdict_prob:.1%}   |   {self.verdict_details.get('decision_type', '')}"
            prob = self.font_header.render(prob_str, True, C_WHITE)
            self.screen.blit(prob,
                             (WINDOW_WIDTH // 2 - prob.get_width() // 2,
                              ty + 80))

            # キャラクター名
            if self.character:
                name_str = f"{self.character['name']} the {self.character['job']}"
                ns = self.font_body.render(name_str, True, C_PARCHMENT)
                self.screen.blit(ns,
                                 (WINDOW_WIDTH // 2 - ns.get_width() // 2,
                                  ty + 120))

    def _draw_loading_screen(self):
        """ローディング画面"""
        self.screen.fill(C_WOOD_DARK)
        txt = self.font_title.render("Loading Phi-2 Model...", True, C_GOLD)
        self.screen.blit(txt, (WINDOW_WIDTH // 2 - txt.get_width() // 2,
                               WINDOW_HEIGHT // 2 - 40))

        # アニメーションドット
        dots = "." * ((pygame.time.get_ticks() // 500) % 4)
        d = self.font_header.render(dots, True, C_PARCHMENT)
        self.screen.blit(d, (WINDOW_WIDTH // 2 - d.get_width() // 2,
                             WINDOW_HEIGHT // 2 + 20))

        sub = self.font_small.render(
            "This may take a minute on first run.", True, C_PARCHMENT_DARK)
        self.screen.blit(sub, (WINDOW_WIDTH // 2 - sub.get_width() // 2,
                               WINDOW_HEIGHT // 2 + 60))

    # ---------- ゲームロジック ----------

    def _new_character(self):
        """新キャラクター生成＋初回挨拶"""
        if not self.simulator:
            return

        self.simulator.reset()
        self.character = self.simulator.create_random_character()
        self.turn_count = 0
        self.messages = []
        self.scroll_offset = 0
        self.verdict_result = None
        self.verdict_frame = 0
        self.input_text = ""

        # 初回挨拶をバックグラウンドで生成
        self.state = self.ST_GENERATING
        self._ai_busy = True

        def gen():
            first_msg = ("Hello! I'm looking for companions. "
                         "Can you tell me about yourself and your abilities?")
            resp = self.simulator.generate_response(
                first_msg, self.character, is_first_greeting=True)
            self.simulator.conversation_history.append({
                'turn': 1, 'user': first_msg, 'ai': resp
            })
            self.messages.append({
                'speaker': 'You', 'text': first_msg, 'is_user': True})
            self.messages.append({
                'speaker': self.character['name'],
                'text': resp, 'is_user': False})
            self.turn_count = 1
            self.state = self.ST_GREETING
            self._ai_busy = False

        threading.Thread(target=gen, daemon=True).start()

    def _send_message(self):
        """ユーザーメッセージ送信 → AI応答生成"""
        text = self.input_text.strip()
        if not text or not self.character or self._ai_busy:
            return

        remaining = MAX_TURNS - (self.turn_count - 1)
        if remaining <= 0:
            return

        self.messages.append({
            'speaker': 'You', 'text': text, 'is_user': True})
        self.input_text = ""
        self.turn_count += 1
        self.state = self.ST_GENERATING
        self._ai_busy = True

        # 自動スクロール
        self.scroll_offset = max(0, self.max_scroll + 100)

        def gen():
            resp = self.simulator.generate_response(text, self.character)
            self.simulator.conversation_history.append({
                'turn': self.turn_count,
                'user': text,
                'ai': resp
            })
            self.messages.append({
                'speaker': self.character['name'],
                'text': resp, 'is_user': False})
            self._ai_busy = False

            # 自動スクロール
            self.scroll_offset = max(0, self.max_scroll + 200)

            # ターン上限チェック
            new_remaining = MAX_TURNS - (self.turn_count - 1)
            if new_remaining <= 0:
                self._finalize_recruitment()
            else:
                self.state = self.ST_TALKING

        threading.Thread(target=gen, daemon=True).start()

    def _finalize_recruitment(self):
        """最終判定"""
        self.state = self.ST_JUDGING

        def judge():
            result, prob, details = self.simulator._classify_companion(
                self.character)
            self.verdict_result = result
            self.verdict_prob = prob
            self.verdict_details = details
            self.verdict_frame = 0
            self.state = self.ST_VERDICT

        threading.Thread(target=judge, daemon=True).start()

    # ---------- ユーティリティ ----------

    @staticmethod
    def _wrap_text(text: str, font: pygame.font.Font,
                   max_width: int) -> List[str]:
        """テキストを指定幅で自動改行"""
        words = text.split(' ')
        lines = []
        current = ""
        for word in words:
            test = (current + " " + word).strip()
            if font.size(test)[0] <= max_width:
                current = test
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines or [""]

    # ---------- メインループ ----------

    def run(self):
        """メインゲームループ"""
        running = True

        while running:
            # --- イベント処理 ---
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # 左クリック
                        pos = event.pos
                        if self.btn_new.clicked(pos):
                            if self.state in (self.ST_WAITING, self.ST_GREETING,
                                              self.ST_TALKING, self.ST_VERDICT):
                                self._new_character()

                        elif self.btn_send.clicked(pos):
                            self._send_message()

                elif event.type == pygame.MOUSEWHEEL:
                    # ダイアログエリアのスクロール
                    self.scroll_offset = max(
                        0, min(self.max_scroll,
                               self.scroll_offset - event.y * 30))

                elif event.type == pygame.KEYDOWN:
                    if self.state in (self.ST_GREETING, self.ST_TALKING):
                        if event.key == pygame.K_RETURN:
                            self._send_message()
                        elif event.key == pygame.K_BACKSPACE:
                            self.input_text = self.input_text[:-1]
                        else:
                            if event.unicode and len(self.input_text) < 200:
                                self.input_text += event.unicode

            # --- 描画 ---
            if self.state == self.ST_LOADING:
                self._draw_loading_screen()
            else:
                self._draw_background()
                self._draw_portrait()
                self._draw_character_info()
                self._draw_dialogue()
                self._draw_input_area()
                self._draw_turn_counter()
                self._draw_status_bar()

                # ボタン
                self.btn_new.enabled = self.state in (
                    self.ST_WAITING, self.ST_GREETING,
                    self.ST_TALKING, self.ST_VERDICT)
                self.btn_new.draw(self.screen, self.font_body)

                # 判定オーバーレイ
                self._draw_verdict_overlay()

            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()


# ============================================
# エントリーポイント
# ============================================

if __name__ == "__main__":
    gui = TavernGUI()
    gui.run()
