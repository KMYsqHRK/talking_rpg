import pygame
from typing import Dict, List, Optional

from settings.settings import WINDOW, C, UIButton


class BaseScreen:
    """全画面の基底クラス"""

    def __init__(self, screen: pygame.Surface, fonts: Dict, assets: Dict):
        self.screen = screen
        self.fonts = fonts
        self.assets = assets

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """イベント処理。画面遷移先を返す。Noneなら遷移なし。"""
        return None

    def draw(self):
        """画面描画"""
        pass

    @staticmethod
    def wrap_text(text: str, font: pygame.font.Font,
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

    def draw_placeholder(self, title: str, bg_img: Optional[pygame.Surface]):
        """汎用プレースホルダー画面（未実装場所用）"""
        if bg_img:
            self.screen.blit(bg_img, (0, 0))
            overlay = pygame.Surface((WINDOW.width, WINDOW.height),
                                     pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 100))
            self.screen.blit(overlay, (0, 0))
        else:
            self.screen.fill(C.black)

        t = self.fonts["title"].render(title, True, C.white)
        self.screen.blit(t, (WINDOW.width // 2 - t.get_width() // 2,
                             WINDOW.height // 2 - 60))

        msg = self.fonts["body"].render("Coming soon...", True, C.parchment_dark)
        self.screen.blit(msg, (WINDOW.width // 2 - msg.get_width() // 2,
                               WINDOW.height // 2))

        self.btn_back.draw(self.screen, self.fonts["body"])
