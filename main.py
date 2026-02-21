"""
Pygame RPG酒場 勧誘シーン GUI
画面遷移とメインループを担当
"""

import pygame
import sys
import os

from settings.settings import WINDOW, PORTRAIT, C
from screens.village import VillageScreen
from screens.tavern import TavernScreen
from screens.lodge import LodgeScreen
from screens.guild import GuildScreen
from screens.shop import ShopScreen
from screens.adventure import AdventureScreen


class Game:
    """画面遷移とメインループ"""

    def __init__(self):
        pygame.init()
        screen = pygame.display.set_mode((WINDOW.width, WINDOW.height))
        pygame.display.set_caption("RPG Village")
        self.clock = pygame.time.Clock()
        self.screen = screen

        fonts = self._init_fonts()
        assets = self._load_assets()

        self.screens = {
            "village":   VillageScreen(screen, fonts, assets),
            "tavern":    TavernScreen(screen, fonts, assets),
            "lodge":     LodgeScreen(screen, fonts, assets),
            "guild":     GuildScreen(screen, fonts, assets),
            "shop":      ShopScreen(screen, fonts, assets),
            "adventure": AdventureScreen(screen, fonts, assets),
        }
        self.current = "village"

    def _init_fonts(self) -> dict:
        candidates = ["notosanscjkjp", "notosans", "dejavusans",
                       "liberationsans", "arial", "freesans"]
        font_name = None
        for name in candidates:
            if pygame.font.match_font(name):
                font_name = name
                break

        if font_name:
            path = pygame.font.match_font(font_name)
            return {
                "title":   pygame.font.Font(path, 32),
                "header":  pygame.font.Font(path, 22),
                "body":    pygame.font.Font(path, 18),
                "small":   pygame.font.Font(path, 14),
                "stat":    pygame.font.Font(path, 16),
                "village": pygame.font.Font(path, 26),
            }
        else:
            return {
                "title":   pygame.font.Font(None, 36),
                "header":  pygame.font.Font(None, 26),
                "body":    pygame.font.Font(None, 20),
                "small":   pygame.font.Font(None, 16),
                "stat":    pygame.font.Font(None, 18),
                "village": pygame.font.Font(None, 30),
            }

    def _load_assets(self) -> dict:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        assets = {}

        # 背景画像
        for key, filename in [("village_img", "village.png"),
                               ("tavern_img", "tavern.png"),
                               ("lodge_img", "lodge.png"),
                               ("shop_img", "shop.png"),
                               ]:
            path = os.path.join(base_dir, "img", filename)
            if os.path.exists(path):
                raw = pygame.image.load(path).convert()
                assets[key] = pygame.transform.smoothscale(
                    raw, (WINDOW.width, WINDOW.height))
            else:
                assets[key] = None

        # キャラクターポートレート
        portrait_path = os.path.join(base_dir, "img", "mage-man.png")
        if os.path.exists(portrait_path):
            raw = pygame.image.load(portrait_path).convert_alpha()
            assets["portrait_img"] = pygame.transform.smoothscale(
                raw, (PORTRAIT.width, PORTRAIT.height))
        else:
            placeholder = pygame.Surface((PORTRAIT.width, PORTRAIT.height))
            placeholder.fill(C.wood_dark)
            assets["portrait_img"] = placeholder

        return assets

    def _switch_to(self, name: str):
        """画面遷移"""
        self.current = name
        screen_obj = self.screens[name]
        if hasattr(screen_obj, "enter"):
            screen_obj.enter()

    def run(self):
        """メインゲームループ"""
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                result = self.screens[self.current].handle_event(event)
                if result and result != self.current:
                    self._switch_to(result)

            self.screens[self.current].draw()
            pygame.display.flip()
            self.clock.tick(WINDOW.fps)


if __name__ == "__main__":
    game = Game()
    game.run()
