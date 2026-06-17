"""图数据结构 — 有向图，邻接表实现"""

from .vertex import Vertex
from .edge import Edge
from config import VERTEX_R


class Graph:
    """有向图：顶点字典 + 邻接表"""

    def __init__(self):
        self.vertices: dict[str, Vertex] = {}
        self.adj: dict[str, list[Edge]] = {}
        self._next_id = 0

    # ---- 顶点 CRUD ----

    def add_vertex(self, x: int, y: int, label: str = "", vid: str = "") -> str:
        """在坐标 (x,y) 处添加顶点，返回顶点 id。可指定 vid 或自动生成"""
        if not vid:
            vid = self._gen_id()
        elif vid in self.vertices:
            # ID 冲突，生成新的
            vid = self._gen_id()
        v = Vertex(id=vid, x=x, y=y, label=label if label else vid)
        self.vertices[vid] = v
        self.adj[vid] = []
        return vid

    def remove_vertex(self, vid: str):
        """删除顶点以及所有关联边"""
        if vid not in self.vertices:
            return
        del self.vertices[vid]
        del self.adj[vid]
        # 删除所有指向该顶点的边
        for src in self.adj:
            self.adj[src] = [e for e in self.adj[src] if e.target_id != vid]

    def move_vertex(self, vid: str, x: int, y: int):
        """移动顶点位置"""
        if vid in self.vertices:
            self.vertices[vid].x = x
            self.vertices[vid].y = y

    def vertex_at_xy(self, x: int, y: int) -> Vertex | None:
        """返回坐标 (x,y) 处的顶点（命中检测），无则返回 None"""
        for v in reversed(list(self.vertices.values())):
            if v.contains_point(x, y, VERTEX_R + 4):
                return v
        return None

    # ---- 边 CRUD ----

    def add_edge(self, source_id: str, target_id: str, weight: float = 1.0) -> bool:
        """添加有向边 source → target，若已存在则覆盖权重。返回 True 表示成功"""
        if source_id not in self.vertices or target_id not in self.vertices:
            return False
        if source_id == target_id:
            return False
        # 若已存在则更新权重
        existing = self.get_edge(source_id, target_id)
        if existing:
            existing.weight = weight
            return True
        edge = Edge(source_id=source_id, target_id=target_id, weight=weight)
        self.adj[source_id].append(edge)
        return True

    def remove_edge(self, source_id: str, target_id: str) -> bool:
        """删除有向边 source → target"""
        if source_id not in self.adj:
            return False
        before = len(self.adj[source_id])
        self.adj[source_id] = [
            e for e in self.adj[source_id] if e.target_id != target_id
        ]
        return len(self.adj[source_id]) < before

    def update_edge_weight(self, source_id: str, target_id: str, weight: float):
        """更新边权重"""
        edge = self.get_edge(source_id, target_id)
        if edge:
            edge.weight = weight

    def get_edge(self, source_id: str, target_id: str) -> Edge | None:
        """获取指定边，不存在返回 None"""
        if source_id not in self.adj:
            return None
        for e in self.adj[source_id]:
            if e.target_id == target_id:
                return e
        return None

    def get_out_edges(self, vid: str) -> list[Edge]:
        """获取从 vid 出发的所有边"""
        return self.adj.get(vid, [])

    def get_in_edges(self, vid: str) -> list[Edge]:
        """获取指向 vid 的所有边"""
        result = []
        for src in self.adj:
            for e in self.adj[src]:
                if e.target_id == vid:
                    result.append(e)
        return result

    def has_edge_between(self, a: str, b: str) -> bool:
        """检查 a→b 或 b→a 是否有边（用于判断双向边偏移）"""
        return self.get_edge(a, b) is not None or self.get_edge(b, a) is not None

    # ---- 边权重标签命中检测 ----

    def edge_weight_at_xy(
        self, x: int, y: int, offset: float
    ) -> tuple[str, str] | None:
        """检测坐标 (x,y) 是否落在某条边的权重标签上。返回 (source_id, target_id) 或 None"""
        for src_id, edges in self.adj.items():
            src_v = self.vertices[src_id]
            for edge in edges:
                tgt_v = self.vertices[edge.target_id]
                # 判断是否双向
                bidirectional = self.get_edge(edge.target_id, src_id) is not None
                lx, ly = edge.weight_label_position(
                    src_v.x, src_v.y, tgt_v.x, tgt_v.y, offset, bidirectional
                )
                if abs(x - lx) < 20 and abs(y - ly) < 12:
                    return (src_id, edge.target_id)
        return None

    # ---- 工具方法 ----

    def clear(self):
        """清空图"""
        self.vertices.clear()
        self.adj.clear()
        self._next_id = 0

    def vertex_count(self) -> int:
        return len(self.vertices)

    def edge_count(self) -> int:
        return sum(len(edges) for edges in self.adj.values())

    def _gen_id(self) -> str:
        """生成下一个顶点 ID"""
        while True:
            self._next_id += 1
            vid = str(self._next_id)
            if vid not in self.vertices:
                return vid

    def __repr__(self) -> str:
        return (
            f"Graph(vertices={self.vertex_count()}, edges={self.edge_count()})"
        )
