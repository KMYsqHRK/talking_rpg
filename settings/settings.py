import pygame
from typing import Dict, List, NamedTuple, Tuple

# ============================================
# 定数（メモリ効率の良い NamedTuple 構造体）
# ============================================

class WindowConfig(NamedTuple):
    width: int
    height: int
    fps: int

class LayoutConfig(NamedTuple):
    left_panel_w: int
    right_panel_x: int
    right_panel_w: int
    padding: int

class PortraitConfig(NamedTuple):
    width: int
    height: int

class ColorPalette(NamedTuple):
    wood: Tuple[int, int, int]
    wood_dark: Tuple[int, int, int]
    wood_light: Tuple[int, int, int]
    parchment: Tuple[int, int, int]
    parchment_dark: Tuple[int, int, int]
    gold: Tuple[int, int, int]
    gold_dim: Tuple[int, int, int]
    charcoal: Tuple[int, int, int]
    white: Tuple[int, int, int]
    black: Tuple[int, int, int]
    user_bg: Tuple[int, int, int]
    npc_bg: Tuple[int, int, int]
    green: Tuple[int, int, int]
    red: Tuple[int, int, int]
    orange: Tuple[int, int, int]
    yellow: Tuple[int, int, int]
    grey: Tuple[int, int, int]
    input_bg: Tuple[int, int, int]
    firelight: Tuple[int, int, int]

WINDOW = WindowConfig(width=1200, height=800, fps=30)

LAYOUT = LayoutConfig(
    left_panel_w=380,
    right_panel_x=380,
    right_panel_w=WINDOW.width - 380,
    padding=20,
)

PORTRAIT = PortraitConfig(width=250, height=320)

C = ColorPalette(
    wood=(101, 67, 33),
    wood_dark=(61, 43, 31),
    wood_light=(139, 90, 43),
    parchment=(245, 235, 220),
    parchment_dark=(220, 200, 170),
    gold=(255, 215, 0),
    gold_dim=(180, 150, 30),
    charcoal=(40, 40, 40),
    white=(255, 255, 255),
    black=(0, 0, 0),
    user_bg=(170, 195, 220),
    npc_bg=(220, 200, 175),
    green=(76, 175, 80),
    red=(211, 47, 47),
    orange=(255, 152, 0),
    yellow=(255, 235, 59),
    grey=(160, 160, 160),
    input_bg=(255, 250, 240),
    firelight=(255, 147, 41),
)


# ============================================
# UIButton
# ============================================

class UIButton:
    """再利用可能なボタン"""

    def __init__(self, rect: pygame.Rect, text: str,
                 color: Tuple, hover_color: Tuple,
                 text_color: Tuple = C.charcoal,
                 disabled_color: Tuple = C.grey):
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
        pygame.draw.rect(surface, C.wood_dark, self.rect, 2, border_radius=6)

        # テキスト
        txt = font.render(self.text, True,
                          self.text_color if self.enabled else C.white)
        txt_rect = txt.get_rect(center=self.rect.center)
        surface.blit(txt, txt_rect)

    def clicked(self, pos: Tuple[int, int]) -> bool:
        return self.enabled and self.rect.collidepoint(pos)