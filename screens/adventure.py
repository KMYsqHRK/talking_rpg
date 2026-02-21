import pygame
from typing import Dict, List, Optional

from settings.settings import WINDOW, LAYOUT, C, UIButton
from screens.base import BaseScreen


class AdventureScreen(BaseScreen):
    """冒険画面"""

    ACTIONS = [
        {"name": "Assemble your team",     "desc": "Choose party members for the journey ahead."},
        {"name": "Prepare your belongings", "desc": "Equip weapons, armor, and accessories."},
        {"name": "Start Adventure",         "desc": "Venture into the dungeon and face the unknown."},
    ]

    def __init__(self, screen: pygame.Surface, fonts: Dict, assets: Dict):
        super().__init__(screen, fonts, assets)
        self.selected = 0

        self.btn_back = UIButton(
            pygame.Rect(LAYOUT.padding, LAYOUT.padding, 120, 36),
            "< Village", C.gold, C.gold_dim, C.charcoal
        )

    def _get_item_rects(self) -> List[pygame.Rect]:
        x = 100
        start_y = 280
        item_h = 50
        rects = []
        for i in range(len(self.ACTIONS)):
            rects.append(pygame.Rect(x, start_y + i * item_h, 400, item_h))
        return rects

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
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

    def _execute_action(self, index: int):
        # TODO: 各アクションの処理を実装
        pass

    def draw(self):
        # 背景画像
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

            # 三角カーソル
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

        # 戻るボタン
        self.btn_back.draw(self.screen, self.fonts["body"])

        # 操作ヒント
        hint = self.fonts["small"].render(
            "Up/Down to select  |  Enter or Click to confirm  |  Esc to go back",
            True, C.parchment_dark)
        self.screen.blit(hint, (100, WINDOW.height - 60))
