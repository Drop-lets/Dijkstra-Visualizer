"""自定义 Pygame 控件库 — 使用 freetype 高质量字体渲染"""

from __future__ import annotations
import pygame
import pygame.freetype
from config import (
    BTN_IDLE, BTN_HOVER, BTN_ACTIVE, BTN_ACTIVE_HOVER,
    BTN_TEXT, BTN_TEXT_WHITE, BTN_DISABLED, BTN_DISABLED_TEXT,
    TABLE_HEADER_BG, TABLE_HEADER_TEXT, TABLE_ROW_EVEN, TABLE_ROW_ODD,
    TABLE_ROW_HL, TABLE_TEXT, TABLE_BORDER,
    PANEL_BG, PANEL_BORDER,
    INPUT_BG, INPUT_BORDER, INPUT_TEXT, INPUT_CURSOR,
    FONT_FAMILY, FONT_FALLBACK, BTN_FONT_SIZE, TABLE_FONT_SIZE,
    SEPARATOR_COLOR,
)


def _try_font(name: str) -> bool:
    try:
        pygame.freetype.SysFont(name, 12)
        return True
    except Exception:
        return False


def _make_font(size: int) -> pygame.freetype.Font:
    for family in (FONT_FAMILY, FONT_FALLBACK):
        try:
            return pygame.freetype.SysFont(family, size)
        except Exception:
            continue
    return pygame.freetype.Font(None, size)


def _draw_text(surface, font, text, x, y, color, align="left", max_w=0):
    """用 freetype 高质量渲染文本"""
    if not text:
        return
    rect = font.get_rect(text)
    if align == "center":
        x = x - rect.width // 2
    elif align == "right":
        x = x - rect.width
    font.render_to(surface, (x, y), text, color)


# ============================================================
# Button
# ============================================================
class Button:
    def __init__(self, rect: pygame.Rect, text: str, callback=None,
                 is_toggle: bool = False, enabled: bool = True):
        self.rect = rect
        self.text = text
        self.callback = callback
        self.is_toggle = is_toggle
        self.toggled = False
        self.enabled = enabled
        self._hovered = False
        self._font = _make_font(BTN_FONT_SIZE)

    def handle_event(self, event: pygame.event.Event) -> bool:
        if not self.enabled:
            return False
        if event.type == pygame.MOUSEMOTION:
            self._hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                if self.is_toggle:
                    self.toggled = not self.toggled
                if self.callback:
                    self.callback()
                return True
        return False

    def draw(self, surface: pygame.Surface):
        if not self.enabled:
            bg, tc = BTN_DISABLED, BTN_DISABLED_TEXT
        elif self.is_toggle and self.toggled:
            bg = BTN_ACTIVE_HOVER if self._hovered else BTN_ACTIVE
            tc = BTN_TEXT_WHITE
        elif self._hovered:
            bg, tc = BTN_HOVER, BTN_TEXT
        else:
            bg, tc = BTN_IDLE, BTN_TEXT

        r = self.rect
        pygame.draw.rect(surface, bg, r, border_radius=6)
        tr = self._font.get_rect(self.text)
        tx = r.centerx - tr.width // 2
        ty = r.centery - tr.height // 2
        self._font.render_to(surface, (tx, ty), self.text, tc)

    @property
    def hovered(self) -> bool:
        return self._hovered

    def set_enabled(self, val: bool):
        self.enabled = val
        if not val:
            self._hovered = False


# ============================================================
# ToggleGroup
# ============================================================
class ToggleGroup:
    def __init__(self, buttons: list[Button] | None = None):
        self.buttons: list[Button] = buttons if buttons else []
        for b in self.buttons:
            b.is_toggle = True

    def add(self, btn: Button):
        btn.is_toggle = True
        self.buttons.append(btn)

    def activate(self, index: int):
        for i, b in enumerate(self.buttons):
            b.toggled = (i == index)

    def handle_event(self, event: pygame.event.Event) -> int:
        for i, b in enumerate(self.buttons):
            if b.handle_event(event):
                for j, other in enumerate(self.buttons):
                    if j != i:
                        other.toggled = False
                return i
        return -1

    def draw(self, surface: pygame.Surface):
        for b in self.buttons:
            b.draw(surface)

    @property
    def active_index(self) -> int:
        for i, b in enumerate(self.buttons):
            if b.toggled:
                return i
        return 0


