"""主控器 — 状态机 + 事件路由 + 模块协调"""

from __future__ import annotations
import pygame

from models.graph import Graph
from algorithms.dijkstra import DijkstraIterator
from controllers.edit_controller import EditController, EditMode
from controllers.algo_controller import AlgoController
from views.graph_view import GraphView
from views.toolbar import Toolbar, AppState
from views.info_panel import InfoPanel
from views.widgets import TextInput
from presets.sample_graph import create_random_graph
from config import (
    SCREEN_W, SCREEN_H, TITLE_H,
    TITLE_BG, TITLE_TEXT,
    BG_COLOR, PANEL_BG, STATUS_BG,
    CANVAS_X, CANVAS_Y, CANVAS_W, CANVAS_H,
    FONT_FAMILY, FONT_FALLBACK, TITLE_FONT_SIZE, STATUS_SIZE,
    STATUS_H,
)


def _make_font(size: int, bold: bool = False) -> pygame.font.Font:
    for family in (FONT_FAMILY, FONT_FALLBACK):
        try:
            return pygame.font.SysFont(family, size, bold=bold)
        except Exception:
            continue
    return pygame.font.Font(None, size)


class AppController:
    """顶层应用控制器"""

    def __init__(self):
        self.graph = Graph()
        self.graph_view = GraphView()
        self.edit_controller = EditController(self.graph, self.graph_view)
        self.algo_controller = AlgoController()
        self.toolbar = Toolbar()
        self.info_panel = InfoPanel()

        self.app_state = AppState.EDIT
        self.source_id: str | None = None
        self.target_id: str | None = None
        self._expecting_target = False  # 是否处于「等待选择终点」状态
        self.status_msg = "编辑模式 — 点击左侧按钮编辑图，或加载样例图"
        self._sub_status = ""

        self.weight_input: TextInput | None = None
        self._weight_edit_edge: tuple[str, str] | None = None
        self._weight_input_visible = False

        self._title_font = _make_font(TITLE_FONT_SIZE, bold=True)
        self._status_font = _make_font(STATUS_SIZE)

    # ============================================================
    # 事件路由
    # ============================================================

    def handle_event(self, event: pygame.event.Event):
        if self._weight_input_visible and self.weight_input:
            if event.type == pygame.KEYDOWN:
                self.weight_input.handle_event(event)
                if self.weight_input.return_pressed:
                    self._confirm_weight_edit()
                    return
                elif self.weight_input.cancelled:
                    self._cancel_weight_edit()
                    return
            return

        result = self.toolbar.handle_event(event)
        if result:
            self._handle_toolbar_action(result)
            return

        # 右侧信息面板的滚动事件
        if self.info_panel.handle_event(event):
            return

        if event.type == pygame.KEYDOWN:
            self._handle_key(event.key)
            return

        if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION):
            self._handle_canvas_mouse(event)

    def _handle_toolbar_action(self, result: dict):
        action = result.get("action")
        if action == "set_mode":
            self.edit_controller.set_mode(EditMode(result["mode"]))
            mode_names = ["移动/平移", "添加顶点", "添加边", "删除"]
            self.status_msg = f"编辑模式：{mode_names[result['mode']]}"
        elif action == "set_source":
            # 允许重新设置起点：清空之前的起终点
            self.source_id = None
            self.target_id = None
            self._expecting_target = False
            self._sub_status = "请点击图中一个顶点设为起点"
            self.app_state = AppState.ALGO_SETUP
            self.status_msg = "请在画布上点击一个顶点作为起点"
            self._refresh_toolbar()
        elif action == "set_target" and self.source_id:
            self._expecting_target = True
            self._sub_status = "请点击图中一个顶点设为终点"
            self.status_msg = "请在画布上点击另一个顶点作为终点"
            self._refresh_toolbar()
        elif action == "run":
            self._start_algorithm()
        elif action == "play_pause":
            self.algo_controller.toggle_play()
        elif action == "step":
            self._do_step()
        elif action == "reset":
            self._reset()
        elif action == "load_sample":
            self._load_sample()
        elif action == "clear":
            self._clear_graph()

    def _handle_key(self, key: int):
        if self._weight_input_visible:
            return
        if key == pygame.K_SPACE and self.app_state == AppState.ALGO_RUNNING:
            self.algo_controller.toggle_play()
        elif key == pygame.K_RIGHT and self.app_state == AppState.ALGO_RUNNING:
            self._do_step()
        elif key == pygame.K_LEFT and self.app_state == AppState.ALGO_RUNNING:
            self.algo_controller.step_backward()
        elif key == pygame.K_r and self.app_state in (AppState.ALGO_RUNNING, AppState.ALGO_COMPLETED):
            self._reset()
        elif key == pygame.K_ESCAPE:
            if self.app_state == AppState.ALGO_SETUP:
                self._reset()
            else:
                self.edit_controller.handle_key_down(key)

    def _handle_canvas_mouse(self, event: pygame.event.Event):
        if not self.graph_view.is_in_canvas(event.pos[0], event.pos[1]):
            return

        if self.app_state == AppState.ALGO_SETUP:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._handle_setup_click(event.pos)
            return

        if self.app_state != AppState.EDIT:
            return

        if event.type == pygame.MOUSEBUTTONDOWN:
            msg = self.edit_controller.handle_mouse_down(event.pos, event.button)
            if msg:
                if msg.startswith("right_click_weight:"):
                    parts = msg.split(":")
                    src, tgt = parts[1], parts[2]
                    self._start_weight_edit(src, tgt, event.pos)
                else:
                    self.status_msg = msg
        elif event.type == pygame.MOUSEBUTTONUP:
            self.edit_controller.handle_mouse_up(event.pos, event.button)
        elif event.type == pygame.MOUSEMOTION:
            self.edit_controller.handle_mouse_motion(event.pos)

    def _handle_setup_click(self, screen_pos: tuple[int, int]):
        local = self.graph_view.canvas_to_local(*screen_pos)
        wx, wy = self.graph_view.screen_to_world(*local)
        hit = self.graph.vertex_at_xy(wx, wy)
        if hit is None:
            self.status_msg = "⚠ 未点击到顶点，请重试"
            return

        if self.source_id is None:
            self.source_id = hit.id
            vlabel = self.graph.vertices[hit.id].label
            self.status_msg = f"起点设为 {vlabel} — 请点击「设置终点」选择终点，或直接点击「运行」"
        elif self._expecting_target and hit.id != self.source_id:
            self.target_id = hit.id
            self._expecting_target = False
            vlabel = self.graph.vertices[hit.id].label
            self.status_msg = f"终点设为 {vlabel} — 点击「运行 Dijkstra」开始算法"
        elif not self._expecting_target:
            self.status_msg = "请先点击「设置终点」按钮，再选择终点；或点击「设置起点」重新选择起点"
        else:
            self.status_msg = "⚠ 终点不能与起点相同，请选择其他顶点"
            return

        self._refresh_toolbar()

    # ============================================================
    # 权重编辑
    # ============================================================

    def _start_weight_edit(self, src: str, tgt: str, screen_pos: tuple[int, int]):
        edge = self.graph.get_edge(src, tgt)
        if not edge:
            return
        self._weight_edit_edge = (src, tgt)
        w, h = 110, 34
        x = min(max(screen_pos[0] - w // 2, 10), SCREEN_W - w - 10)
        y = min(max(screen_pos[1] - h // 2, 10), SCREEN_H - h - 10)
        self.weight_input = TextInput(pygame.Rect(x, y, w, h), initial_text=str(edge.weight))
        self._weight_input_visible = True
        self.status_msg = f"编辑权重 {src}→{tgt}：输入新值 → Enter 确认 | Esc 取消"

    def _confirm_weight_edit(self):
        if self._weight_edit_edge and self.weight_input:
            val = self.weight_input.get_value()
            if val is not None and val >= 0:
                src, tgt = self._weight_edit_edge
                self.graph.update_edge_weight(src, tgt, val)
                self.status_msg = f"权重已更新：{src}→{tgt} = {val}"
            else:
                self.status_msg = "⚠ 无效权重（请输入非负数字）"
        self._clear_weight_input()

    def _cancel_weight_edit(self):
        self.status_msg = "已取消权重编辑"
        self._clear_weight_input()

    def _clear_weight_input(self):
        self.weight_input = None
        self._weight_edit_edge = None
        self._weight_input_visible = False

    # ============================================================
    # 算法控制
    # ============================================================

    def _start_algorithm(self):
        if self.source_id is None:
            self.status_msg = "⚠ 请先设置起点！"
            return
        if self.source_id not in self.graph.vertices:
            self.status_msg = "⚠ 起点已被删除，请重新设置"
            self._reset()
            return
        err = DijkstraIterator.validate_graph(self.graph, self.source_id)
        if err:
            self.status_msg = f"❌ {err}"
            return

        self.algo_controller.start(self.graph, self.source_id, self.target_id)
        self.app_state = AppState.ALGO_RUNNING
        step = self.algo_controller.current_step
        if step:
            self.status_msg = step.message
        self._refresh_toolbar()

    def _do_step(self):
        if self.app_state != AppState.ALGO_RUNNING:
            return
        step = self.algo_controller.step_forward()
        if step:
            self.status_msg = step.message
            if self.algo_controller.is_complete:
                self.app_state = AppState.ALGO_COMPLETED
                self._refresh_toolbar()
        else:
            self.app_state = AppState.ALGO_COMPLETED
            self._refresh_toolbar()

    def _reset(self):
        self.algo_controller.reset()
        self.app_state = AppState.EDIT
        self.source_id = None
        self.target_id = None
        self._expecting_target = False
        self.status_msg = "编辑模式 — 点击左侧按钮编辑图，或加载样例图"
        self._sub_status = ""
        self.edit_controller.set_mode(EditMode.MOVE)
        self.toolbar.mode_group.activate(0)
        self._refresh_toolbar()
        self.graph_view.fit_view(self.graph)

    def _load_sample(self):
        self.graph = create_random_graph()
        self.edit_controller.graph = self.graph
        self.algo_controller.reset()
        self.source_id = None
        self.target_id = None
        self.app_state = AppState.EDIT
        self.graph_view.fit_view(self.graph)
        self.status_msg = f"已随机生成图（{self.graph.vertex_count()} 顶点, {self.graph.edge_count()} 边）"
        self._refresh_toolbar()

    def _clear_graph(self):
        self.graph.clear()
        self.algo_controller.reset()
        self.source_id = None
        self.target_id = None
        self.app_state = AppState.EDIT
        self.graph_view.pan_x = 0.0
        self.graph_view.pan_y = 0.0
        self.graph_view.scale = 1.0
        self.status_msg = "画布已清空，从空白图开始编辑"
        self._refresh_toolbar()

    def _refresh_toolbar(self):
        self.toolbar.update_for_state(
            self.app_state, self.algo_controller.is_playing,
            self.source_id is not None, self.target_id is not None,
        )

    # ============================================================
    # 每帧更新
    # ============================================================

    def update(self, dt_ms: int):
        if self.app_state == AppState.ALGO_RUNNING:
            self.algo_controller.update(dt_ms)
            step = self.algo_controller.current_step
            if step:
                self.status_msg = step.message
            if self.algo_controller.is_complete and self.app_state != AppState.ALGO_COMPLETED:
                self.app_state = AppState.ALGO_COMPLETED
                self._refresh_toolbar()

        if self._weight_input_visible and self.weight_input:
            self.weight_input.update(dt_ms)

    # ============================================================
    # 渲染
    # ============================================================

    def draw(self, screen: pygame.Surface):
        screen.fill(BG_COLOR)

        # ---- 标题栏 ----
        title_rect = pygame.Rect(0, 0, SCREEN_W, TITLE_H)
        pygame.draw.rect(screen, TITLE_BG, title_rect)
        title_surf = self._title_font.render(
            "Dijkstra最短路径算法演示", True, TITLE_TEXT
        )
        screen.blit(title_surf, (16, (TITLE_H - title_surf.get_height()) // 2))

        # ---- 画布 ----
        canvas_rect = pygame.Rect(CANVAS_X, CANVAS_Y, CANVAS_W, CANVAS_H)
        canvas_surface = screen.subsurface(canvas_rect)

        step = self.algo_controller.current_step
        self.graph_view.draw(
            canvas_surface, self.graph, step=step,
            edit_state=self.edit_controller.state_dict,
            source_id=self.source_id, target_id=self.target_id,
            edge_source_id=self.edit_controller.edge_source_id,
            selected_edge=self._weight_edit_edge if self._weight_input_visible else None,
        )

        # ---- 画布底部状态栏 ----
        status_y = CANVAS_Y + CANVAS_H
        status_rect = pygame.Rect(CANVAS_X, status_y, CANVAS_W, STATUS_H)
        pygame.draw.rect(screen, STATUS_BG, status_rect)
        # 细顶线
        pygame.draw.line(screen, (209, 213, 219), (CANVAS_X, status_y),
                         (CANVAS_X + CANVAS_W, status_y))

        status = self.status_msg
        if self.algo_controller.is_playing:
            status = f"▶ {status}"
        elif self.app_state == AppState.ALGO_RUNNING:
            status = f"⏸ 暂停中 — {status}"
        status_surf = self._status_font.render(status, True, (107, 114, 128))
        screen.blit(status_surf, (CANVAS_X + 12, status_y + (STATUS_H - status_surf.get_height()) // 2))

        # ---- 工具栏 ----
        self._refresh_toolbar()
        self.toolbar.draw(screen)

        # ---- 信息面板 ----
        self.info_panel.update_from_step(step, self.source_id, self.target_id)
        self.info_panel.set_status(status)
        self.info_panel.draw(screen)

        # ---- 权重编辑浮层 ----
        if self._weight_input_visible and self.weight_input:
            self.weight_input.draw(screen)

        pygame.display.flip()
