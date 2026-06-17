"""有向边数据模型"""

from dataclasses import dataclass
import math


@dataclass
class Edge:
    """有向图中的一条边"""

    source_id: str
    target_id: str
    weight: float = 1.0

    def __hash__(self):
        return hash((self.source_id, self.target_id))

    def __eq__(self, other):
        if not isinstance(other, Edge):
            return False
        return self.source_id == other.source_id and self.target_id == other.target_id

    def midpoint(
        self, src_x: float, src_y: float, tgt_x: float, tgt_y: float
    ) -> tuple[float, float]:
        """返回边中点坐标"""
        return ((src_x + tgt_x) / 2, (src_y + tgt_y) / 2)

    def weight_label_position(
        self,
        src_x: float,
        src_y: float,
        tgt_x: float,
        tgt_y: float,
        offset: float,
        bidirectional: bool = False,
    ) -> tuple[float, float]:
        """
        返回权重标签的绘制位置。

        在中点的基础上，沿边的法线方向偏移 offset 像素。
        - 单向边：标签在中点，法线一侧偏移
        - 双向边：标签向源顶点方向偏移（30% 处而非 50%），
          这样 A→B 的权重靠近 A，B→A 的权重靠近 B，方向一目了然。
          同时法线向相反方向偏移，避免双向标签重叠。
        """
        dx = tgt_x - src_x
        dy = tgt_y - src_y
        length = math.hypot(dx, dy)
        if length == 0:
            return (src_x, src_y)

        # 双向边：沿边向源顶点偏移（从 50% 中点 → 30% 靠近源）
        if bidirectional:
            ratio = 0.3  # 离源顶点 30%，离目标 70%
        else:
            ratio = 0.5  # 中点

        mx = src_x + ratio * dx
        my = src_y + ratio * dy

        # 法线方向（顺时针旋转90度）
        nx = -dy / length
        ny = dx / length
        sign = -1 if bidirectional else 1
        return (mx + sign * nx * offset, my + sign * ny * offset)
