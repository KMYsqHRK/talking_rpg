import pygame
from typing import Dict, List, Optional

from settings.settings import WINDOW, C
from screens.base import BaseScreen


class VillageScreen(BaseScreen):
    """村の選択画面"""

    LOCATIONS = [
        {"name": "Guild",     "key": "guild",     "desc": "Coming soon..."},
        {"name": "Lodge",     "key": "lodge",      "desc": "Rest and recover at the inn."},
        {"name": "Shop",      "key": "shop",       "desc": "Coming soon..."},
        {"name": "Tavern",    "key": "tavern",     "desc": "Gather party members together while sharing drinks."},
        {"name": "Adventure", "key": "adventure",  "desc": "Coming soon..."},
    ]

    def __init__(self, screen: pygame.Surface, fonts: Dict, assets: Dict):
        super().__init__(screen, fonts, assets)
        self.selected = 3  # デフォルト: Tavern

    def _get_item_rects(self) -> List[pygame.Rect]:
        x = 100
        start_y = 280
        item_h = 50
        rects = []
        for i in range(len(self.LOCATIONS)):
            rects.append(pygame.Rect(x, start_y + i * item_h, 300, item_h))
        return rects

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            item_rects = self._get_item_rects()
            for i, rect in enumerate(item_rects):
                if rect.collidepoint(event.pos):
                    self.selected = i
                    return self.LOCATIONS[i]["key"]

        elif event.type == pygame.MOUSEMOTION:
            item_rects = self._get_item_rects()
            for i, rect in enumerate(item_rects):
                if rect.collidepoint(event.pos):
                    self.selected = i

        elif event.type == pygame.KEYDOWN:
            n = len(self.LOCATIONS)
            if event.key == pygame.K_UP:
                self.selected = (self.selected - 1) % n
            elif event.key == pygame.K_DOWN:
                self.selected = (self.selected + 1) % n
            elif event.key == pygame.K_RETURN:
                return self.LOCATIONS[self.selected]["key"]

        return None

    def draw(self):
        # 背景
        village_img = self.assets.get("village_img")
        if village_img:
            self.screen.blit(village_img, (0, 0))
            overlay = pygame.Surface((WINDOW.width, WINDOW.height),
                                     pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 80))
            self.screen.blit(overlay, (0, 0))
        else:
            self.screen.fill(C.black)

        # タイトル
        title = self.fonts["title"].render("Village", True, C.white)
        self.screen.blit(title, (100, 180))

        sub = self.fonts["small"].render("Where would you like to go?",
                                         True, C.parchment_dark)
        self.screen.blit(sub, (100, 220))

        # メニューリスト
        item_rects = self._get_item_rects()
        for i, (loc, rect) in enumerate(zip(self.LOCATIONS, item_rects)):
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

            name_surf = self.fonts["village"].render(loc["name"], True, color)
            self.screen.blit(name_surf, (rect.x, rect.y + 8))

        # 説明文
        loc = self.LOCATIONS[self.selected]
        desc_x = 500
        desc_y = 400
        for line in self.wrap_text(loc["desc"], self.fonts["body"], 500):
            desc_surf = self.fonts["body"].render(line, True, C.parchment)
            self.screen.blit(desc_surf, (desc_x, desc_y))
            desc_y += 24

        # 操作ヒント
        hint = self.fonts["small"].render(
            "Up/Down to select  |  Enter or Click to confirm",
            True, C.parchment_dark)
        self.screen.blit(hint, (100, WINDOW.height - 60))
