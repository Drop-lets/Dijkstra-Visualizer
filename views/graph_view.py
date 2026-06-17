"""图渲染 — 高质量抗锯齿绘制：顶点、边、箭头、权重标签及算法状态叠层"""

from __future__ import annotations
import math
import pygame
import pygame.gfxdraw
from models.graph import Graph
from algorithms.step_data import DijkstraStep
from config import (
    CANVAS_BG,
    VERTEX_DEFAULT, VERTEX_CURRENT, VERTEX_VISITED,
    VERTEX_SOURCE, VERTEX_TARGET, VERTEX_PATH,
    VERTEX_LABEL, VERTEX_R, VERTEX_RING_W,
    RING_CURRENT, RING_SOURCE, RING_TARGET, RING_EDGE_SRC,
    EDGE_DEFAULT, EDGE_RELAXING, EDGE_PATH,
    EDGE_WEIGHT_BG, EDGE_WEIGHT_TEXT,
    EDGE_WIDTH, EDGE_HIGHLIGHT_W, ARROW_SIZE,
    WEIGHT_OFFSET, WEIGHT_FONT_SIZE,
    FONT_FAMILY, FONT_FALLBACK,
    CANVAS_X, CANVAS_Y, CANVAS_W, CANVAS_H,
)
import pygame.freetype


