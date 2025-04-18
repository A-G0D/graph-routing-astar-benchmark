"""Weighted graph type plus two synthetic generators (a grid and a random
geometric graph). Every node carries a 2D coordinate because A*'s heuristic
needs positions, and that's also what keeps the geometric heuristics admissible.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, Iterable, Iterator, List, Optional, Tuple

Node = int
Coord = Tuple[float, float]


@dataclass
class Graph:
    """Undirected weighted graph; adjacency is {node: {neighbour: weight}}."""

    coords: Dict[Node, Coord] = field(default_factory=dict)
    adj: Dict[Node, Dict[Node, float]] = field(default_factory=dict)

    def add_node(self, node: Node, coord: Coord) -> None:
        if node not in self.adj:
            self.adj[node] = {}
        self.coords[node] = coord

    def add_edge(self, a: Node, b: Node, weight: float) -> None:
        if weight < 0:
            raise ValueError("edge weights must be non-negative")
        if a not in self.adj or b not in self.adj:
            raise KeyError("both endpoints must be added before the edge")
        # Keep the cheaper weight if a parallel edge sneaks in.
        if b in self.adj[a] and self.adj[a][b] <= weight:
            return
        self.adj[a][b] = weight
        self.adj[b][a] = weight

    @property
    def nodes(self) -> List[Node]:
        return list(self.adj.keys())

    def neighbors(self, node: Node) -> Iterable[Tuple[Node, float]]:
        return self.adj[node].items()

    def __len__(self) -> int:
        return len(self.adj)

    @property
    def num_edges(self) -> int:
        return sum(len(nbrs) for nbrs in self.adj.values()) // 2

    def edge_weight(self, a: Node, b: Node) -> float:
        return self.adj[a][b]

    def iter_edges(self) -> Iterator[Tuple[Node, Node, float]]:
        seen: set[Tuple[Node, Node]] = set()
        for a, nbrs in self.adj.items():
            for b, w in nbrs.items():
                key = (a, b) if a < b else (b, a)
                if key not in seen:
                    seen.add(key)
                    yield key[0], key[1], w


def _euclid(p: Coord, q: Coord) -> float:
    return math.hypot(p[0] - q[0], p[1] - q[1])


def grid_graph(
    width: int,
    height: int,
    *,
    rng,
    obstacle_ratio: float = 0.0,
    diagonal: bool = False,
    weight_jitter: float = 0.0,
) -> Graph:
    """A width x height lattice with optional blocked cells.

    Coordinates are the (col, row) cell positions, so manhattan is exact on the
    open grid. After carving obstacles I keep only the largest component so the
    result is connected. weight_jitter only ever raises an edge's cost, which is
    enough to break the trivial symmetry without breaking admissibility.
    """
    if not (0.0 <= obstacle_ratio < 1.0):
        raise ValueError("obstacle_ratio must be in [0, 1)")

    blocked = set()
    if obstacle_ratio > 0.0:
        for c in range(width):
            for r in range(height):
                if rng.random() < obstacle_ratio:
                    blocked.add((c, r))

    def cell_id(c: int, r: int) -> Node:
        return r * width + c

    g = Graph()
    for c in range(width):
        for r in range(height):
            if (c, r) in blocked:
                continue
            g.add_node(cell_id(c, r), (float(c), float(r)))

    steps = [(1, 0), (0, 1)]
    if diagonal:
        steps += [(1, 1), (1, -1)]

    for c in range(width):
        for r in range(height):
            if (c, r) in blocked:
                continue
            for dc, dr in steps:
                nc, nr = c + dc, r + dr
                if 0 <= nc < width and 0 <= nr < height and (nc, nr) not in blocked:
                    base = math.hypot(dc, dr)
                    extra = rng.random() * weight_jitter
                    g.add_edge(cell_id(c, r), cell_id(nc, nr), base + extra)

    return _largest_component(g)


def random_connected_graph(
    n: int,
    *,
    rng,
    radius: float = 0.0,
    extent: float = 1.0,
) -> Graph:
    """Random geometric graph on n points, stitched into one component.

    Points are uniform in [0, extent]^2 and linked when within radius; the edge
    weight is the Euclidean distance. If the radius graph is disconnected I join
    the leftover components with their shortest cross-edges.
    """
    if n < 2:
        raise ValueError("need at least two nodes")
    if radius <= 0.0:
        # rough connectivity threshold for n points in the unit square
        radius = extent * math.sqrt(math.log(n) / n) * 1.8

    pts: Dict[Node, Coord] = {
        i: (rng.random() * extent, rng.random() * extent) for i in range(n)
    }
    g = Graph()
    for i, p in pts.items():
        g.add_node(i, p)

    for i in range(n):
        for j in range(i + 1, n):
            d = _euclid(pts[i], pts[j])
            if d <= radius:
                g.add_edge(i, j, d)

    _connect_components(g, pts)
    return g


def _components(g: Graph) -> List[List[Node]]:
    seen: set[Node] = set()
    comps: List[List[Node]] = []
    for start in g.nodes:
        if start in seen:
            continue
        stack = [start]
        comp: List[Node] = []
        seen.add(start)
        while stack:
            cur = stack.pop()
            comp.append(cur)
            for nbr in g.adj[cur]:
                if nbr not in seen:
                    seen.add(nbr)
                    stack.append(nbr)
        comps.append(comp)
    return comps


def _largest_component(g: Graph) -> Graph:
    comps = _components(g)
    if len(comps) <= 1:
        return g
    keep = set(max(comps, key=len))
    out = Graph()
    for node in keep:
        out.add_node(node, g.coords[node])
    for a, b, w in g.iter_edges():
        if a in keep and b in keep:
            out.add_edge(a, b, w)
    return out


def _connect_components(g: Graph, pts: Dict[Node, Coord]) -> None:
    """Add minimum cross-component edges until the graph is connected."""
    comps = _components(g)
    while len(comps) > 1:
        base = set(comps[0])
        best: Optional[Tuple[float, Node, Node]] = None
        for a in base:
            for b in pts:
                if b in base:
                    continue
                d = _euclid(pts[a], pts[b])
                if best is None or d < best[0]:
                    best = (d, a, b)
        assert best is not None
        _, a, b = best
        g.add_edge(a, b, best[0])
        comps = _components(g)
