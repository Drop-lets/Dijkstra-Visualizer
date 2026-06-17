"""Dijkstra 最短路径算法 — 逐步生成器实现"""

from __future__ import annotations
import heapq
from models.graph import Graph
from algorithms.step_data import DijkstraStep
from config import INF


class DijkstraIterator:
    """Dijkstra 算法逐步执行器，使用 heapq + generator 模式"""

    def __init__(self, graph: Graph, source_id: str, target_id: str | None = None):
        self.graph = graph
        self.source_id = source_id
        self.target_id = target_id

        # 内部状态
        self._dist: dict[str, float] = {}
        self._pred: dict[str, str | None] = {}
        self._visited: set[str] = set()
        self._pq: list[tuple[float, str]] = []  # (distance, vertex_id)

    def run(self):
        """生成器：逐步 yield DijkstraStep"""
        from config import INF

        # 初始化距离
        for vid in self.graph.vertices:
            self._dist[vid] = INF
            self._pred[vid] = None
        self._dist[self.source_id] = 0.0
        heapq.heappush(self._pq, (0.0, self.source_id))

        step_count = 0

        # Step: init
        yield self._make_step(
            step_count, "init",
            f"初始化：起点 {self._vlabel(self.source_id)} 距离=0，其余=∞。",
        )
        step_count += 1

        while self._pq:
            dist_u, u = heapq.heappop(self._pq)
            if u in self._visited:
                continue
            self._visited.add(u)

            # Step: pop
            yield self._make_step(
                step_count, "pop",
                f"弹出顶点 {self._vlabel(u)}（dist={self._fmt_dist(dist_u)}），标记为已访问。",
                current_vertex_id=u,
            )
            step_count += 1

            # 提前终止：到达目标
            if self.target_id is not None and u == self.target_id:
                break

            # 松弛所有出边
            for edge in self.graph.get_out_edges(u):
                v = edge.target_id
                if v in self._visited:
                    continue
                old = self._dist[v]
                new = dist_u + edge.weight

                # Step: relax_start
                yield self._make_step(
                    step_count, "relax_start",
                    f"检查边 {self._vlabel(u)} → {self._vlabel(v)}（权重={edge.weight}）："
                    f"当前距离 dist[{self._vlabel(v)}]={self._fmt_dist(old)}",
                    current_vertex_id=u,
                    relaxing_edge=(u, v),
                    old_distance=old,
                )
                step_count += 1

                if new < old:
                    self._dist[v] = new
                    self._pred[v] = u
                    heapq.heappush(self._pq, (new, v))

                    # Step: relax_update
                    yield self._make_step(
                        step_count, "relax_update",
                        f"更新！dist[{self._vlabel(v)}]：{self._fmt_dist(old)} → {self._fmt_dist(new)}",
                        current_vertex_id=u,
                        relaxing_edge=(u, v),
                        relaxation_result="updated",
                        old_distance=old,
                        new_distance=new,
                    )
                    step_count += 1
                else:
                    # Step: relax_check
                    yield self._make_step(
                        step_count, "relax_check",
                        f"松弛未成功：{self._fmt_dist(old)} + {edge.weight} = {self._fmt_dist(new)} ≥ {self._fmt_dist(old)}",
                        current_vertex_id=u,
                        relaxing_edge=(u, v),
                        relaxation_result="unchanged",
                        old_distance=old,
                        new_distance=new,
                    )
                    step_count += 1

        # Step: complete
        path = self._reconstruct_path() if self.target_id else None
        if path and path[-1] == self.target_id:
            total = self._dist.get(self.target_id, INF)
            path_labels = " → ".join(self._vlabel(vid) for vid in path)
            msg = f"完成！最短路径：{path_labels}，总长度={self._fmt_dist(total)}。"
        elif self.target_id:
            msg = f"完成。目标 {self._vlabel(self.target_id)} 从起点 {self._vlabel(self.source_id)} 不可达。"
        else:
            msg = "完成。所有可达顶点的最短距离已计算。"

        yield self._make_step(
            step_count, "complete",
            msg,
            final_path=tuple(path) if path else None,
        )

    # ---- 辅助方法 ----

    def _make_step(self, index: int, step_type: str, message: str, **kwargs):
        """构造 DijkstraStep 快照"""
        # 对 INF 用字符串表示（JSON/pickle 兼容）
        pq_sorted = tuple(
            sorted(self._pq, key=lambda x: x[0])
        )
        return DijkstraStep(
            step_index=index,
            step_type=step_type,
            message=message,
            current_vertex_id=kwargs.get("current_vertex_id"),
            visited=tuple(self._visited),
            distances=dict(self._dist),
            predecessors=dict(self._pred),
            pq_state=pq_sorted,
            relaxing_edge=kwargs.get("relaxing_edge"),
            relaxation_result=kwargs.get("relaxation_result"),
            old_distance=kwargs.get("old_distance"),
            new_distance=kwargs.get("new_distance"),
            final_path=kwargs.get("final_path"),
        )

    def _reconstruct_path(self) -> list[str]:
        """从 source → target 重建路径"""
        if not self.target_id or self._dist.get(self.target_id, INF) == INF:
            return []
        path = []
        cur = self.target_id
        while cur is not None:
            path.append(cur)
            cur = self._pred.get(cur)
        path.reverse()
        return path if path[0] == self.source_id else []

    def _vlabel(self, vid: str) -> str:
        v = self.graph.vertices.get(vid)
        return v.label if v else vid

    @staticmethod
    def _fmt_dist(d: float) -> str:
        if d == INF:
            return "∞"
        if d == int(d):
            return str(int(d))
        return f"{d:.1f}"

    # ---- 静态验证 ----

    @staticmethod
    def validate_graph(graph: Graph, source_id: str) -> str | None:
        """验证图是否适合 Dijkstra。返回错误消息或 None"""
        if source_id not in graph.vertices:
            return f"起点 '{source_id}' 不在图中。"
        if graph.vertex_count() < 2:
            return "图中至少需要两个顶点。"
        for edges in graph.adj.values():
            for e in edges:
                if e.weight < 0:
                    return (
                        f"边 {e.source_id}→{e.target_id} 权重为负 ({e.weight})。"
                        " Dijkstra 算法要求非负权重。"
                    )
        return None
