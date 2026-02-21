import pygame
import csv
import os
from typing import Dict, List, Optional, Tuple

from settings.settings import WINDOW, LAYOUT, C, UIButton
from screens.base import BaseScreen


class ShopScreen(BaseScreen):
    """ショップ画面 - アイテム購入"""

    # 内部状態
    ST_CATEGORY = "category"      # カテゴリ選択 (Weapon / Armor / Accessory)
    ST_ITEM_LIST = "item_list"    # アイテム一覧
    ST_CONFIRM = "confirm"        # 購入確認

    def __init__(self, screen: pygame.Surface, fonts: Dict, assets: Dict):
        super().__init__(screen, fonts, assets)

        self.state = self.ST_CATEGORY
        self.gold = 10000  # プレイヤーの所持金

        # カテゴリデータ
        self.categories: List[Dict] = []
        self.category_selected = 0

        # アイテムデータ
        self.items: List[Dict] = []
        self.item_selected = 0
        self.item_scroll = 0
        self.items_visible = 12  # 画面に表示する最大アイテム数

        # 購入確認
        self.confirm_selected = 0  # 0=Yes, 1=No

        # 購入メッセージ
        self.message = ""
        self.message_timer = 0

        # ボタン
        self.btn_back = UIButton(
            pygame.Rect(LAYOUT.padding, LAYOUT.padding, 120, 36),
            "< Village", C.gold, C.gold_dim, C.charcoal
        )

        # データ読み込み
        self._load_categories()

    def _load_categories(self):
        """shop.csvからカテゴリを読み込む"""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        path = os.path.join(base_dir, "data", "shop.csv")
        self.categories = []
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.categories.append(row)

    def _load_items(self, csv_filename: str):
        """指定CSVからアイテム一覧を読み込む"""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        path = os.path.join(base_dir, "data", csv_filename)
        self.items = []
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # 数値フィールドを変換
                    for key in row:
                        if key not in ("Name", "Description"):
                            try:
                                row[key] = int(row[key])
                            except (ValueError, TypeError):
                                pass
                    self.items.append(row)
        self.item_selected = 0
        self.item_scroll = 0

    def enter(self):
        """画面に入ったときの処理"""
        self.state = self.ST_CATEGORY
        self.category_selected = 0
        self.message = ""
        self.message_timer = 0

    # ---------- イベント処理 ----------

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return self._handle_back()
            elif self.state == self.ST_CATEGORY:
                return self._handle_category_key(event.key)
            elif self.state == self.ST_ITEM_LIST:
                return self._handle_item_list_key(event.key)
            elif self.state == self.ST_CONFIRM:
                return self._handle_confirm_key(event.key)

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.btn_back.clicked(event.pos):
                return self._handle_back()
            if self.state == self.ST_CATEGORY:
                self._handle_category_click(event.pos)
            elif self.state == self.ST_ITEM_LIST:
                self._handle_item_list_click(event.pos)
            elif self.state == self.ST_CONFIRM:
                self._handle_confirm_click(event.pos)

        elif event.type == pygame.MOUSEMOTION:
            if self.state == self.ST_CATEGORY:
                self._handle_category_hover(event.pos)
            elif self.state == self.ST_ITEM_LIST:
                self._handle_item_list_hover(event.pos)

        return None

    def _handle_back(self) -> Optional[str]:
        if self.state == self.ST_CONFIRM:
            self.state = self.ST_ITEM_LIST
        elif self.state == self.ST_ITEM_LIST:
            self.state = self.ST_CATEGORY
        else:
            return "village"
        return None

    def _handle_category_key(self, key: int) -> Optional[str]:
        n = len(self.categories)
        if n == 0:
            return None
        if key == pygame.K_UP:
            self.category_selected = (self.category_selected - 1) % n
        elif key == pygame.K_DOWN:
            self.category_selected = (self.category_selected + 1) % n
        elif key == pygame.K_RETURN:
            cat = self.categories[self.category_selected]
            self._load_items(cat["File"])
            self.state = self.ST_ITEM_LIST
        return None

    def _handle_item_list_key(self, key: int) -> Optional[str]:
        n = len(self.items)
        if n == 0:
            return None
        if key == pygame.K_UP:
            self.item_selected = (self.item_selected - 1) % n
            self._adjust_scroll()
        elif key == pygame.K_DOWN:
            self.item_selected = (self.item_selected + 1) % n
            self._adjust_scroll()
        elif key == pygame.K_RETURN:
            self.confirm_selected = 0
            self.state = self.ST_CONFIRM
        return None

    def _handle_confirm_key(self, key: int) -> Optional[str]:
        if key == pygame.K_LEFT or key == pygame.K_RIGHT:
            self.confirm_selected = 1 - self.confirm_selected
        elif key == pygame.K_RETURN:
            if self.confirm_selected == 0:
                self._buy_item()
            self.state = self.ST_ITEM_LIST
        return None

    def _adjust_scroll(self):
        if self.item_selected < self.item_scroll:
            self.item_scroll = self.item_selected
        elif self.item_selected >= self.item_scroll + self.items_visible:
            self.item_scroll = self.item_selected - self.items_visible + 1

    # ---------- マウス処理 ----------

    def _get_category_rects(self) -> List[pygame.Rect]:
        rects = []
        x = 100
        start_y = 200
        for i in range(len(self.categories)):
            rects.append(pygame.Rect(x, start_y + i * 60, 350, 50))
        return rects

    def _handle_category_click(self, pos: Tuple[int, int]):
        for i, rect in enumerate(self._get_category_rects()):
            if rect.collidepoint(pos):
                self.category_selected = i
                cat = self.categories[i]
                self._load_items(cat["File"])
                self.state = self.ST_ITEM_LIST

    def _handle_category_hover(self, pos: Tuple[int, int]):
        for i, rect in enumerate(self._get_category_rects()):
            if rect.collidepoint(pos):
                self.category_selected = i

    def _get_item_rects(self) -> List[pygame.Rect]:
        rects = []
        x = 60
        start_y = 140
        row_h = 44
        for i in range(self.items_visible):
            idx = self.item_scroll + i
            if idx >= len(self.items):
                break
            rects.append((idx, pygame.Rect(x, start_y + i * row_h, WINDOW.width - 120, row_h - 4)))
        return rects

    def _handle_item_list_click(self, pos: Tuple[int, int]):
        for idx, rect in self._get_item_rects():
            if rect.collidepoint(pos):
                self.item_selected = idx
                self.confirm_selected = 0
                self.state = self.ST_CONFIRM

    def _handle_item_list_hover(self, pos: Tuple[int, int]):
        for idx, rect in self._get_item_rects():
            if rect.collidepoint(pos):
                self.item_selected = idx

    def _get_confirm_rects(self) -> Tuple[pygame.Rect, pygame.Rect]:
        cx = WINDOW.width // 2
        cy = WINDOW.height // 2 + 60
        yes_rect = pygame.Rect(cx - 140, cy, 120, 40)
        no_rect = pygame.Rect(cx + 20, cy, 120, 40)
        return yes_rect, no_rect

    def _handle_confirm_click(self, pos: Tuple[int, int]):
        yes_rect, no_rect = self._get_confirm_rects()
        if yes_rect.collidepoint(pos):
            self.confirm_selected = 0
            self._buy_item()
            self.state = self.ST_ITEM_LIST
        elif no_rect.collidepoint(pos):
            self.confirm_selected = 1
            self.state = self.ST_ITEM_LIST

    # ---------- 購入処理 ----------

    def _buy_item(self):
        if self.item_selected >= len(self.items):
            return
        item = self.items[self.item_selected]
        price = item.get("Price", 0)
        if self.gold >= price:
            self.gold -= price
            self.message = f"Purchased {item['Name']}!"
            self.message_timer = 120  # 約4秒表示 (30fps)
        else:
            self.message = "Not enough gold!"
            self.message_timer = 90

    # ---------- 描画 ----------

    def draw(self):
        # メッセージタイマー更新
        if self.message_timer > 0:
            self.message_timer -= 1
            if self.message_timer <= 0:
                self.message = ""

        shop_imgg = self.assets.get("shop_img")
        if shop_imgg:
            self.screen.blit(shop_imgg, (0, 0))
            overlay = pygame.Surface((WINDOW.width, WINDOW.height),
                                     pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 80))
            self.screen.blit(overlay, (0, 0))
        else:
            self.screen.fill(C.black)

        # タイトルバー
        title_rect = pygame.Rect(0, 0, WINDOW.width, 50)
        pygame.draw.rect(self.screen, C.charcoal, title_rect)
        pygame.draw.line(self.screen, C.gold, (0, 50), (WINDOW.width, 50), 2)
        title = self.fonts["title"].render("Shop", True, C.gold)
        self.screen.blit(title, (WINDOW.width // 2 - title.get_width() // 2, 8))

        # 所持金表示
        gold_str = f"Gold: {self.gold:,}"
        gold_surf = self.fonts["header"].render(gold_str, True, C.gold)
        self.screen.blit(gold_surf, (WINDOW.width - gold_surf.get_width() - 30, 14))

        # 戻るボタン
        self.btn_back.text = "< Village" if self.state == self.ST_CATEGORY else "< Back"
        self.btn_back.draw(self.screen, self.fonts["body"])

        if self.state == self.ST_CATEGORY:
            self._draw_category()
        elif self.state == self.ST_ITEM_LIST:
            self._draw_item_list()

        # 購入確認オーバーレイ
        if self.state == self.ST_CONFIRM:
            self._draw_item_list()
            self._draw_confirm()

        # メッセージ表示
        if self.message:
            self._draw_message()

    def _draw_category(self):
        sub = self.fonts["body"].render("What would you like to buy?",
                                         True, C.parchment_dark)
        self.screen.blit(sub, (100, 150))

        rects = self._get_category_rects()
        for i, (cat, rect) in enumerate(zip(self.categories, rects)):
            selected = (i == self.category_selected)

            # 背景
            bg_color = C.wood_light if selected else C.wood
            pygame.draw.rect(self.screen, bg_color, rect, border_radius=6)
            pygame.draw.rect(self.screen, C.gold if selected else C.wood_dark,
                             rect, 2, border_radius=6)

            # カーソル
            if selected:
                tri_x = rect.x - 10
                tri_y = rect.y + rect.h // 2
                pygame.draw.polygon(self.screen, C.gold, [
                    (tri_x - 14, tri_y - 8),
                    (tri_x - 14, tri_y + 8),
                    (tri_x, tri_y),
                ])

            # テキスト
            name_surf = self.fonts["header"].render(cat["Category"], True,
                                                      C.gold if selected else C.parchment)
            self.screen.blit(name_surf, (rect.x + 15, rect.y + 5))

            desc_surf = self.fonts["small"].render(cat["Description"], True,
                                                     C.parchment_dark)
            self.screen.blit(desc_surf, (rect.x + 15, rect.y + 30))

        # 操作ヒント
        hint = self.fonts["small"].render(
            "Up/Down to select  |  Enter or Click to confirm  |  Esc to go back",
            True, C.parchment_dark)
        self.screen.blit(hint, (100, WINDOW.height - 60))

    def _draw_item_list(self):
        # カテゴリ名表示
        cat = self.categories[self.category_selected]
        cat_label = self.fonts["body"].render(
            f"Buy {cat['Category']}", True, C.parchment_dark)
        self.screen.blit(cat_label, (60, 70))

        # ヘッダー行
        hx = 60
        hy = 110
        header_bg = pygame.Rect(hx, hy, WINDOW.width - 120, 26)
        pygame.draw.rect(self.screen, C.charcoal, header_bg)

        col_name_x = hx + 10
        col_stat_x = hx + 380
        col_price_x = hx + 560
        col_desc_x = hx + 680

        self.screen.blit(self.fonts["small"].render("Name", True, C.gold),
                         (col_name_x, hy + 4))

        # カテゴリに応じたステータスヘッダー
        if cat["Category"] == "Weapon":
            stat_header = "ATK"
        elif cat["Category"] == "Armor":
            stat_header = "DEF"
        else:
            stat_header = "Stats"
        self.screen.blit(self.fonts["small"].render(stat_header, True, C.gold),
                         (col_stat_x, hy + 4))
        self.screen.blit(self.fonts["small"].render("Price", True, C.gold),
                         (col_price_x, hy + 4))
        self.screen.blit(self.fonts["small"].render("Description", True, C.gold),
                         (col_desc_x, hy + 4))

        # アイテム一覧
        start_y = 140
        row_h = 44

        for vi in range(self.items_visible):
            idx = self.item_scroll + vi
            if idx >= len(self.items):
                break

            item = self.items[idx]
            selected = (idx == self.item_selected)
            ry = start_y + vi * row_h

            # 行背景
            row_rect = pygame.Rect(hx, ry, WINDOW.width - 120, row_h - 4)
            if selected:
                bg_color = C.wood_light
            elif vi % 2 == 0:
                bg_color = C.wood
            else:
                bg_color = C.wood_dark
            pygame.draw.rect(self.screen, bg_color, row_rect, border_radius=4)

            if selected:
                pygame.draw.rect(self.screen, C.gold, row_rect, 2, border_radius=4)
                # カーソル
                tri_x = hx - 4
                tri_y = ry + row_h // 2 - 2
                pygame.draw.polygon(self.screen, C.gold, [
                    (tri_x - 12, tri_y - 7),
                    (tri_x - 12, tri_y + 7),
                    (tri_x, tri_y),
                ])

            text_color = C.gold if selected else C.parchment

            # Name
            name_surf = self.fonts["body"].render(item["Name"], True, text_color)
            self.screen.blit(name_surf, (col_name_x, ry + 10))

            # Stats
            if cat["Category"] == "Weapon":
                stat_str = f"+{item.get('ATK', 0)}"
            elif cat["Category"] == "Armor":
                stat_str = f"+{item.get('DEF', 0)}"
            else:
                # アクセサリーは複数ステータス
                parts = []
                for s in ("HP", "ATK", "DEF", "WIS", "LUC", "AGI"):
                    v = item.get(s, 0)
                    if v:
                        parts.append(f"{s}+{v}")
                stat_str = " ".join(parts) if parts else "-"

            stat_surf = self.fonts["stat"].render(stat_str, True, C.green)
            self.screen.blit(stat_surf, (col_stat_x, ry + 12))

            # Price
            price = item.get("Price", 0)
            affordable = self.gold >= price
            price_color = C.gold if affordable else C.red
            price_surf = self.fonts["stat"].render(f"{price:,}G", True, price_color)
            self.screen.blit(price_surf, (col_price_x, ry + 12))

            # Description (truncated)
            desc = item.get("Description", "")
            desc_surf = self.fonts["small"].render(desc, True, C.parchment_dark)
            # clip description to available space
            desc_area = pygame.Rect(col_desc_x, ry, WINDOW.width - col_desc_x - 70, row_h)
            self.screen.set_clip(desc_area)
            self.screen.blit(desc_surf, (col_desc_x, ry + 14))
            self.screen.set_clip(None)

        # スクロールインジケーター
        total = len(self.items)
        if total > self.items_visible:
            if self.item_scroll > 0:
                up_surf = self.fonts["small"].render("^ more items above ^", True, C.parchment_dark)
                self.screen.blit(up_surf, (WINDOW.width // 2 - up_surf.get_width() // 2,
                                            start_y - 18))
            if self.item_scroll + self.items_visible < total:
                down_surf = self.fonts["small"].render("v more items below v", True, C.parchment_dark)
                self.screen.blit(down_surf, (WINDOW.width // 2 - down_surf.get_width() // 2,
                                              start_y + self.items_visible * row_h + 4))

        # 選択中アイテムの詳細パネル
        if self.items and self.item_selected < len(self.items):
            self._draw_item_detail(self.items[self.item_selected], cat["Category"])

        # 操作ヒント
        hint = self.fonts["small"].render(
            "Up/Down to select  |  Enter or Click to buy  |  Esc to go back",
            True, C.parchment_dark)
        self.screen.blit(hint, (60, WINDOW.height - 30))

    def _draw_item_detail(self, item: Dict, category: str):
        """選択中アイテムの詳細表示"""
        panel_y = WINDOW.height - 160
        panel_rect = pygame.Rect(60, panel_y, WINDOW.width - 120, 100)

        bg = pygame.Surface((panel_rect.w, panel_rect.h), pygame.SRCALPHA)
        bg.fill((*C.charcoal, 200))
        self.screen.blit(bg, panel_rect.topleft)
        pygame.draw.rect(self.screen, C.gold_dim, panel_rect, 1, border_radius=6)

        x = panel_rect.x + 15
        y = panel_rect.y + 10

        # アイテム名
        name_surf = self.fonts["header"].render(item["Name"], True, C.gold)
        self.screen.blit(name_surf, (x, y))

        # 価格
        price_surf = self.fonts["body"].render(f"{item.get('Price', 0):,} Gold",
                                                  True, C.gold)
        self.screen.blit(price_surf, (x + 400, y))

        y += 30

        # ステータス
        if category == "Weapon":
            stat_surf = self.fonts["body"].render(f"ATK +{item.get('ATK', 0)}", True, C.green)
            self.screen.blit(stat_surf, (x, y))
        elif category == "Armor":
            stat_surf = self.fonts["body"].render(f"DEF +{item.get('DEF', 0)}", True, C.green)
            self.screen.blit(stat_surf, (x, y))
        else:
            sx = x
            for s in ("HP", "ATK", "DEF", "WIS", "LUC", "AGI"):
                v = item.get(s, 0)
                if v:
                    ss = self.fonts["stat"].render(f"{s}+{v}", True, C.green)
                    self.screen.blit(ss, (sx, y))
                    sx += 70

        # 説明
        desc_surf = self.fonts["body"].render(item.get("Description", ""), True, C.parchment)
        self.screen.blit(desc_surf, (x, y + 24))

    def _draw_confirm(self):
        """購入確認オーバーレイ"""
        overlay = pygame.Surface((WINDOW.width, WINDOW.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))

        # ダイアログボックス
        dw, dh = 420, 200
        dx = WINDOW.width // 2 - dw // 2
        dy = WINDOW.height // 2 - dh // 2
        dialog_rect = pygame.Rect(dx, dy, dw, dh)

        pygame.draw.rect(self.screen, C.wood_dark, dialog_rect, border_radius=8)
        pygame.draw.rect(self.screen, C.gold, dialog_rect, 2, border_radius=8)

        item = self.items[self.item_selected]

        # タイトル
        title = self.fonts["header"].render("Purchase?", True, C.gold)
        self.screen.blit(title, (dx + dw // 2 - title.get_width() // 2, dy + 20))

        # アイテム名と価格
        name_surf = self.fonts["body"].render(item["Name"], True, C.parchment)
        self.screen.blit(name_surf, (dx + dw // 2 - name_surf.get_width() // 2, dy + 55))

        price = item.get("Price", 0)
        price_surf = self.fonts["body"].render(f"{price:,} Gold", True, C.gold)
        self.screen.blit(price_surf, (dx + dw // 2 - price_surf.get_width() // 2, dy + 80))

        affordable = self.gold >= price
        if not affordable:
            warn = self.fonts["small"].render("Not enough gold!", True, C.red)
            self.screen.blit(warn, (dx + dw // 2 - warn.get_width() // 2, dy + 108))

        # Yes / No ボタン
        yes_rect, no_rect = self._get_confirm_rects()

        for i, (rect, label) in enumerate([(yes_rect, "Yes"), (no_rect, "No")]):
            selected = (i == self.confirm_selected)
            if i == 0 and not affordable:
                bg = C.grey
            elif selected:
                bg = C.gold
            else:
                bg = C.wood_light
            pygame.draw.rect(self.screen, bg, rect, border_radius=6)
            pygame.draw.rect(self.screen, C.gold if selected else C.wood_dark,
                             rect, 2, border_radius=6)
            txt = self.fonts["body"].render(label, True, C.charcoal)
            self.screen.blit(txt, (rect.x + rect.w // 2 - txt.get_width() // 2,
                                   rect.y + rect.h // 2 - txt.get_height() // 2))

    def _draw_message(self):
        """購入結果メッセージ"""
        msg_surf = self.fonts["header"].render(self.message, True, C.white)
        msg_w = msg_surf.get_width() + 40
        msg_h = 40
        msg_x = WINDOW.width // 2 - msg_w // 2
        msg_y = 55

        bg_rect = pygame.Rect(msg_x, msg_y, msg_w, msg_h)
        is_success = "Purchased" in self.message
        bg_color = (*C.green, 220) if is_success else (*C.red, 220)
        bg = pygame.Surface((msg_w, msg_h), pygame.SRCALPHA)
        bg.fill(bg_color)
        self.screen.blit(bg, (msg_x, msg_y))
        pygame.draw.rect(self.screen, C.gold, bg_rect, 1, border_radius=4)

        self.screen.blit(msg_surf, (msg_x + 20, msg_y + 8))