# ============================================================
# Label（支持滚动条）
# ============================================================
class Label:
    SB_W = 8
    SB_MARGIN = 3

    def __init__(self, rect: pygame.Rect, text: str = "", font_size: int = 14,
                 color: tuple = BTN_TEXT, align: str = "left",
                 bg_color: tuple | None = None, bold: bool = False):
        self.rect = rect
        self.text = text
        self.color = color
        self.align = align
        self.bg_color = bg_color
        self._font = _make_font(font_size)
        self.scroll_y = 0
        self._scroll_dragging = False
        self._scroll_drag_start_y = 0
        self._scroll_drag_start_scroll = 0
        self._padding_top = 4
        self._wrapped_cache: list[str] | None = None  # 换行缓存

    def set_text(self, text: str):
        self.text = text
        self._wrapped_cache = None  # 文本变化 → 失效缓存
        self.scroll_y = max(0, min(self.scroll_y, self._max_scroll))

    def _wrap_line(self, line: str, max_width: int) -> list[str]:
        """将单行文本按 max_width 折行，优先在空格处断行，否则按字符断行"""
        if not line:
            return [""]
        # 整行放得下 → 直接返回
        if self._font.get_rect(line).width <= max_width:
            return [line]

        result: list[str] = []
        remaining = line
        while remaining:
            # 二分查找最佳断点
            lo, hi = 0, len(remaining)
            best = 0
            while lo <= hi:
                mid = (lo + hi) // 2
                w = self._font.get_rect(remaining[:mid]).width
                if w <= max_width:
                    best = mid
                    lo = mid + 1
                else:
                    hi = mid - 1

            if best == 0:
                # 单个字符就超宽 → 强制取1字符
                best = 1

            # 尝试在空格处断行（回退到最近的空格）
            break_at = best
            for space_ch in (" ", "，", "。", "、", "；", "：", "）", "】"):
                pos = remaining.rfind(space_ch, 0, best)
                if pos > best // 2:  # 空格位置不要太靠前
                    break_at = pos + 1
                    break

            result.append(remaining[:break_at])
            remaining = remaining[break_at:]

        return result

    # ---- 换行 ----

    @property
    def _wrap_width(self) -> int:
        """可用于文字换行的最大宽度（始终预留滚动条空间，打破循环依赖）"""
        return max(40, self.rect.width - 16 - self.SB_W - self.SB_MARGIN - 2)

    def _get_wrapped_lines(self) -> list[str]:
        """返回换行后的全部文字行（带缓存，文本不变不重复计算）"""
        if self._wrapped_cache is not None:
            return self._wrapped_cache

        raw_lines = self.text.split("\n") if self.text else []
        result: list[str] = []
        w = self._wrap_width
        for line in raw_lines:
            if not line and raw_lines:
                result.append("")  # 保留空行
                continue
            result.extend(self._wrap_line(line, w))

        self._wrapped_cache = result
        return result

    # ---- 滚动条几何 ----

    @property
    def _lh(self) -> int:
        return self._font.get_sized_height() + 2

    @property
    def _line_count(self) -> int:
        return len(self._get_wrapped_lines())

    @property
    def _content_h(self) -> int:
        return self._line_count * self._lh

    @property
    def _max_scroll(self) -> int:
        return max(0, self._content_h - self.rect.height + self._padding_top * 2)

    @property
    def _sb_visible(self) -> bool:
        return self._max_scroll > 0

    def _sb_track_rect(self) -> pygame.Rect:
        return pygame.Rect(
            self.rect.right - self.SB_W - self.SB_MARGIN,
            self.rect.y,
            self.SB_W,
            self.rect.height,
        )

    def _sb_thumb_rect(self) -> pygame.Rect:
        if not self._sb_visible:
            return pygame.Rect(0, 0, 0, 0)
        track = self._sb_track_rect()
        ratio = self.rect.height / max(1, self._content_h)
        thumb_h = max(20, int(track.height * ratio))
        scroll_ratio = self.scroll_y / self._max_scroll
        thumb_y = track.y + int((track.height - thumb_h) * scroll_ratio)
        return pygame.Rect(track.x + 1, thumb_y, track.width - 2, thumb_h)

    # ---- 事件 ----

    def handle_event(self, event: pygame.event.Event) -> bool:
        if not self._sb_visible:
            return False
        mx, my = pygame.mouse.get_pos()

        if event.type == pygame.MOUSEWHEEL:
            if self.rect.collidepoint(mx, my) or self._sb_track_rect().collidepoint(mx, my):
                delta = -event.y * 28
                self.scroll_y = max(0, min(self._max_scroll, self.scroll_y + delta))
                return True

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            track = self._sb_track_rect()
            thumb = self._sb_thumb_rect()
            if thumb.collidepoint(mx, my):
                self._scroll_dragging = True
                self._scroll_drag_start_y = my
                self._scroll_drag_start_scroll = self.scroll_y
                return True
            elif track.collidepoint(mx, my):
                ratio = (my - track.y - thumb.height / 2) / max(1, track.height - thumb.height)
                self.scroll_y = max(0, min(self._max_scroll, int(ratio * self._max_scroll)))
                return True

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._scroll_dragging = False

        elif event.type == pygame.MOUSEMOTION and self._scroll_dragging:
            track = self._sb_track_rect()
            thumb = self._sb_thumb_rect()
            dy = my - self._scroll_drag_start_y
            track_len = max(1, track.height - thumb.height)
            ratio = dy / track_len
            self.scroll_y = max(0, min(self._max_scroll,
                                       int(self._scroll_drag_start_scroll + ratio * self._max_scroll)))
            return True

        return False

    # ---- 绘制 ----

    def draw(self, surface: pygame.Surface):
        if self.bg_color:
            pygame.draw.rect(surface, self.bg_color, self.rect, border_radius=4)

        lh = self._lh
        sb_vis = self._sb_visible
        wrapped_lines = self._get_wrapped_lines()

        # 文字区域 clip：始终预留滚动条空间（与 _wrap_width 一致）
        sb_reserve = self.SB_W + self.SB_MARGIN + 2
        text_clip = pygame.Rect(
            self.rect.x, self.rect.y,
            self.rect.width - sb_reserve, self.rect.height,
        )
        saved_clip = surface.get_clip()
        surface.set_clip(text_clip)

        y = self.rect.y + self._padding_top - self.scroll_y
        for line in wrapped_lines:
            # 跳过完全在上方不可见的行
            if y + lh <= self.rect.y:
                y += lh
                continue
            # 跳过起始在上方（半行裁切）的行
            if y < self.rect.y:
                y += lh
                continue
            # 行底部超出 → 停止（只渲染完整行）
            if y + lh > self.rect.bottom:
                break

            tr = self._font.get_rect(line)
            if self.align == "center":
                x = text_clip.centerx - tr.width // 2
            elif self.align == "right":
                x = text_clip.right - tr.width - 8
            else:
                x = self.rect.x + 8
            self._font.render_to(surface, (x, y), line, self.color)
            y += lh

        surface.set_clip(saved_clip)

        # 滚动条
        if sb_vis:
            track = self._sb_track_rect()
            pygame.draw.rect(surface, (235, 237, 240), track, border_radius=4)
            thumb = self._sb_thumb_rect()
            thumb_color = (160, 165, 175) if self._scroll_dragging else (190, 195, 205)
            pygame.draw.rect(surface, thumb_color, thumb, border_radius=4)


