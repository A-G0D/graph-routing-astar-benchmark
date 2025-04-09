"""Weighted graph type with 2D node coordinates."""
from __future__ import annotations

import math
from typing import Dict, List, Tuple

Node = int
Coord = Tuple[float, float]


class Graph:
    def __init__(self) -> None:
        self.coords: Dict[Node, Coord] = {}
        self.adj: Dict[Node, Dict[Node, float]] = {}

    def add_node(self, node: Node, coord: Coord) -> None:
        if node not in self.adj:
            self.adj[node] = {}
        self.coords[node] = coord

    def add_edge(self, a: Node, b: Node, weight: float) -> None:
        self.adj[a][b] = weight
        self.adj[b][a] = weight

    @property
    def nodes(self) -> List[Node]:
        return list(self.adj.keys())

    def neighbors(self, node: Node):
        return self.adj[node].items()

    def __len__(self) -> int:
        return len(self.adj)
