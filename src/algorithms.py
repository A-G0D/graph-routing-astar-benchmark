"""Dijkstra and A* over the Graph type.

Both share a binary-heap frontier and count node expansions (pops that relax
neighbours) as the effort metric. Priority ties break on insertion order, which
keeps the expansion order deterministic.
"""
from __future__ import annotations

import heapq
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .graph import Graph, Node
from .heuristics import Heuristic, zero


@dataclass
class SearchResult:
    # path is empty and cost is inf when the goal is unreachable.
    path: List[Node]
    cost: float
    expanded: int
    frontier_peak: int = 0
    meta: Dict[str, object] = field(default_factory=dict)

    @property
    def found(self) -> bool:
        return bool(self.path)


def _reconstruct(came_from: Dict[Node, Node], start: Node, goal: Node) -> List[Node]:
    if goal not in came_from and goal != start:
        return []
    path = [goal]
    cur = goal
    while cur != start:
        cur = came_from[cur]
        path.append(cur)
    path.reverse()
    return path


def dijkstra(g: Graph, start: Node, goal: Node) -> SearchResult:
    """Shortest path from start to goal. Stops once goal is settled."""
    if start not in g.adj or goal not in g.adj:
        raise KeyError("start and goal must be nodes in the graph")

    dist: Dict[Node, float] = {start: 0.0}
    came_from: Dict[Node, Node] = {}
    visited: set[Node] = set()
    counter = 0
    frontier: List[tuple] = [(0.0, 0, start)]
    expanded = 0
    peak = 1

    while frontier:
        d, _, u = heapq.heappop(frontier)
        if u in visited:
            continue
        visited.add(u)
        if u == goal:
            break
        expanded += 1
        for v, w in g.neighbors(u):
            if v in visited:
                continue
            nd = d + w
            if nd < dist.get(v, math.inf):
                dist[v] = nd
                came_from[v] = u
                counter += 1
                heapq.heappush(frontier, (nd, counter, v))
        peak = max(peak, len(frontier))

    path = _reconstruct(came_from, start, goal)
    cost = dist.get(goal, math.inf) if path or start == goal else math.inf
    return SearchResult(path=path, cost=cost, expanded=expanded, frontier_peak=peak)


def astar(
    g: Graph,
    start: Node,
    goal: Node,
    heuristic: Optional[Heuristic] = None,
) -> SearchResult:
    """A* with priority g + h. Defaults to the zero heuristic, i.e. Dijkstra."""
    if start not in g.adj or goal not in g.adj:
        raise KeyError("start and goal must be nodes in the graph")
    h = heuristic or zero

    g_score: Dict[Node, float] = {start: 0.0}
    came_from: Dict[Node, Node] = {}
    visited: set[Node] = set()
    counter = 0
    f0 = h(start, goal, g)
    frontier: List[tuple] = [(f0, 0, start)]
    expanded = 0
    peak = 1

    while frontier:
        _, _, u = heapq.heappop(frontier)
        if u in visited:
            continue
        visited.add(u)
        if u == goal:
            break
        expanded += 1
        gu = g_score[u]
        for v, w in g.neighbors(u):
            if v in visited:
                continue
            tentative = gu + w
            if tentative < g_score.get(v, math.inf):
                g_score[v] = tentative
                came_from[v] = u
                counter += 1
                heapq.heappush(frontier, (tentative + h(v, goal, g), counter, v))
        peak = max(peak, len(frontier))

    path = _reconstruct(came_from, start, goal)
    cost = g_score.get(goal, math.inf) if path or start == goal else math.inf
    return SearchResult(path=path, cost=cost, expanded=expanded, frontier_peak=peak)


def path_cost(g: Graph, path: List[Node]) -> float:
    """Sum the edge weights along ``path`` (validates adjacency)."""
    if not path:
        return math.inf
    total = 0.0
    for a, b in zip(path, path[1:]):
        if b not in g.adj[a]:
            raise ValueError(f"path uses missing edge {a}->{b}")
        total += g.adj[a][b]
    return total
