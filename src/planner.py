"""Planner front-end over dijkstra/astar.

Everything else (eval, tests) goes through Planner instead of the raw search
functions, so strategy choice and logging live in one place. Each plan emits one
trace event through the shared logger.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import List, Optional

from shared.obs import Observer

from .algorithms import SearchResult, astar, dijkstra
from .graph import Graph, Node
from .heuristics import Heuristic, by_name, euclidean


@dataclass
class PlanRequest:
    start: Node
    goal: Node


@dataclass
class PlanResult:
    start: Node
    goal: Node
    path: List[Node]
    cost: float
    expanded: int
    strategy: str
    latency_ms: float = 0.0
    meta: dict = field(default_factory=dict)

    @property
    def found(self) -> bool:
        return bool(self.path)


class Planner:
    """Routes on a fixed graph with one strategy ("dijkstra" or "astar").

    The heuristic (name or callable) only matters for A* and defaults to
    euclidean, which is admissible on these graphs.
    """

    def __init__(
        self,
        graph: Graph,
        *,
        strategy: str = "astar",
        heuristic=euclidean,
        observer: Optional[Observer] = None,
    ) -> None:
        if strategy not in ("dijkstra", "astar"):
            raise ValueError(f"unknown strategy {strategy!r}")
        self.graph = graph
        self.strategy = strategy
        self.heuristic: Heuristic = (
            by_name(heuristic) if isinstance(heuristic, str) else heuristic
        )
        self.obs = observer or Observer("planner")

    def _search(self, start: Node, goal: Node) -> SearchResult:
        if self.strategy == "dijkstra":
            return dijkstra(self.graph, start, goal)
        return astar(self.graph, start, goal, self.heuristic)

    def plan(self, request: PlanRequest) -> PlanResult:
        start_t = time.perf_counter()
        result = self._search(request.start, request.goal)
        latency_ms = (time.perf_counter() - start_t) * 1000.0

        self.obs.emit(
            input={"start": request.start, "goal": request.goal,
                   "strategy": self.strategy},
            output={"cost": result.cost, "expanded": result.expanded,
                    "hops": len(result.path)},
            latency_ms=latency_ms,
        )
        return PlanResult(
            start=request.start,
            goal=request.goal,
            path=result.path,
            cost=result.cost,
            expanded=result.expanded,
            strategy=self.strategy,
            latency_ms=latency_ms,
            meta={"frontier_peak": result.frontier_peak},
        )

    def plan_many(self, requests: List[PlanRequest]) -> List[PlanResult]:
        return [self.plan(r) for r in requests]
