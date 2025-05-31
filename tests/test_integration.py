"""End-to-end: build a graph, plan a batch, route through the planner."""
import pytest

from shared.determinism import seeded_rng
from shared.obs import Observer
from src.algorithms import path_cost
from src.evaluation import compare, sample_queries
from src.graph import grid_graph, random_connected_graph
from src.heuristics import euclidean
from src.planner import Planner, PlanRequest


def test_planner_routes_a_batch():
    rng = seeded_rng(31)
    g = grid_graph(30, 30, rng=rng, obstacle_ratio=0.12, weight_jitter=0.1)
    qrng = seeded_rng(8)
    queries = sample_queries(g, 25, rng=qrng)

    obs = Observer("test", deterministic=True)
    planner = Planner(g, strategy="astar", heuristic=euclidean, observer=obs)
    results = planner.plan_many(queries)

    assert len(results) == 25
    assert len(obs.events) == 25
    for r in results:
        if r.found:
            assert path_cost(g, r.path) == pytest.approx(r.cost, rel=1e-9, abs=1e-9)
            assert r.path[0] == r.start and r.path[-1] == r.goal


def test_both_strategies_agree_end_to_end():
    rng = seeded_rng(204)
    g = random_connected_graph(300, rng=rng)
    qrng = seeded_rng(13)
    queries = sample_queries(g, 40, rng=qrng)

    base = Planner(g, strategy="dijkstra")
    impr = Planner(g, strategy="astar", heuristic=euclidean)
    for q in queries:
        b = base.plan(q)
        i = impr.plan(q)
        assert i.cost == pytest.approx(b.cost, rel=1e-9, abs=1e-9)


def test_planner_rejects_bad_strategy():
    rng = seeded_rng(31)
    g = grid_graph(5, 5, rng=rng)
    with pytest.raises(ValueError):
        Planner(g, strategy="greedy")


def test_full_comparison_pipeline():
    rng = seeded_rng(204)
    g = grid_graph(35, 35, rng=rng, obstacle_ratio=0.15, weight_jitter=0.12)
    qrng = seeded_rng(21)
    queries = sample_queries(g, 100, rng=qrng)
    cmp = compare(g, queries, heuristic=euclidean)
    assert cmp.optimal_fraction == pytest.approx(1.0)
    assert cmp.expansion_ratio < 1.0