# ============================================================
# Panel
# ============================================================
class Panel:
    def __init__(self, rect: pygame.Rect, title: str = "",
                 bg_color: tuple = PANEL_BG, border_color: tuple = PANEL_BORDER):
        self.rect = rect
        self.title = title
        self.bg_color = bg_color
        self.border_color = border_color
        self.children: list = []
        self._title_font = _make_font(13) if not pygame.freetype.get_default_font() else _make_font(13)

    def add(self, widget):
        self.children.append(widget)
        return widget

    def draw(self, surface: pygame.Surface):
        r = self.rect
        pygame.draw.rect(surface, self.bg_color, r, border_radius=8)
        pygame.draw.rect(surface, self.border_color, r, width=1, border_radius=8)

        if self.title:
            self._title_font.render_to(surface, (r.x + 12, r.y + 10), self.title, BTN_TEXT)
            sep_y = r.y + 28
            pygame.draw.line(surface, self.border_color,
                             (r.x + 10, sep_y), (r.right - 10, sep_y))

        for child in self.children:
            child.draw(surface)


# ============================================================
# Table（带滚动条）
# ============================================================
class Table:
    SB_W = 8           # 滚动条宽度
    SB_MARGIN = 3      # 滚动条与内容间距

    def __init__(self, rect: pygame.Rect, headers: list[str] | None = None):
        self.rect = rect
        self.headers = headers if headers else []
        self.rows: list[list[str]] = []
        self._font = _make_font(TABLE_FONT_SIZE)
        self._header_font = _make_font(TABLE_FONT_SIZE)
        self.row_height = 24
        self.header_height = 28
        self._highlight_rows: set[int] = set()
        self.scroll_y = 0
        self._scroll_dragging = False
        self._scroll_drag_start_y = 0
        self._scroll_drag_start_scroll = 0
        self._col_widths_cache: list[int] | None = None  # 列宽缓存

    # ---- 滚动条几何 ----

    @property
    def _sb_visible(self) -> bool:
        return self._max_scroll > 0

    @property
    def _content_h(self) -> int:
        return self.header_height + len(self.rows) * self.row_height

    @property
    def _max_scroll(self) -> int:
        return max(0, self._content_h - self.rect.height)

    def _sb_track_rect(self) -> pygame.Rect:
        """滚动条轨道"""
        return pygame.Rect(
            self.rect.right - self.SB_W - self.SB_MARGIN,
            self.rect.y,
            self.SB_W,
            self.rect.height,
        )

    def _sb_thumb_rect(self) -> pygame.Rect:
        """滚动条滑块"""
        if not self._sb_visible:
            return pygame.Rect(0, 0, 0, 0)
        track = self._sb_track_rect()
        ratio = self.rect.height / self._content_h
        thumb_h = max(20, int(track.height * ratio))
        scroll_ratio = self.scroll_y / self._max_scroll
        thumb_y = track.y + int((track.height - thumb_h) * scroll_ratio)
        return pygame.Rect(track.x + 1, thumb_y, track.width - 2, thumb_h)

    @property
    def _content_width(self) -> int:
        """内容区域宽度（除去滚动条）"""
        if self._sb_visible:
            return self.rect.width - self.SB_W - self.SB_MARGIN - 2
        return self.rect.width

    # ---- 数据 ----

    def set_data(self, headers: list[str], rows: list[list[str]]):
        self.headers = headers
        self.rows = rows
        self._col_widths_cache = None  # 数据变了 → 列宽失效
        # 数据变化时把滚动位置钳制在有效范围
        self.scroll_y = max(0, min(self.scroll_y, self._max_scroll))

    def clear_highlights(self):
        self._highlight_rows.clear()

    def add_highlight(self, row_index: int):
        self._highlight_rows.add(row_index)

    # ---- 事件 ----

    def handle_event(self, event: pygame.event.Event) -> bool:
        """处理滚动相关事件。返回 True 表示事件已消费。"""
        if not self._sb_visible:
            return False

        mx, my = pygame.mouse.get_pos()

        if event.type == pygame.MOUSEWHEEL:
            if self.rect.collidepoint(mx, my) or self._sb_track_rect().collidepoint(mx, my):
                # macOS 自然滚动方向：precise_y > 0 = 内容上移 = scroll_y 减小
                delta = -event.y * 28
                self.scroll_y = max(0, min(self._max_scroll, self.scroll_y + delta))
                return True

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            track = self._sb_track_rect()
            thumb = self._sb_thumb_rect()
            if thumb.collidepoint(mx, my):
                self._scroll_dragging = True
                self._scroll_drag_start_y = my
                self._scroll_drag_start_scroll = self.scroll_y
                return True
            elif track.collidepoint(mx, my):
                # 点击轨道空白处 → 跳转
                ratio = (my - track.y - thumb.height / 2) / max(1, track.height - thumb.height)
                self.scroll_y = max(0, min(self._max_scroll, int(ratio * self._max_scroll)))
                return True

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._scroll_dragging = False

        elif event.type == pygame.MOUSEMOTION and self._scroll_dragging:
            track = self._sb_track_rect()
            thumb = self._sb_thumb_rect()
            dy = my - self._scroll_drag_start_y
            track_len = max(1, track.height - thumb.height)
            ratio = dy / track_len
            self.scroll_y = max(
                0, min(self._max_scroll,
                       int(self._scroll_drag_start_scroll + ratio * self._max_scroll)))
            return True

        return False

    # ---- 绘制 ----

    def draw(self, surface: pygame.Surface):
        clip = surface.get_clip()
        surface.set_clip(self.rect)

        sb_vis = self._sb_visible
        cw = self._content_width

        # 列宽（缓存：仅在数据变化时重新计算）
        if self._col_widths_cache is not None:
            col_widths = self._col_widths_cache
        elif not self.headers:
            col_widths = [cw]
        elif not self.rows:
            col_widths = [cw // len(self.headers)] * len(self.headers)
        else:
            col_widths = []
            for c in range(len(self.headers)):
                max_w = self._header_font.get_rect(self.headers[c]).width + 20
                for row in self.rows:
                    if c < len(row):
                        w = self._font.get_rect(str(row[c])).width + 20
                        if w > max_w:
                            max_w = w
                col_widths.append(max_w)
            self._col_widths_cache = col_widths

        # ---- 表头 ----
        x, y = self.rect.x, self.rect.y
        for c, header in enumerate(self.headers):
            hr = pygame.Rect(x, y, col_widths[c], self.header_height)
            pygame.draw.rect(surface, TABLE_HEADER_BG, hr)
            pygame.draw.line(surface, TABLE_BORDER,
                             (x, y + self.header_height - 1),
                             (x + col_widths[c], y + self.header_height - 1))
            self._header_font.render_to(surface, (x + 6, y + 5), header, TABLE_HEADER_TEXT)
            x += col_widths[c]

        # ---- 数据行（带滚动偏移） ----
        row_base_y = self.rect.y + self.header_height - self.scroll_y
        for i, row in enumerate(self.rows):
            ry = row_base_y + i * self.row_height
            # 完全在上方 → 跳过
            if ry + self.row_height <= self.rect.y:
                continue
            # 顶部被裁切 → 跳过，只渲染完整行
            if ry < self.rect.y:
                continue
            # 底部超出 → 停止
            if ry + self.row_height > self.rect.bottom:
                break

            rx = self.rect.x
            bg = TABLE_ROW_HL if i in self._highlight_rows else (
                TABLE_ROW_EVEN if i % 2 == 0 else TABLE_ROW_ODD)
            pygame.draw.rect(surface, bg, (rx, ry, cw, self.row_height))

            for c, val in enumerate(row):
                if c < len(col_widths):
                    self._font.render_to(surface, (rx + 6, ry + 3), str(val), TABLE_TEXT)
                    rx += col_widths[c]

        # ---- 滚动条 ----
        if sb_vis:
            track = self._sb_track_rect()
            # 轨道背景
            pygame.draw.rect(surface, (235, 237, 240), track, border_radius=4)
            # 滑块
            thumb = self._sb_thumb_rect()
            thumb_color = (160, 165, 175) if self._scroll_dragging else (190, 195, 205)
            pygame.draw.rect(surface, thumb_color, thumb, border_radius=4)

        surface.set_clip(clip)


# ============================================================
# TextInput
# ============================================================
class TextInput:
    def __init__(self, rect: pygame.Rect, initial_text: str = ""):
        self.rect = rect
        self.text = initial_text
        self.active = True
        self._font = _make_font(15)
        self._cursor_visible = True
        self._cursor_timer = 0
        self.return_pressed = False
        self.cancelled = False

    def handle_event(self, event: pygame.event.Event) -> bool:
        if not self.active:
            return False
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self.return_pressed = True
                self.active = False
                return True
            elif event.key == pygame.K_ESCAPE:
                self.cancelled = True
                self.active = False
                return True
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
                return True
            elif event.key == pygame.K_DELETE:
                self.text = ""
                return True
            elif event.unicode and event.unicode.isprintable():
                ch = event.unicode
                if ch.isdigit() or ch in ".-":
                    self.text += ch
                return True
        return False

    def update(self, dt_ms: int):
        self._cursor_timer += dt_ms
        if self._cursor_timer >= 500:
            self._cursor_timer = 0
            self._cursor_visible = not self._cursor_visible

    def draw(self, surface: pygame.Surface):
        r = self.rect
        pygame.draw.rect(surface, INPUT_BG, r, border_radius=5)
        pygame.draw.rect(surface, INPUT_BORDER, r, width=2, border_radius=5)

        tr = self._font.get_rect(self.text)
        tx = r.x + 8
        ty = r.centery - tr.height // 2
        self._font.render_to(surface, (tx, ty), self.text, INPUT_TEXT)

        if self.active and self._cursor_visible:
            cx = tx + tr.width + 2
            pygame.draw.line(surface, INPUT_CURSOR,
                             (cx, r.y + 6), (cx, r.bottom - 6), width=2)

    def get_value(self) -> float | None:
        try:
            return float(self.text)
        except ValueError:
            return None