class GraphView:
    """绘制图及其算法状态的渲染器，使用 gfxdraw 抗锯齿"""

    def __init__(self):
        self._font_cache: dict[tuple[int, bool], pygame.freetype.Font] = {}  # (size, bold) → font
        self.pan_x = 0.0
        self.pan_y = 0.0
        self.scale = 1.0

    def _get_font(self, size: int, bold: bool = False) -> pygame.freetype.Font:
        """获取指定大小和粗细的字体（带缓存）"""
        key = (size, bold)
        font = self._font_cache.get(key)
        if font is None:
            for family in (FONT_FAMILY, FONT_FALLBACK):
                try:
                    font = pygame.freetype.SysFont(family, size, bold=bold)
                    break
                except Exception:
                    continue
            if font is None:
                font = pygame.freetype.Font(None, size)
            self._font_cache[key] = font
        return font

    def _ensure_fonts(self):
        """预创建常用字号字体（首次 draw 时调用）"""
        if not self._font_cache:
            self._get_font(int(WEIGHT_FONT_SIZE))  # 预热

    # ---- 坐标转换 ----

    def world_to_screen(self, wx: float, wy: float) -> tuple[float, float]:
        return ((wx - self.pan_x) * self.scale, (wy - self.pan_y) * self.scale)

    def screen_to_world(self, sx: float, sy: float) -> tuple[float, float]:
        return (sx / self.scale + self.pan_x, sy / self.scale + self.pan_y)

    def scaled_vertex_r(self) -> float:
        return max(6, VERTEX_R * self.scale)

    def fit_view(self, graph: Graph):
        if graph.vertex_count() == 0:
            self.pan_x = 0.0
            self.pan_y = 0.0
            self.scale = 1.0
            return
        xs = [v.x for v in graph.vertices.values()]
        ys = [v.y for v in graph.vertices.values()]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        margin = 60
        graph_w = max_x - min_x + 2 * margin
        graph_h = max_y - min_y + 2 * margin
        self.scale = max(0.1, min(CANVAS_W / graph_w, CANVAS_H / graph_h, 1.0))
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2
        self.pan_x = center_x - CANVAS_W / (2 * self.scale)
        self.pan_y = center_y - CANVAS_H / (2 * self.scale)

    # ---- 主绘制入口 ----

    def draw(
        self, surface: pygame.Surface, graph: Graph,
        step: DijkstraStep | None = None,
        edit_state: dict | None = None,
        source_id: str | None = None,
        target_id: str | None = None,
        edge_source_id: str | None = None,
        selected_edge: tuple[str, str] | None = None,
    ):
        self._ensure_fonts()
        surface.fill(CANVAS_BG)

        visited = set(step.visited) if step else set()
        current_vid = step.current_vertex_id if step and step.step_type == "pop" else None
        relaxing_edge = step.relaxing_edge if step else None
        final_path = set()
        final_path_v = set()
        if step and step.final_path:
            path = step.final_path
            final_path_v = set(path)
            for i in range(len(path) - 1):
                final_path.add((path[i], path[i + 1]))

        # ---- 边 ----
        for src_id, edges in graph.adj.items():
            src_v = graph.vertices.get(src_id)
            if not src_v:
                continue
            for edge in edges:
                tgt_v = graph.vertices.get(edge.target_id)
                if not tgt_v:
                    continue
                ek = (src_id, edge.target_id)
                bidir = graph.get_edge(edge.target_id, src_id) is not None

                if final_path and ek in final_path:
                    color, width = EDGE_PATH, EDGE_HIGHLIGHT_W
                elif relaxing_edge and ek == relaxing_edge:
                    color, width = EDGE_RELAXING, EDGE_HIGHLIGHT_W
                else:
                    color, width = EDGE_DEFAULT, EDGE_WIDTH

                sx1, sy1 = self.world_to_screen(src_v.x, src_v.y)
                sx2, sy2 = self.world_to_screen(tgt_v.x, tgt_v.y)
                self._draw_edge(surface, sx1, sy1, sx2, sy2, color, width)
                self._draw_weight_label(surface, edge, sx1, sy1, sx2, sy2, bidir,
                                        selected=selected_edge == ek)

        # ---- 顶点 ----
        r = self.scaled_vertex_r()
        for vid, v in graph.vertices.items():
            sx, sy = self.world_to_screen(v.x, v.y)

            if final_path_v and vid in final_path_v:
                fill_color, ring_color = VERTEX_PATH, RING_SOURCE
            elif vid == source_id:
                fill_color, ring_color = VERTEX_SOURCE, RING_SOURCE
            elif vid == target_id:
                fill_color, ring_color = VERTEX_TARGET, RING_TARGET
            elif vid == current_vid:
                fill_color, ring_color = VERTEX_DEFAULT, RING_CURRENT
            elif vid in visited:
                fill_color, ring_color = VERTEX_VISITED, None
            else:
                fill_color, ring_color = VERTEX_DEFAULT, None

            is_dragging = edit_state and edit_state.get("drag_vertex_id") == vid
            is_edge_src = vid == edge_source_id
            is_hovered = edit_state and edit_state.get("hovered_vertex_id") == vid
            self._draw_vertex(surface, sx, sy, r, v.label,
                              fill_color, ring_color,
                              dragging=is_dragging,
                              edge_src=is_edge_src,
                              hovered=is_hovered)

    # ================================================================
    # 抗锯齿绘制
    # ================================================================

    def _draw_edge(self, surface, sx1, sy1, sx2, sy2, color, width):
        dx, dy = sx2 - sx1, sy2 - sy1
        length = math.hypot(dx, dy)
        if length < 1:
            return
        ux, uy = dx / length, dy / length
        r = self.scaled_vertex_r()
        ix1 = int(sx1 + ux * r)
        iy1 = int(sy1 + uy * r)
        ix2 = int(sx2 - ux * r)
        iy2 = int(sy2 - uy * r)

        # 抗锯齿线段
        if width <= 1:
            pygame.gfxdraw.line(surface, ix1, iy1, ix2, iy2, color)
        else:
            # 粗线：先画主线再用 aaline 柔化
            pygame.draw.line(surface, color, (ix1, iy1), (ix2, iy2), width)
            # 抗锯齿边缘线
            pygame.gfxdraw.line(surface, ix1, iy1, ix2, iy2,
                                tuple(min(c + 30, 255) for c in color))

        # 抗锯齿箭头
        self._draw_arrow(surface, ix2, iy2, ux, uy, color)

    def _draw_arrow(self, surface, tip_x, tip_y, ux, uy, color):
        angle = math.atan2(uy, ux)
        arr_s = max(5, int(ARROW_SIZE * self.scale))
        a1 = angle + math.pi * 5 / 6
        a2 = angle - math.pi * 5 / 6
        pts = [
            (tip_x, tip_y),
            (int(tip_x + arr_s * math.cos(a1)), int(tip_y + arr_s * math.sin(a1))),
            (int(tip_x + arr_s * math.cos(a2)), int(tip_y + arr_s * math.sin(a2))),
        ]
        # 填充箭头
        pygame.gfxdraw.filled_polygon(surface, pts, color)
        pygame.gfxdraw.aapolygon(surface, pts, color)

    def _draw_weight_label(self, surface, edge, sx1, sy1, sx2, sy2, bidir, selected=False):
        offset = WEIGHT_OFFSET * self.scale
        lx, ly = edge.weight_label_position(sx1, sy1, sx2, sy2, offset, bidir)

        w = edge.weight
        text = str(int(w)) if w == int(w) else f"{w:.1f}"
        fs = max(9, int(WEIGHT_FONT_SIZE * self.scale))
        font = self._get_font(fs)

        text_rect = font.get_rect(text)
        text_rect.center = (lx, ly)
        bg_rect = text_rect.inflate(10, 6)
        bg_color = (255, 243, 205) if selected else EDGE_WEIGHT_BG

        pygame.draw.rect(surface, bg_color, bg_rect, border_radius=3)
        pygame.draw.rect(surface, EDGE_DEFAULT, bg_rect, width=1, border_radius=3)
        font.render_to(surface, (bg_rect.x + 5, bg_rect.centery - text_rect.height // 2), text, EDGE_WEIGHT_TEXT)

    def _draw_vertex(self, surface, sx, sy, r, label, fill, ring, **opts):
        ix, iy = int(sx), int(sy)
        ir = int(r)
        rr = ir + 2 if (opts.get("dragging") or opts.get("hovered")) else ir

        # 光环（抗锯齿圆环）
        if ring:
            ring_w = max(1, int(VERTEX_RING_W * self.scale))
            outer_r = rr + ring_w
            inner_r = rr - 2
            # 画两个填充圆来实现圆环效果
            pygame.gfxdraw.filled_circle(surface, ix, iy, outer_r, ring)
            pygame.gfxdraw.aacircle(surface, ix, iy, outer_r, ring)
            pygame.gfxdraw.filled_circle(surface, ix, iy, inner_r, (255, 255, 255, 0))
            # 用背景色重画内部
            pygame.gfxdraw.filled_circle(surface, ix, iy, inner_r,
                                         (CANVAS_BG[0], CANVAS_BG[1], CANVAS_BG[2]))

        if opts.get("edge_src"):
            pygame.gfxdraw.aacircle(surface, ix, iy, rr + 3, RING_EDGE_SRC)

        # 阴影
        if rr >= 6:
            pygame.gfxdraw.filled_circle(surface, ix + 1, iy + 1, rr, (200, 205, 215))
            pygame.gfxdraw.aacircle(surface, ix + 1, iy + 1, rr, (200, 205, 215))

        # 主体（抗锯齿填充圆 + 抗锯齿边）
        pygame.gfxdraw.filled_circle(surface, ix, iy, rr, fill)
        pygame.gfxdraw.aacircle(surface, ix, iy, rr, fill)

        # 柔和内边框
        border_color = tuple(max(c - 30, 0) for c in fill)
        pygame.gfxdraw.aacircle(surface, ix, iy, rr, border_color)

        # 顶部高光
        if rr >= 7:
            hl_color = tuple(min(c + 50, 255) for c in fill)
            hx = int(ix - rr * 0.25)
            hy = int(iy - rr * 0.3)
            hr = max(1, int(rr * 0.35))
            pygame.gfxdraw.filled_circle(surface, hx, hy, hr, hl_color)
            pygame.gfxdraw.aacircle(surface, hx, hy, hr, hl_color)

        # 标签（黑色加粗，淡色顶点上高可读性）
        fs = max(9, int(14 * self.scale))
        font = self._get_font(fs, bold=True)
        lr = font.get_rect(label)
        tx = ix - lr.width // 2
        ty = iy - lr.height // 2
        font.render_to(surface, (tx, ty), label, VERTEX_LABEL)

    # ---- 画布区域 ----

    def is_in_canvas(self, screen_x: int, screen_y: int) -> bool:
        return CANVAS_X <= screen_x < CANVAS_X + CANVAS_W and CANVAS_Y <= screen_y < CANVAS_Y + CANVAS_H

    def canvas_to_local(self, screen_x: int, screen_y: int) -> tuple[int, int]:
        return (screen_x - CANVAS_X, screen_y - CANVAS_Y)
