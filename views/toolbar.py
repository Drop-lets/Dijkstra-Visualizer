"""左侧工具栏 — 编辑模式 + 算法控制按钮"""

from __future__ import annotations
import pygame
import pygame.freetype
from enum import IntEnum
from views.widgets import Button, ToggleGroup, Label, Panel
from config import (
    TOOLBAR_W, TOOLBAR_X, TOOLBAR_Y, TOOLBAR_H,
    SEPARATOR_COLOR, SECTION_FONT_SIZE, FONT_FAMILY, FONT_FALLBACK,
)


def _make_section_font():
    for family in (FONT_FAMILY, FONT_FALLBACK):
        try:
            return pygame.freetype.SysFont(family, SECTION_FONT_SIZE)
        except Exception:
            continue
    return pygame.freetype.Font(None, SECTION_FONT_SIZE)


class AppState(IntEnum):
    EDIT = 0
    ALGO_SETUP = 1
    ALGO_RUNNING = 2
    ALGO_COMPLETED = 3


class Toolbar:
    """左侧工具栏面板"""

    def __init__(self):
        self.panel = Panel(
            pygame.Rect(TOOLBAR_X, TOOLBAR_Y, TOOLBAR_W, TOOLBAR_H),
            title="控制面板",
        )
        self._section_font = _make_section_font()

        btn_w = TOOLBAR_W - 28
        btn_h = 32
        x0 = TOOLBAR_X + 14
        y = TOOLBAR_Y + 40
        self._separator_ys = []
        self._x0 = x0
        self._btn_w = btn_w

        # ---- 编辑模式 ----
        self._draw_section_title(None, x0, y, "✏️ 编辑模式", btn_w)
        y += 20
        mode_btns = []
        for text in ["🖐 移动 / 平移", "➕ 添加顶点", "🔗 添加边", "🗑 删除"]:
            mode_btns.append(Button(pygame.Rect(x0, y, btn_w, btn_h), text, is_toggle=True))
            y += 38
        self.mode_group = ToggleGroup(mode_btns)
        self.mode_group.activate(0)
        y += 8

        # ---- 算法控制 ----
        self._separator_ys.append(y)
        y += 8
        self._draw_section_title(None, x0, y, "⚡ 算法控制", btn_w)
        y += 20

        self.btn_source = Button(pygame.Rect(x0, y, btn_w, btn_h), "📍 设置起点")
        y += 42
        self.btn_target = Button(pygame.Rect(x0, y, btn_w, btn_h), "🎯 设置终点", enabled=False)
        y += 42
        self.btn_run = Button(pygame.Rect(x0, y, btn_w, btn_h), "▶ 运行 Dijkstra", enabled=False)
        y += 42
        self.btn_play = Button(pygame.Rect(x0, y, btn_w, btn_h), "▶ 自动播放", enabled=False)
        y += 42
        self.btn_step = Button(pygame.Rect(x0, y, btn_w, btn_h), "⏭ 单步步进", enabled=False)
        y += 42
        self.btn_reset = Button(pygame.Rect(x0, y, btn_w, btn_h), "🔄 重置", enabled=False)
        y += 42

        # ---- 预设 ----
        self._separator_ys.append(y)
        y += 8
        self._draw_section_title(None, x0, y, "📦 图预设", btn_w)
        y += 20

        self.btn_sample = Button(pygame.Rect(x0, y, btn_w, btn_h), "🎲 随机生成")
        y += 42
        self.btn_clear = Button(pygame.Rect(x0, y, btn_w, btn_h), "🗑 清空画布")

        self._all_buttons = [
            self.btn_source, self.btn_target, self.btn_run,
            self.btn_play, self.btn_step, self.btn_reset,
            self.btn_sample, self.btn_clear,
        ]

    def _draw_section_title(self, _surface, x, y, text, width):
        """仅用于定位 — 实际绘制在 draw() 中通过 section_labels 完成"""
        pass

    def handle_event(self, event: pygame.event.Event) -> dict | None:
        idx = self.mode_group.handle_event(event)
        if idx >= 0:
            return {"action": "set_mode", "mode": idx}

        actions = [
            (self.btn_source, "set_source"),
            (self.btn_target, "set_target"),
            (self.btn_run, "run"),
            (self.btn_play, "play_pause"),
            (self.btn_step, "step"),
            (self.btn_reset, "reset"),
            (self.btn_sample, "load_sample"),
            (self.btn_clear, "clear"),
        ]
        for btn, action in actions:
            if btn.handle_event(event):
                return {"action": action}
        return None

    def update_for_state(self, app_state: AppState, is_playing: bool,
                         source_set: bool, target_set: bool):
        is_edit = app_state == AppState.EDIT
        is_setup = app_state == AppState.ALGO_SETUP
        is_running = app_state == AppState.ALGO_RUNNING
        is_done = app_state == AppState.ALGO_COMPLETED

        for b in self.mode_group.buttons:
            b.enabled = is_edit

        self.btn_source.enabled = is_edit or is_setup
        self.btn_target.enabled = source_set and (is_edit or is_setup)
        self.btn_run.enabled = source_set and (is_edit or is_setup)
        self.btn_play.enabled = is_running
        self.btn_step.enabled = is_running
        self.btn_reset.enabled = is_running or is_done
        self.btn_sample.enabled = is_edit or is_setup
        self.btn_clear.enabled = is_edit or is_setup

        self.btn_play.text = "⏸ 暂停" if is_playing else "▶ 自动播放"

    def draw(self, surface: pygame.Surface):
        self.panel.draw(surface)

        # 绘制小节标题
        titles = [
            (self.mode_group.buttons[0].rect.y - 22, "✏️ 编辑模式"),
            (self.btn_source.rect.y - 22, "⚡ 算法控制"),
            (self.btn_sample.rect.y - 22, "📦 图预设"),
        ]
        for sec_y, sec_text in titles:
            self._section_font.render_to(surface, (self._x0, sec_y), sec_text, (107, 114, 128))

        # 分隔线
        for sep_y in self._separator_ys:
            pygame.draw.line(surface, SEPARATOR_COLOR,
                             (self._x0, sep_y), (self._x0 + self._btn_w, sep_y))

        self.mode_group.draw(surface)
        for btn in self._all_buttons:
            btn.draw(surface)

    @property
    def active_mode(self) -> int:
        return self.mode_group.active_index
