"""Runs the same batch of queries through both strategies and computes the
comparison: optimality (how often A* matches Dijkstra's cost), cost ratios,
expansions, and latency. Writes comparison.json and COMPARISON.md.
"""
from __future__ import annotations

import json
import math
import random
import statistics
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import List, Tuple

from shared.obs import Observer

from .graph import Graph
from .heuristics import euclidean
from .planner import Planner, PlanRequest, PlanResult

COST_TOL = 1e-9


@dataclass
class StrategyStats:
    strategy: str
    mean_expanded: float
    mean_latency_ms: float
    mean_frontier_peak: float
    queries: int


@dataclass
class Comparison:
    queries: int
    optimal_fraction: float
    mean_cost_ratio: float
    max_cost_ratio: float
    expansion_ratio: float
    speedup: float
    baseline: StrategyStats
    improved: StrategyStats
    notes: List[str] = field(default_factory=list)


def sample_queries(
    g: Graph, n: int, *, rng: random.Random, min_hops: int = 1
) -> List[PlanRequest]:
    """Pick ``n`` distinct random start/goal pairs from the graph."""
    nodes = g.nodes
    if len(nodes) < 2:
        raise ValueError("graph too small to sample queries")
    out: List[PlanRequest] = []
    seen: set[Tuple[int, int]] = set()
    attempts = 0
    while len(out) < n and attempts < n * 50:
        attempts += 1
        a = rng.choice(nodes)
        b = rng.choice(nodes)
        if a == b or (a, b) in seen:
            continue
        seen.add((a, b))
        out.append(PlanRequest(start=a, goal=b))
    return out


def _summarise(strategy: str, results: List[PlanResult]) -> StrategyStats:
    return StrategyStats(
        strategy=strategy,
        mean_expanded=statistics.fmean(r.expanded for r in results),
        mean_latency_ms=statistics.fmean(r.latency_ms for r in results),
        mean_frontier_peak=statistics.fmean(
            float(r.meta.get("frontier_peak", 0)) for r in results
        ),
        queries=len(results),
    )


def compare(
    g: Graph,
    queries: List[PlanRequest],
    *,
    heuristic=euclidean,
    observer: Observer | None = None,
) -> Comparison:
    """Run both strategies over ``queries`` and compute comparison metrics."""
    base = Planner(g, strategy="dijkstra", observer=observer)
    improved = Planner(g, strategy="astar", heuristic=heuristic, observer=observer)

    base_results = base.plan_many(queries)
    impr_results = improved.plan_many(queries)

    optimal = 0
    ratios: List[float] = []
    for b, i in zip(base_results, impr_results):
        if not b.found:
            # Unreachable under ground truth -> both should agree it's unreachable.
            if not i.found:
                optimal += 1
            continue
        if i.found and abs(i.cost - b.cost) <= COST_TOL + COST_TOL * abs(b.cost):
            optimal += 1
        if b.cost > 0:
            ratios.append((i.cost if i.found else math.inf) / b.cost)

    base_stats = _summarise("dijkstra", base_results)
    impr_stats = _summarise("astar", impr_results)

    finite_ratios = [r for r in ratios if math.isfinite(r)]
    expansion_ratio = (
        impr_stats.mean_expanded / base_stats.mean_expanded
        if base_stats.mean_expanded
        else float("nan")
    )
    speedup = (
        base_stats.mean_latency_ms / impr_stats.mean_latency_ms
        if impr_stats.mean_latency_ms
        else float("nan")
    )

    notes: List[str] = []
    if optimal == len(queries):
        notes.append("a* matched dijkstra on every reachable query")
    if expansion_ratio < 1.0:
        notes.append(
            f"a* expanded {(1 - expansion_ratio) * 100:.1f}% fewer nodes on average"
        )

    return Comparison(
        queries=len(queries),
        optimal_fraction=optimal / len(queries) if queries else float("nan"),
        mean_cost_ratio=statistics.fmean(finite_ratios) if finite_ratios else float("nan"),
        max_cost_ratio=max(finite_ratios) if finite_ratios else float("nan"),
        expansion_ratio=expansion_ratio,
        speedup=speedup,
        baseline=base_stats,
        improved=impr_stats,
        notes=notes,
    )


def write_reports(cmp: Comparison, out_dir: str | Path) -> Tuple[Path, Path]:
    """Write ``comparison.json`` and ``COMPARISON.md`` into ``out_dir``."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    json_path = out / "comparison.json"
    json_path.write_text(json.dumps(asdict(cmp), indent=2), encoding="utf-8")

    md_path = out / "COMPARISON.md"
    md_path.write_text(_to_markdown(cmp), encoding="utf-8")
    return json_path, md_path


def _to_markdown(cmp: Comparison) -> str:
    b, i = cmp.baseline, cmp.improved
    lines = [
        "# Dijkstra vs A* comparison",
        "",
        f"Evaluated over **{cmp.queries}** random start/goal queries on the same "
        "graph, with Dijkstra as the optimality reference.",
        "",
        "## Headline",
        "",
        f"- Queries where A* matched the optimal cost: "
        f"**{cmp.optimal_fraction * 100:.1f}%**",
        f"- Mean cost ratio (A* / optimal): **{cmp.mean_cost_ratio:.4f}** "
        f"(max {cmp.max_cost_ratio:.4f})",
        f"- Nodes expanded ratio (A* / Dijkstra): **{cmp.expansion_ratio:.3f}** "
        f"-> {(1 - cmp.expansion_ratio) * 100:.1f}% fewer",
        f"- Mean per-query speedup: **{cmp.speedup:.2f}x**",
        "",
        "## Per-strategy means",
        "",
        "| strategy | nodes expanded | latency (ms) | frontier peak |",
        "| --- | ---: | ---: | ---: |",
        f"| dijkstra (baseline) | {b.mean_expanded:.1f} | {b.mean_latency_ms:.4f} "
        f"| {b.mean_frontier_peak:.1f} |",
        f"| a* (improved) | {i.mean_expanded:.1f} | {i.mean_latency_ms:.4f} "
        f"| {i.mean_frontier_peak:.1f} |",
        "",
    ]
    if cmp.notes:
        lines.append("## Notes")
        lines.append("")
        lines += [f"- {n}" for n in cmp.notes]
        lines.append("")
    return "\n".join(lines)
