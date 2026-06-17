"""随机图生成器 — 每次生成 10~15 个顶点的随机图"""

import random
import math
from models.graph import Graph


def _generate_positions(
    n: int,
    area_w: int = 780,
    area_h: int = 620,
    margin: int = 50,
) -> list[tuple[int, int]]:
    """
    拒绝采样：逐个放置顶点，保证任意两点间距 ≥ min_dist。
    min_dist 根据顶点数动态计算，n 越少间距越大。
    """
    # 动态最小间距：面积 / 顶点数 的开方，确保有足够空间
    min_dist = max(90, int(math.sqrt(area_w * area_h / (n * 1.8))))
    max_attempts = 400

    positions: list[tuple[int, int]] = []

    for _ in range(n):
        best_pos = (0, 0)
        best_min = 0.0

        for _ in range(max_attempts):
            x = random.randint(margin, area_w - margin)
            y = random.randint(margin, area_h - margin)

            min_d = float("inf")
            for px, py in positions:
                d = math.hypot(x - px, y - py)
                if d < min_d:
                    min_d = d
                if min_d < min_dist:
                    break  # 早停：已经太近了

            if min_d >= min_dist:
                positions.append((x, y))
                break
            elif min_d > best_min:
                best_min = min_d
                best_pos = (x, y)
        else:
            # 所有尝试都失败 → 取最佳位置
            positions.append(best_pos)

    return positions


def create_random_graph() -> Graph:
    """
    随机生成一个有向图。
    - 顶点数：10~15
    - 布局：拒绝采样散点，顶点均匀分散不扎堆
    - 每个顶点出边：2~4 条（混合近邻 + 随机远端，边不全部挤一起）
    - 权重：1~15 的整数
    - 保证从第一个顶点可达所有其他顶点
    """
    g = Graph()
    n = random.randint(10, 15)
    labels = [chr(65 + i) for i in range(n)]

    # ---- 顶点 ----
    positions = _generate_positions(n)
    for i, (x, y) in enumerate(positions):
        g.add_vertex(x, y, label=labels[i], vid=labels[i])

    # ---- 边 ----
    vids = list(g.vertices.keys())
    for vid in vids:
        vx, vy = g.vertices[vid].x, g.vertices[vid].y

        # 按距离排序候选目标
        candidates: list[tuple[float, str]] = []
        for nid in vids:
            if nid == vid:
                continue
            nx, ny = g.vertices[nid].x, g.vertices[nid].y
            candidates.append((math.hypot(nx - vx, ny - vy), nid))
        candidates.sort(key=lambda kv: kv[0])

        k = random.randint(2, min(4, len(candidates)))

        # 划分近邻池和远端池（各占约一半）
        split = max(k, len(candidates) // 2)
        near_pool = candidates[:split]
        far_pool = candidates[split:]

        # 近邻选 k-1 或 k 个
        near_count = random.randint(k - 1, k) if far_pool else k
        near_count = min(near_count, len(near_pool))
        chosen: set[str] = set()

        if near_pool:
            for _, target_id in random.sample(near_pool, near_count):
                chosen.add(target_id)

        # 不足 k 个 → 从远端补
        need = k - len(chosen)
        if need > 0 and far_pool:
            for _, target_id in random.sample(far_pool, min(need, len(far_pool))):
                chosen.add(target_id)

        # 仍不足（候选太少）→ 按距离补足
        if len(chosen) < k:
            for _, target_id in candidates:
                if target_id not in chosen:
                    chosen.add(target_id)
                    if len(chosen) >= k:
                        break

        for target_id in chosen:
            g.add_edge(vid, target_id, random.randint(1, 15))

    # ---- 连通性 ----
    _ensure_connectivity(g)
    return g


def _ensure_connectivity(g: Graph) -> None:
    """确保从第一个顶点出发可到达所有其他顶点"""
    if g.vertex_count() < 2:
        return
    first = next(iter(g.vertices.keys()))
    reachable = _bfs_reachable(g, first)

    for vid in g.vertices:
        if vid not in reachable:
            src = random.choice(list(reachable))
            g.add_edge(src, vid, random.randint(1, 15))
            reachable = _bfs_reachable(g, first)


def _bfs_reachable(g: Graph, start: str) -> set[str]:
    """返回从 start 可到达的所有顶点集合"""
    visited = {start}
    queue = [start]
    while queue:
        u = queue.pop(0)
        for e in g.get_out_edges(u):
            if e.target_id not in visited:
                visited.add(e.target_id)
                queue.append(e.target_id)
    return visited
