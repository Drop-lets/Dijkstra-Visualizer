"""右侧信息面板 — 距离表、优先队列表、步骤描述"""

from __future__ import annotations
import pygame
from views.widgets import Panel, Table, Label
from algorithms.step_data import DijkstraStep
from config import (
    INFO_X, INFO_Y, INFO_W, INFO_H,
    BTN_TEXT,
    INF,
)

DIST_PANEL_H = 210
PQ_PANEL_H = 210
DESC_PANEL_H = 240
GAP = 8
PANEL_PAD_X = 4
PANEL_PAD_Y = 4


class InfoPanel:
    """右侧面板，展示算法运行时的状态信息"""

    _RESET_TEXT = "请在左侧工具栏加载样例图\n或手动编辑图，然后运行算法。"

    def __init__(self):
        px, py = INFO_X + PANEL_PAD_X, INFO_Y + PANEL_PAD_Y
        pw = INFO_W - PANEL_PAD_X * 2

        # 距离表面板
        self.dist_table = Table(
            pygame.Rect(px + 4, py + 28, pw - 8, DIST_PANEL_H - 36),
            headers=["顶点", "距离"],
        )
        self.dist_panel = Panel(
            pygame.Rect(px, py, pw, DIST_PANEL_H),
            title="📊 距离表",
        )
        py += DIST_PANEL_H + GAP

        # 优先队列面板
        self.pq_table = Table(
            pygame.Rect(px + 4, py + 28, pw - 8, PQ_PANEL_H - 36),
            headers=["距离", "顶点"],
        )
        self.pq_panel = Panel(
            pygame.Rect(px, py, pw, PQ_PANEL_H),
            title="📋 优先队列",
        )
        py += PQ_PANEL_H + GAP

        # 步骤描述面板
        self.desc_label = Label(
            pygame.Rect(px + 8, py + 30, pw - 16, DESC_PANEL_H - 40),
            text=self._RESET_TEXT,
            font_size=12,
            color=BTN_TEXT,
        )
        self.desc_panel = Panel(
            pygame.Rect(px, py, pw, DESC_PANEL_H),
            title="📝 步骤详情",
        )
        py += DESC_PANEL_H + GAP
        self._last_step_index = -1

        # 状态标签
        self.status_label = Label(
            pygame.Rect(px, INFO_Y + INFO_H - 32, pw, 28),
            text="编辑模式",
            font_size=12,
            color=(130, 135, 145),
            align="center",
            bg_color=(243, 244, 246),
        )

    def update_from_step(self, step: DijkstraStep | None, source_id: str | None = None, target_id: str | None = None):
        if step is None:
            self.dist_table.set_data(["顶点", "距离"], [])
            self.pq_table.set_data(["距离", "顶点"], [])
            self.desc_label.set_text(self._RESET_TEXT)
            self._last_step_index = -1
            return

        # 距离表
        dist_rows = []
        for vid, dist in sorted(step.distances.items(), key=lambda kv: kv[1]):
            dist_str = "∞" if dist == INF else (
                str(int(dist)) if dist == int(dist) else f"{dist:.1f}"
            )
            dist_rows.append([vid, dist_str])
        self.dist_table.set_data(["顶点", "距离"], dist_rows)
        self.dist_table.clear_highlights()
        if step.current_vertex_id:
            for i, row in enumerate(dist_rows):
                if row[0] == step.current_vertex_id:
                    self.dist_table.add_highlight(i)
                    break

        # 优先队列表
        pq_rows = []
        for dist, vid in step.pq_state:
            ds = "∞" if dist == INF else (
                str(int(dist)) if dist == int(dist) else f"{dist:.1f}"
            )
            pq_rows.append([ds, vid])
        self.pq_table.set_data(["距离", "顶点"], pq_rows)

        # 步骤描述 — 累积历史，新步骤在最上面
        # 仅在算法正向推进时追加新步骤；步退时 step_index 减小，不重复追加
        if step.step_index > self._last_step_index:
            self._last_step_index = step.step_index
            prefix = f"[{step.step_index}] "
            new_text = prefix + step.message
            current = self.desc_label.text
            if current and current != self._RESET_TEXT:
                self.desc_label.set_text(new_text + "\n" + current)
            else:
                self.desc_label.set_text(new_text)

    def set_status(self, text: str):
        self.status_label.set_text(text)

    def handle_event(self, event: pygame.event.Event) -> bool:
        """处理滚动事件，返回 True 表示已消费"""
        if self.dist_table.handle_event(event):
            return True
        if self.pq_table.handle_event(event):
            return True
        if self.desc_label.handle_event(event):
            return True
        return False

    def draw(self, surface: pygame.Surface):
        self.dist_panel.draw(surface)
        self.dist_table.draw(surface)
        self.pq_panel.draw(surface)
        self.pq_table.draw(surface)
        self.desc_panel.draw(surface)
        self.desc_label.draw(surface)
        self.status_label.draw(surface)
