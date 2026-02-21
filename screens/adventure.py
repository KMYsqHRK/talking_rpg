import pygame
import os
from typing import Dict, List, Optional

from settings.settings import WINDOW, LAYOUT, C, UIButton
from screens.base import BaseScreen


class AdventureScreen(BaseScreen):
    """冒険画面 - 準備 & ダンジョン探索"""

    # 画面状態
    ST_PREPARE = "prepare"        # 冒険準備メニュー
    ST_DUNGEON = "dungeon"        # ダンジョン探索中
    ST_BOSS = "boss"              # ボス戦（到達表示）

    STEPS_PER_FLOOR = 25          # ボス戦までの歩数

    ACTIONS = [
        {"name": "Assemble your team",     "desc": "Choose party members for the journey ahead."},
        {"name": "Prepare your belongings", "desc": "Equip weapons, armor, and accessories."},
        {"name": "Start Adventure",         "desc": "Venture into the dungeon and face the unknown."},
    ]

    def __init__(self, screen: pygame.Surface, fonts: Dict, assets: Dict):
        super().__init__(screen, fonts, assets)
        self.state = self.ST_PREPARE
        self.selected = 0

        # ダンジョン進行状態
        self.current_step = 0
        self.current_floor = 1
        self.max_floors = 5  # dungeon-1 ~ dungeon-5

        # ダンジョン背景画像キャッシュ
        self._dungeon_imgs: Dict[int, Optional[pygame.Surface]] = {}
        self._load_dungeon_images()

        # ボタン
        self.btn_back = UIButton(
            pygame.Rect(LAYOUT.padding, LAYOUT.padding, 120, 36),
            "< Village", C.gold, C.gold_dim, C.charcoal
        )

    def _load_dungeon_images(self):
        """dungeon-N.png を動的に読み込む"""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        img_dir = os.path.join(base_dir, "img")
        floor = 1
        while True:
            path = os.path.join(img_dir, f"dungeon-{floor}.png")
            if not os.path.exists(path):
                break
            raw = pygame.image.load(path).convert()
            self._dungeon_imgs[floor] = pygame.transform.smoothscale(
                raw, (WINDOW.width, WINDOW.height))
            floor += 1
        self.max_floors = max(1, floor - 1)

    def _get_dungeon_bg(self) -> Optional[pygame.Surface]:
        """現在の階層に対応する背景を返す"""
        return self._dungeon_imgs.get(self.current_floor)

    # ---------- メニューrects ----------

    def _get_item_rects(self) -> List[pygame.Rect]:
        x = 100
        start_y = 280
        item_h = 50
        rects = []
        for i in range(len(self.ACTIONS)):
            rects.append(pygame.Rect(x, start_y + i * item_h, 400, item_h))
        return rects

    # ---------- イベント処理 ----------

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        if self.state == self.ST_PREPARE:
            return self._handle_prepare(event)
        elif self.state == self.ST_DUNGEON:
            return self._handle_dungeon(event)
        elif self.state == self.ST_BOSS:
            return self._handle_boss(event)
        return None

    def _handle_prepare(self, event: pygame.event.Event) -> Optional[str]:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.btn_back.clicked(event.pos):
                return "village"
            item_rects = self._get_item_rects()
            for i, rect in enumerate(item_rects):
                if rect.collidepoint(event.pos):
                    self.selected = i
                    self._execute_action(i)

        elif event.type == pygame.MOUSEMOTION:
            item_rects = self._get_item_rects()
            for i, rect in enumerate(item_rects):
                if rect.collidepoint(event.pos):
                    self.selected = i

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return "village"
            n = len(self.ACTIONS)
            if event.key == pygame.K_UP:
                self.selected = (self.selected - 1) % n
            elif event.key == pygame.K_DOWN:
                self.selected = (self.selected + 1) % n
            elif event.key == pygame.K_RETURN:
                self._execute_action(self.selected)
        return None

    def _handle_dungeon(self, event: pygame.event.Event) -> Optional[str]:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.state = self.ST_PREPARE
            elif event.key in (pygame.K_RIGHT, pygame.K_RETURN, pygame.K_SPACE):
                self._step_forward()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.btn_back.clicked(event.pos):
                self.state = self.ST_PREPARE
            else:
                self._step_forward()
        return None

    def _handle_boss(self, event: pygame.event.Event) -> Optional[str]:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.state = self.ST_PREPARE
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._advance_floor()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.btn_back.clicked(event.pos):
                self.state = self.ST_PREPARE
            else:
                self._advance_floor()
        return None

    # ---------- ゲームロジック ----------

    def _execute_action(self, index: int):
        if index == 2:  # Start Adventure
            self.current_step = 0
            self.current_floor = 1
            self.state = self.ST_DUNGEON

    def _step_forward(self):
        self.current_step += 1
        if self.current_step >= self.STEPS_PER_FLOOR:
            self.state = self.ST_BOSS

    def _advance_floor(self):
        """ボス戦後、次の階層へ"""
        if self.current_floor >= self.max_floors:
            # 最終階クリア → 準備画面に戻る
            self.state = self.ST_PREPARE
        else:
            self.current_floor += 1
            self.current_step = 0
            self.state = self.ST_DUNGEON

    # ---------- 描画 ----------

    def draw(self):
        if self.state == self.ST_PREPARE:
            self._draw_prepare()
        elif self.state == self.ST_DUNGEON:
            self._draw_dungeon()
        elif self.state == self.ST_BOSS:
            self._draw_boss()

    def _draw_prepare(self):
        """冒険準備画面（Village風メニュー）"""
        bg_img = self.assets.get("adventure_img")
        if bg_img:
            self.screen.blit(bg_img, (0, 0))
            overlay = pygame.Surface((WINDOW.width, WINDOW.height),
                                     pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 80))
            self.screen.blit(overlay, (0, 0))
        else:
            self.screen.fill(C.black)

        # タイトル
        title = self.fonts["title"].render("Adventure", True, C.white)
        self.screen.blit(title, (100, 180))

        sub = self.fonts["small"].render("What would you like to do?",
                                         True, C.parchment_dark)
        self.screen.blit(sub, (100, 220))

        # メニューリスト
        item_rects = self._get_item_rects()
        for i, (action, rect) in enumerate(zip(self.ACTIONS, item_rects)):
            selected = (i == self.selected)
            color = C.gold if selected else C.parchment_dark

            if selected:
                tri_x = rect.x - 10
                tri_y = rect.y + rect.h // 2
                pygame.draw.polygon(self.screen, C.gold, [
                    (tri_x - 14, tri_y - 8),
                    (tri_x - 14, tri_y + 8),
                    (tri_x, tri_y),
                ])

            name_surf = self.fonts["village"].render(action["name"], True, color)
            self.screen.blit(name_surf, (rect.x, rect.y + 8))

        # 説明文
        action = self.ACTIONS[self.selected]
        desc_x = 500
        desc_y = 400
        for line in self.wrap_text(action["desc"], self.fonts["body"], 500):
            desc_surf = self.fonts["body"].render(line, True, C.parchment)
            self.screen.blit(desc_surf, (desc_x, desc_y))
            desc_y += 24

        self.btn_back.draw(self.screen, self.fonts["body"])

        hint = self.fonts["small"].render(
            "Up/Down to select  |  Enter or Click to confirm  |  Esc to go back",
            True, C.parchment_dark)
        self.screen.blit(hint, (100, WINDOW.height - 60))

    def _draw_dungeon(self):
        """ダンジョン探索画面"""
        # 背景（現在の階層）
        bg = self._get_dungeon_bg()
        if bg:
            self.screen.blit(bg, (0, 0))
            overlay = pygame.Surface((WINDOW.width, WINDOW.height),
                                     pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 60))
            self.screen.blit(overlay, (0, 0))
        else:
            self.screen.fill(C.black)

        # 階層情報
        floor_str = f"Floor {self.current_floor}"
        floor_surf = self.fonts["title"].render(floor_str, True, C.white)
        self.screen.blit(floor_surf, (100, 40))

        # 戻るボタン
        self.btn_back.text = "< Back"
        self.btn_back.draw(self.screen, self.fonts["body"])

        # 操作ヒント
        hint = self.fonts["small"].render(
            "Right / Enter / Space / Click to move forward  |  Esc to retreat",
            True, C.parchment_dark)
        self.screen.blit(hint, (100, WINDOW.height - 40))

    def _draw_boss(self):
        """ボス戦到達画面"""
        # 背景（現在の階層）
        bg = self._get_dungeon_bg()
        if bg:
            self.screen.blit(bg, (0, 0))

        # 暗いオーバーレイ
        overlay = pygame.Surface((WINDOW.width, WINDOW.height), pygame.SRCALPHA)
        overlay.fill((80, 0, 0, 140))
        self.screen.blit(overlay, (0, 0))

        # ボス到達テキスト
        boss_title = self.fonts["title"].render(
            f"Floor {self.current_floor} - BOSS", True, C.red)
        self.screen.blit(boss_title,
                         (WINDOW.width // 2 - boss_title.get_width() // 2,
                          WINDOW.height // 2 - 80))

        # TODO表記
        todo_surf = self.fonts["header"].render(
            "Boss battle coming soon...", True, C.gold)
        self.screen.blit(todo_surf,
                         (WINDOW.width // 2 - todo_surf.get_width() // 2,
                          WINDOW.height // 2 - 20))

        # 次の階層 or クリア
        if self.current_floor >= self.max_floors:
            next_str = "Press Enter to return to camp (Final floor!)"
        else:
            next_str = f"Press Enter to advance to Floor {self.current_floor + 1}"
        next_surf = self.fonts["body"].render(next_str, True, C.parchment)
        self.screen.blit(next_surf,
                         (WINDOW.width // 2 - next_surf.get_width() // 2,
                          WINDOW.height // 2 + 40))

        # 戻るボタン
        self.btn_back.text = "< Retreat"
        self.btn_back.draw(self.screen, self.fonts["body"])
