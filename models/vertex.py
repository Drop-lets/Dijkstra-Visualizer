"""顶点数据模型"""

from dataclasses import dataclass


@dataclass
class Vertex:
    """有向图中的一个顶点"""

    id: str
    x: int
    y: int
    label: str = ""

    def __post_init__(self):
        if not self.label:
            self.label = self.id

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        if not isinstance(other, Vertex):
            return False
        return self.id == other.id

    def contains_point(self, px: int, py: int, radius: int) -> bool:
        """判断点 (px, py) 是否在该顶点圆内"""
        return (px - self.x) ** 2 + (py - self.y) ** 2 <= radius ** 2
