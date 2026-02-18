import pygame
from typing import Dict, Optional

from settings.settings import LAYOUT, C, UIButton
from screens.base import BaseScreen


class GuildScreen(BaseScreen):
    """ギルド画面"""

    def __init__(self, screen: pygame.Surface, fonts: Dict, assets: Dict):
        super().__init__(screen, fonts, assets)
        self.btn_back = UIButton(
            pygame.Rect(LAYOUT.padding, LAYOUT.padding, 120, 36),
            "< Village", C.gold, C.gold_dim, C.charcoal
        )

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.btn_back.clicked(event.pos):
                return "village"
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return "village"
        return None

    def draw(self):
        self.draw_placeholder("Guild", None)
