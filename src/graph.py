"""Weighted graph type with 2D node coordinates."""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, Iterable, Iterator, List, Tuple

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
