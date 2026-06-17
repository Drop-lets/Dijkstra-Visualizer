"""算法控制器 — Dijkstra 生成器的执行管理"""

from __future__ import annotations
from models.graph import Graph
from algorithms.dijkstra import DijkstraIterator
from algorithms.step_data import DijkstraStep
from config import AUTO_STEP_MS


class AlgoController:
    """管理 Dijkstra 算法的执行状态：播放/暂停/步进/重置"""

    def __init__(self):
        self._iterator: DijkstraIterator | None = None
        self._generator = None
        self.step_history: list[DijkstraStep] = []
        self.current_index: int = -1  # -1 表示尚未开始
        self.is_playing: bool = False
        self.is_complete: bool = False
        self._auto_timer: int = 0
        self.source_id: str | None = None
        self.target_id: str | None = None

    def start(self, graph: Graph, source_id: str, target_id: str | None = None):
        """初始化并启动算法，获取第一个步骤 (init)"""
        self.source_id = source_id
        self.target_id = target_id
        self._iterator = DijkstraIterator(graph, source_id, target_id)
        self._generator = self._iterator.run()
        self.step_history.clear()
        self.current_index = -1
        self.is_playing = False
        self.is_complete = False
        self._auto_timer = 0
        # 立即执行第一步
        self.step_forward()

    def step_forward(self) -> DijkstraStep | None:
        """向前一步，返回新的步骤或 None（已结束）"""
        if self.is_complete or self._generator is None:
            return None
        try:
            step = next(self._generator)
            self.step_history.append(step)
            self.current_index += 1
            if step.step_type == "complete":
                self.is_complete = True
                self.is_playing = False
            return step
        except StopIteration:
            self.is_complete = True
            self.is_playing = False
            return None

    def step_backward(self) -> DijkstraStep | None:
        """向后一步（从历史记录回退）"""
        if self.current_index <= 0:
            return None
        self.current_index -= 1
        self.is_complete = False
        return self.current_step

    def toggle_play(self):
        """切换播放/暂停"""
        if self.is_complete:
            return
        self.is_playing = not self.is_playing

    def reset(self):
        """完全重置"""
        self._iterator = None
        self._generator = None
        self.step_history.clear()
        self.current_index = -1
        self.is_playing = False
        self.is_complete = False
        self._auto_timer = 0
        self.source_id = None
        self.target_id = None

    def update(self, dt_ms: int):
        """每帧更新：处理自动播放计时"""
        if not self.is_playing or self.is_complete:
            return
        self._auto_timer += dt_ms
        while self._auto_timer >= AUTO_STEP_MS and self.is_playing:
            self._auto_timer -= AUTO_STEP_MS
            self.step_forward()

    @property
    def current_step(self) -> DijkstraStep | None:
        """当前步骤"""
        if 0 <= self.current_index < len(self.step_history):
            return self.step_history[self.current_index]
        return None

    @property
    def progress_text(self) -> str:
        """进度文本"""
        if self.is_complete:
            return "✅ 算法完成"
        elif self.is_playing:
            return f"▶ 自动播放中... (第 {self.current_index + 1} 步)"
        elif self.current_index >= 0:
            return f"⏸ 暂停 (第 {self.current_index + 1} 步)"
        return ""
