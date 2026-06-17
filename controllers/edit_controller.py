"""图编辑控制器 — 处理画布区域的鼠标/键盘事件（视口感知）"""

from __future__ import annotations
from enum import IntEnum
from models.graph import Graph
from models.vertex import Vertex
from config import WEIGHT_OFFSET


class EditMode(IntEnum):
    MOVE = 0
    ADD_VERTEX = 1
    ADD_EDGE = 2
    DELETE = 3


class EditController:
    """管理图的增删改交互，支持视口坐标转换"""

    def __init__(self, graph: Graph, graph_view):
        self.graph = graph
        self.view = graph_view
        self.mode = EditMode.MOVE
        self.drag_vertex_id: str | None = None
        self.drag_offset_wx = 0.0
        self.drag_offset_wy = 0.0
        self.edge_source_id: str | None = None
        self.hovered_vertex_id: str | None = None
        self.is_dragging_vertex = False
        # 视口平移
        self.is_panning = False
        self.pan_start_x = 0
        self.pan_start_y = 0
        self.pan_start_pan_x = 0.0
        self.pan_start_pan_y = 0.0

    def set_mode(self, mode: EditMode):
        """切换编辑模式"""
        self.mode = mode
        self.edge_source_id = None
        self.drag_vertex_id = None
        self.is_dragging_vertex = False

    # ---- 事件处理 ----

    def handle_mouse_down(self, screen_pos: tuple[int, int], button: int) -> str | None:
        """
        处理鼠标按下。screen_pos 为屏幕绝对坐标。
        button: 1=左键, 2=中键, 3=右键
        返回操作描述或 None。
        """
        if not self.view.is_in_canvas(*screen_pos):
            return None

        local = self.view.canvas_to_local(*screen_pos)
        wx, wy = self.view.screen_to_world(*local)

        # 右键：优先检测权重标签点击，否则平移视口
        if button == 2 or (button == 3 and self.mode == EditMode.MOVE):
            if button == 3:
                edge_key = self.graph.edge_weight_at_xy(wx, wy, WEIGHT_OFFSET / self.view.scale)
                if edge_key:
                    return f"right_click_weight:{edge_key[0]}:{edge_key[1]}"
            # 未命中权重 → 平移
            self.is_panning = True
            self.pan_start_x = screen_pos[0]
            self.pan_start_y = screen_pos[1]
            self.pan_start_pan_x = self.view.pan_x
            self.pan_start_pan_y = self.view.pan_y
            return None

        if button != 1:
            return None

        hit_v = self.graph.vertex_at_xy(wx, wy)
        if self.mode == EditMode.MOVE:
            if hit_v:
                self.drag_vertex_id = hit_v.id
                self.drag_offset_wx = hit_v.x - wx
                self.drag_offset_wy = hit_v.y - wy
                self.is_dragging_vertex = True
                return f"拖拽顶点 {hit_v.label}"

        elif self.mode == EditMode.ADD_VERTEX:
            if hit_v is None:
                vid = self.graph.add_vertex(wx, wy)
                return f"添加顶点 {self.graph.vertices[vid].label}"

        elif self.mode == EditMode.ADD_EDGE:
            if hit_v:
                if self.edge_source_id is None:
                    self.edge_source_id = hit_v.id
                    return f"已选起点 {hit_v.label}，请点击终点"
                elif hit_v.id != self.edge_source_id:
                    ok = self.graph.add_edge(self.edge_source_id, hit_v.id, 1.0)
                    src_label = self.graph.vertices[self.edge_source_id].label
                    self.edge_source_id = None
                    if ok:
                        return f"添加边 {src_label} → {hit_v.label}"
                else:
                    self.edge_source_id = None
            else:
                self.edge_source_id = None

        elif self.mode == EditMode.DELETE:
            if hit_v:
                label = hit_v.label
                self.graph.remove_vertex(hit_v.id)
                return f"删除顶点 {label} 及其关联边"
            else:
                edge_key = self.graph.edge_weight_at_xy(wx, wy, WEIGHT_OFFSET / self.view.scale)
                if edge_key:
                    self.graph.remove_edge(*edge_key)
                    return f"删除边 {edge_key[0]} → {edge_key[1]}"

        return None

    def handle_mouse_up(self, screen_pos: tuple[int, int], button: int):
        """处理鼠标释放"""
        if button == 2 or (button == 3 and self.is_panning):
            self.is_panning = False
        self.drag_vertex_id = None
        self.is_dragging_vertex = False

    def handle_mouse_motion(self, screen_pos: tuple[int, int]):
        """处理鼠标移动"""
        # 视口平移
        if self.is_panning:
            dx = screen_pos[0] - self.pan_start_x
            dy = screen_pos[1] - self.pan_start_y
            self.view.pan_x = self.pan_start_pan_x - dx / self.view.scale
            self.view.pan_y = self.pan_start_pan_y - dy / self.view.scale
            return

        if not self.view.is_in_canvas(*screen_pos):
            self.hovered_vertex_id = None
            return

        local = self.view.canvas_to_local(*screen_pos)
        wx, wy = self.view.screen_to_world(*local)

        # 拖拽顶点
        if self.is_dragging_vertex and self.drag_vertex_id:
            self.graph.move_vertex(
                self.drag_vertex_id,
                wx + self.drag_offset_wx,
                wy + self.drag_offset_wy,
            )

        # 悬停检测
        hit_v = self.graph.vertex_at_xy(wx, wy)
        self.hovered_vertex_id = hit_v.id if hit_v else None

    def handle_right_click_weight(self, screen_pos: tuple[int, int]) -> tuple[str, str] | None:
        """处理右键点击权重标签。返回 (src, tgt) 或 None。"""
        if not self.view.is_in_canvas(*screen_pos):
            return None
        local = self.view.canvas_to_local(*screen_pos)
        wx, wy = self.view.screen_to_world(*local)
        return self.graph.edge_weight_at_xy(wx, wy, WEIGHT_OFFSET / self.view.scale)

    def handle_key_down(self, key: int) -> str | None:
        if key == 27:  # Escape
            self.edge_source_id = None
            return "取消当前操作"
        return None

    @property
    def state_dict(self) -> dict:
        return {
            "hovered_vertex_id": self.hovered_vertex_id,
            "drag_vertex_id": self.drag_vertex_id,
            "is_dragging": self.is_dragging_vertex,
        }
