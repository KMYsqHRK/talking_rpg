import pygame
import threading
from typing import Dict, List, Optional

from Phi2DialogueSimulatour import Phi2DialogueSimulator
from settings.settings import DIALOGUE, WINDOW, LAYOUT, PORTRAIT, C, UIButton
from screens.base import BaseScreen


class TavernScreen(BaseScreen):
    """タバーン勧誘画面（AI対話含む）"""

    # 内部状態
    ST_LOADING = "loading"
    ST_WAITING = "waiting"
    ST_GREETING = "greeting"
    ST_TALKING = "talking"
    ST_GENERATING = "generating"
    ST_JUDGING = "judging"
    ST_VERDICT = "verdict"

    _INTERACTIVE_STATES = {ST_WAITING, ST_GREETING, ST_TALKING, ST_VERDICT}

    def __init__(self, screen: pygame.Surface, fonts: Dict, assets: Dict):
        super().__init__(screen, fonts, assets)

        self.state = self.ST_LOADING

        # 対話状態
        self.character: Optional[Dict] = None
        self.turn_count = 0
        self.messages: List[Dict] = []
        self.input_text = ""
        self.scroll_offset = 0
        self.max_scroll = 0

        # 判定結果
        self.verdict_result: Optional[bool] = None
        self.verdict_prob = 0.0
        self.verdict_details: Dict = {}
        self.verdict_frame = 0

        # AI応答スレッド
        self._ai_busy = False

        # ボタン
        self.btn_new = UIButton(
            pygame.Rect(LAYOUT.left_panel_w // 2 - 90, 700, 180, 50),
            "New Character", C.gold, C.gold_dim, C.charcoal
        )
        self.btn_send = UIButton(
            pygame.Rect(WINDOW.width - LAYOUT.padding - 100,
                        WINDOW.height - 100, 100, 40),
            "Send", C.gold, C.gold_dim, C.charcoal
        )
        self.btn_back = UIButton(
            pygame.Rect(LAYOUT.padding, LAYOUT.padding, 120, 36),
            "< Village", C.gold, C.gold_dim, C.charcoal
        )

        # Simulator
        self.simulator: Optional[Phi2DialogueSimulator] = None

    def enter(self):
        """画面に入ったときの処理"""
        if self.simulator:
            self.state = self.ST_WAITING
        else:
            self.state = self.ST_LOADING
            threading.Thread(target=self._load_simulator,
                             daemon=True).start()

    def _load_simulator(self):
        self.simulator = Phi2DialogueSimulator(use_gpu=True)
        self.state = self.ST_WAITING

    # ---------- イベント処理 ----------

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            if self.btn_back.clicked(pos):
                if self.state in self._INTERACTIVE_STATES:
                    return "village"
            elif self.btn_new.clicked(pos):
                if self.state in self._INTERACTIVE_STATES:
                    self._new_character()
            elif self.btn_send.clicked(pos):
                self._send_message()

        elif event.type == pygame.MOUSEWHEEL:
            self.scroll_offset = max(
                0, min(self.max_scroll,
                       self.scroll_offset - event.y * 30))

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.state in self._INTERACTIVE_STATES:
                    return "village"
            elif self.state in (self.ST_GREETING, self.ST_TALKING):
                if event.key == pygame.K_RETURN:
                    self._send_message()
                elif event.key == pygame.K_BACKSPACE:
                    self.input_text = self.input_text[:-1]
                else:
                    if event.unicode and len(self.input_text) < 200:
                        self.input_text += event.unicode

        return None

    # ---------- 描画 ----------

    def draw(self):
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

            self.btn_new.enabled = self.state in self._INTERACTIVE_STATES
            self.btn_new.draw(self.screen, self.fonts["body"])

            if self.state in self._INTERACTIVE_STATES:
                self.btn_back.draw(self.screen, self.fonts["body"])

            self._draw_verdict_overlay()

    # ---------- タバーン描画メソッド ----------

    def _draw_background(self):
        bg_img = self.assets.get("tavern_img")
        if bg_img:
            self.screen.blit(bg_img, (0, 0))
        else:
            self.screen.fill(C.wood)

        left_bg = pygame.Surface((LAYOUT.left_panel_w, WINDOW.height), pygame.SRCALPHA)
        left_bg.fill((*C.wood_dark, 180))
        self.screen.blit(left_bg, (0, 0))

        right_bg = pygame.Surface((LAYOUT.right_panel_w, WINDOW.height), pygame.SRCALPHA)
        right_bg.fill((*C.wood_dark, 120))
        self.screen.blit(right_bg, (LAYOUT.left_panel_w, 0))

        pygame.draw.line(self.screen, C.gold_dim,
                         (LAYOUT.left_panel_w, 0), (LAYOUT.left_panel_w, WINDOW.height), 2)

        title_rect = pygame.Rect(0, 0, WINDOW.width, 70)
        pygame.draw.rect(self.screen, C.wood_dark, title_rect)
        pygame.draw.line(self.screen, C.gold,
                         (0, 70), (WINDOW.width, 70), 2)
        title = self.fonts["title"].render("Tavern Recruitment", True, C.gold)
        self.screen.blit(title, (WINDOW.width // 2 - title.get_width() // 2, 8))

    def _draw_portrait(self):
        x = LAYOUT.left_panel_w // 2 - PORTRAIT.width // 2
        y = 100
        portrait_img = self.assets.get("portrait_img")

        if self.character:
            frame = pygame.Rect(x - 6, y - 6,
                                PORTRAIT.width + 12, PORTRAIT.height + 12)
            pygame.draw.rect(self.screen, C.gold, frame, 3, border_radius=4)
            if portrait_img:
                self.screen.blit(portrait_img, (x, y))
        else:
            frame = pygame.Rect(x - 6, y - 6,
                                PORTRAIT.width + 12, PORTRAIT.height + 12)
            pygame.draw.rect(self.screen, C.grey, frame, 2, border_radius=4)
            placeholder = pygame.Surface((PORTRAIT.width, PORTRAIT.height))
            placeholder.fill(C.wood_dark)
            q = self.fonts["title"].render("?", True, C.grey)
            placeholder.blit(q, (PORTRAIT.width // 2 - q.get_width() // 2,
                                 PORTRAIT.height // 2 - q.get_height() // 2))
            self.screen.blit(placeholder, (x, y))

    def _draw_character_info(self):
        if not self.character:
            hint = self.fonts["body"].render(
                'Click "New Character" to begin.', True, C.parchment)
            self.screen.blit(hint, (LAYOUT.right_panel_x + LAYOUT.padding, 80))
            return

        ch = self.character
        x = LAYOUT.right_panel_x + LAYOUT.padding
        y = 65

        name_surf = self.fonts["header"].render(ch['name'], True, C.gold)
        self.screen.blit(name_surf, (x, y))
        y += 30

        job_str = f"{ch['job']}  ({ch['role']})"
        job_surf = self.fonts["body"].render(job_str, True, C.parchment)
        self.screen.blit(job_surf, (x, y))
        y += 24

        pers_str = f"Personality: {ch['personality']} - {ch['personality_desc']}"
        for line in self.wrap_text(pers_str, self.fonts["small"],
                                   LAYOUT.right_panel_w - LAYOUT.padding * 2):
            surf = self.fonts["small"].render(line, True, C.parchment_dark)
            self.screen.blit(surf, (x, y))
            y += 18

        y += 4
        wep = self.fonts["small"].render(
            f"Weapon: {ch['weapon']}   |   Abilities: {ch['abilities']}",
            True, C.parchment_dark)
        self.screen.blit(wep, (x, y))
        y += 22

        self._draw_stats_badges(x, y, ch)

    def _draw_stats_badges(self, x: int, y: int, ch: Dict):
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

            pygame.draw.rect(self.screen, C.wood_dark, rect, border_radius=4)
            pygame.draw.rect(self.screen, C.gold_dim, rect, 1, border_radius=4)

            if val > 0:
                val_color = C.green
                val_str = f"+{val}"
            elif val < 0:
                val_color = C.red
                val_str = str(val)
            else:
                val_color = C.white
                val_str = "0"

            txt = self.fonts["stat"].render(f"{label} {val_str}", True, val_color)
            txt_rect = txt.get_rect(center=rect.center)
            self.screen.blit(txt, txt_rect)

    def _draw_dialogue(self):
        area_x = LAYOUT.right_panel_x + LAYOUT.padding
        area_y = 220
        area_w = LAYOUT.right_panel_w - LAYOUT.padding * 2
        area_h = WINDOW.height - 220 - 120

        bg_rect = pygame.Rect(area_x - 5, area_y - 5, area_w + 10, area_h + 10)
        panel_bg = pygame.Surface((bg_rect.w, bg_rect.h), pygame.SRCALPHA)
        panel_bg.fill((*C.wood_dark, 160))
        self.screen.blit(panel_bg, bg_rect.topleft)
        pygame.draw.rect(self.screen, C.gold_dim, bg_rect, 1, border_radius=6)

        clip_rect = pygame.Rect(area_x, area_y, area_w, area_h)
        self.screen.set_clip(clip_rect)

        msg_y = area_y + 8 - self.scroll_offset
        bubble_pad = 10
        max_text_w = area_w - 80

        total_height = 0
        for msg in self.messages:
            lines = self.wrap_text(msg['text'], self.fonts["body"], max_text_w)
            line_h = self.fonts["body"].get_linesize()
            bubble_h = len(lines) * line_h + bubble_pad * 2 + 4
            speaker_h = 18

            if msg['is_user']:
                bubble_w = min(max_text_w + bubble_pad * 2,
                               max(self.fonts["body"].size(l)[0] for l in lines)
                               + bubble_pad * 2)
                bx = area_x + area_w - bubble_w - 8
                bg_color = C.user_bg
                sp = self.fonts["small"].render("You", True, C.parchment_dark)
                if area_y <= msg_y + total_height <= area_y + area_h:
                    self.screen.blit(sp, (bx + bubble_w - sp.get_width(),
                                         msg_y + total_height))
            else:
                bubble_w = min(max_text_w + bubble_pad * 2,
                               max(self.fonts["body"].size(l)[0] for l in lines)
                               + bubble_pad * 2)
                bx = area_x + 8
                bg_color = C.npc_bg
                name = msg['speaker']
                sp = self.fonts["small"].render(name, True, C.gold)
                if area_y <= msg_y + total_height <= area_y + area_h:
                    self.screen.blit(sp, (bx, msg_y + total_height))

            total_height += speaker_h

            bubble_rect = pygame.Rect(bx, msg_y + total_height,
                                      bubble_w, bubble_h)
            pygame.draw.rect(self.screen, bg_color, bubble_rect,
                             border_radius=8)
            pygame.draw.rect(self.screen, C.wood, bubble_rect, 1,
                             border_radius=8)

            ty = msg_y + total_height + bubble_pad
            for line in lines:
                txt = self.fonts["body"].render(line, True, C.charcoal)
                self.screen.blit(txt, (bx + bubble_pad, ty))
                ty += line_h

            total_height += bubble_h + 10

        self.max_scroll = max(0, total_height - area_h + 20)
        self.screen.set_clip(None)

        if self.max_scroll > 0:
            bar_x = area_x + area_w + 2
            bar_h = max(20, int(area_h * area_h / (total_height + 1)))
            bar_ratio = self.scroll_offset / self.max_scroll if self.max_scroll else 0
            bar_y = area_y + int(bar_ratio * (area_h - bar_h))
            pygame.draw.rect(self.screen, C.gold_dim,
                             (bar_x, bar_y, 6, bar_h), border_radius=3)

    def _draw_input_area(self):
        ix = LAYOUT.right_panel_x + LAYOUT.padding
        iy = WINDOW.height - 100
        iw = LAYOUT.right_panel_w - LAYOUT.padding * 2 - 120
        ih = 40

        can_type = self.state in (self.ST_GREETING, self.ST_TALKING)

        input_rect = pygame.Rect(ix, iy, iw, ih)
        bg = C.input_bg if can_type else C.grey
        pygame.draw.rect(self.screen, bg, input_rect, border_radius=4)
        pygame.draw.rect(self.screen, C.wood_dark, input_rect, 2,
                         border_radius=4)

        if can_type and self.input_text:
            txt = self.fonts["body"].render(self.input_text, True, C.charcoal)
            self.screen.set_clip(input_rect.inflate(-8, -4))
            self.screen.blit(txt, (ix + 8, iy + 10))
            self.screen.set_clip(None)
        elif can_type:
            ph = self.fonts["body"].render("Type your message...", True, C.grey)
            self.screen.blit(ph, (ix + 8, iy + 10))

        if can_type and (pygame.time.get_ticks() // 500) % 2 == 0:
            cx = ix + 8 + self.fonts["body"].size(self.input_text)[0]
            cx = min(cx, ix + iw - 8)
            pygame.draw.line(self.screen, C.charcoal,
                             (cx, iy + 8), (cx, iy + ih - 8), 2)

        self.btn_send.enabled = can_type and len(self.input_text.strip()) > 0
        self.btn_send.rect.topleft = (ix + iw + 10, iy)
        self.btn_send.draw(self.screen, self.fonts["body"])

    def _draw_turn_counter(self):
        if not self.character or self.state in (self.ST_WAITING, self.ST_LOADING):
            return

        x = LAYOUT.left_panel_w // 2
        y = 420

        remaining = max(0, DIALOGUE.max_turns - (self.turn_count - 1))

        label = self.fonts["small"].render("Turns remaining", True, C.parchment_dark)
        self.screen.blit(label, (x - label.get_width() // 2, y))

        if remaining >= 3:
            color = C.green
        elif remaining == 2:
            color = C.yellow
        elif remaining == 1:
            color = C.orange
        else:
            color = C.red

        num = self.fonts["title"].render(str(remaining), True, color)
        self.screen.blit(num, (x - num.get_width() // 2, y + 22))

        dot_y = y + 62
        for i in range(DIALOGUE.max_turns):
            cx = x - (DIALOGUE.max_turns * 12) // 2 + i * 24 + 12
            if i < remaining:
                pygame.draw.circle(self.screen, color, (cx, dot_y), 8)
            else:
                pygame.draw.circle(self.screen, C.grey, (cx, dot_y), 8)
            pygame.draw.circle(self.screen, C.wood_dark, (cx, dot_y), 8, 2)

    def _draw_status_bar(self):
        bar_rect = pygame.Rect(LAYOUT.right_panel_x, WINDOW.height - 45,
                               LAYOUT.right_panel_w, 45)
        pygame.draw.rect(self.screen, C.wood_dark, bar_rect)
        pygame.draw.line(self.screen, C.gold_dim,
                         (LAYOUT.right_panel_x, WINDOW.height - 45),
                         (WINDOW.width, WINDOW.height - 45), 1)

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
            remaining = max(0, DIALOGUE.max_turns - (self.turn_count - 1))
            txt = f"Talk to recruit this character. {remaining} turn(s) left."

        surf = self.fonts["small"].render(txt, True, C.parchment_dark)
        self.screen.blit(surf, (LAYOUT.right_panel_x + LAYOUT.padding, WINDOW.height - 32))

    def _draw_verdict_overlay(self):
        if self.state != self.ST_VERDICT:
            return

        self.verdict_frame += 1
        alpha = min(200, self.verdict_frame * 6)

        overlay = pygame.Surface((WINDOW.width, WINDOW.height), pygame.SRCALPHA)

        if self.verdict_result:
            overlay.fill((76, 175, 80, alpha))
            main_text = "Recruited!"
        else:
            overlay.fill((211, 47, 47, alpha))
            main_text = "Declined..."

        self.screen.blit(overlay, (0, 0))

        if self.verdict_frame > 15:
            big_font = pygame.font.Font(
                pygame.font.match_font("notosans") or
                pygame.font.match_font("dejavusans"),
                64) if pygame.font.match_font("notosans") or \
                       pygame.font.match_font("dejavusans") \
                else pygame.font.Font(None, 72)

            txt = big_font.render(main_text, True, C.white)
            tx = WINDOW.width // 2 - txt.get_width() // 2
            ty = WINDOW.height // 2 - 60
            self.screen.blit(txt, (tx, ty))

            prob_str = f"YES: {self.verdict_prob:.1%}   |   {self.verdict_details.get('decision_type', '')}"
            prob = self.fonts["header"].render(prob_str, True, C.white)
            self.screen.blit(prob,
                             (WINDOW.width // 2 - prob.get_width() // 2,
                              ty + 80))

            if self.character:
                name_str = f"{self.character['name']} the {self.character['job']}"
                ns = self.fonts["body"].render(name_str, True, C.parchment)
                self.screen.blit(ns,
                                 (WINDOW.width // 2 - ns.get_width() // 2,
                                  ty + 120))

    def _draw_loading_screen(self):
        bg_img = self.assets.get("tavern_img")
        if bg_img:
            self.screen.blit(bg_img, (0, 0))
            overlay = pygame.Surface((WINDOW.width, WINDOW.height), pygame.SRCALPHA)
            overlay.fill((*C.wood_dark, 180))
            self.screen.blit(overlay, (0, 0))
        else:
            self.screen.fill(C.wood_dark)

        txt = self.fonts["title"].render("Loading Phi-2 Model...", True, C.gold)
        self.screen.blit(txt, (WINDOW.width // 2 - txt.get_width() // 2,
                               WINDOW.height // 2 - 40))

        dots = "." * ((pygame.time.get_ticks() // 500) % 4)
        d = self.fonts["header"].render(dots, True, C.parchment)
        self.screen.blit(d, (WINDOW.width // 2 - d.get_width() // 2,
                             WINDOW.height // 2 + 20))

        sub = self.fonts["small"].render(
            "This may take a minute on first run.", True, C.parchment_dark)
        self.screen.blit(sub, (WINDOW.width // 2 - sub.get_width() // 2,
                               WINDOW.height // 2 + 60))

    # ---------- ゲームロジック ----------

    def _new_character(self):
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
        text = self.input_text.strip()
        if not text or not self.character or self._ai_busy:
            return

        remaining = DIALOGUE.max_turns - (self.turn_count - 1)
        if remaining <= 0:
            return

        self.messages.append({
            'speaker': 'You', 'text': text, 'is_user': True})
        self.input_text = ""
        self.turn_count += 1
        self.state = self.ST_GENERATING
        self._ai_busy = True

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

            self.scroll_offset = max(0, self.max_scroll + 200)

            new_remaining = DIALOGUE.max_turns - (self.turn_count - 1)
            if new_remaining <= 0:
                self._finalize_recruitment()
            else:
                self.state = self.ST_TALKING

        threading.Thread(target=gen, daemon=True).start()

    def _finalize_recruitment(self):
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
