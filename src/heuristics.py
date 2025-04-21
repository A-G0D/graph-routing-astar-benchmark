"""A* heuristics.

A heuristic estimates the remaining cost to the goal; it has to be admissible
(never an overestimate) for A* to stay optimal. The graphs here use geometric
edge weights, so straight-line distance is a safe lower bound. zero turns A*
back into Dijkstra and is useful as a control.
"""
from __future__ import annotations

import math
from typing import Callable

from .graph import Coord, Graph, Node

Heuristic = Callable[[Node, Node, Graph], float]


def zero(_a: Node, _b: Node, _g: Graph) -> float:
    """No information; turns A* into Dijkstra. Trivially admissible."""
    return 0.0


def euclidean(a: Node, goal: Node, g: Graph) -> float:
    """Straight-line distance between node coordinates."""
    pa: Coord = g.coords[a]
    pg: Coord = g.coords[goal]
    return math.hypot(pa[0] - pg[0], pa[1] - pg[1])


def manhattan(a: Node, goal: Node, g: Graph) -> float:
    """L1 distance -- exact for an obstacle-free axis-aligned grid."""
    pa: Coord = g.coords[a]
    pg: Coord = g.coords[goal]
    return abs(pa[0] - pg[0]) + abs(pa[1] - pg[1])


def by_name(name: str) -> Heuristic:
    table = {"zero": zero, "euclidean": euclidean, "manhattan": manhattan}
    if name not in table:
        raise KeyError(f"unknown heuristic {name!r}; choose from {sorted(table)}")
    return table[name]
