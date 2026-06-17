"""Dijkstra 算法单步数据"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class DijkstraStep:
    """Dijkstra 算法执行过程中的一个不可变快照"""

    step_index: int
    step_type: str  # init | pop | relax_start | relax_update | relax_check | complete
    message: str

    current_vertex_id: str | None = None
    visited: tuple[str, ...] = ()
    distances: dict[str, float] = field(default_factory=dict)
    predecessors: dict[str, str | None] = field(default_factory=dict)

    # 优先队列快照（(distance, vertex_id) 的有序元组）
    pq_state: tuple[tuple[float, str], ...] = ()

    # 松弛详情（仅 relax_* 步有效）
    relaxing_edge: tuple[str, str] | None = None
    relaxation_result: str | None = None  # 'updated' | 'unchanged'
    old_distance: float | None = None
    new_distance: float | None = None

    # 最终路径（仅 complete 步有效）
    final_path: tuple[str, ...] | None = None
