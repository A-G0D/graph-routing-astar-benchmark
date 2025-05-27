import json

import pytest

from shared.determinism import seeded_rng
from src.evaluation import compare, sample_queries, write_reports
from src.graph import grid_graph, random_connected_graph
from src.heuristics import euclidean, manhattan


def test_sample_queries_are_distinct_pairs():
    rng = seeded_rng(31)
    g = grid_graph(20, 20, rng=rng)
    qrng = seeded_rng(5)
    qs = sample_queries(g, 50, rng=qrng)
    assert len(qs) == 50
    seen = {(q.start, q.goal) for q in qs}
    assert len(seen) == 50
    for q in qs:
        assert q.start != q.goal


def test_compare_reports_full_optimality():
    rng = seeded_rng(204)
    g = grid_graph(25, 25, rng=rng, obstacle_ratio=0.1, weight_jitter=0.1)
    qrng = seeded_rng(7)
    qs = sample_queries(g, 60, rng=qrng)
    cmp = compare(g, qs, heuristic=euclidean)
    # admissible heuristic -> optimal everywhere
    assert cmp.optimal_fraction == pytest.approx(1.0)
    assert cmp.mean_cost_ratio == pytest.approx(1.0, abs=1e-9)


def test_compare_shows_expansion_savings():
    rng = seeded_rng(31)
    g = random_connected_graph(500, rng=rng)
    qrng = seeded_rng(11)
    qs = sample_queries(g, 80, rng=qrng)
    cmp = compare(g, qs, heuristic=euclidean)
    assert cmp.expansion_ratio < 1.0
    assert cmp.improved.mean_expanded < cmp.baseline.mean_expanded


def test_write_reports_emits_files(tmp_path):
    rng = seeded_rng(31)
    g = grid_graph(15, 15, rng=rng)
    qrng = seeded_rng(2)
    qs = sample_queries(g, 30, rng=qrng)
    cmp = compare(g, qs, heuristic=manhattan)
    json_path, md_path = write_reports(cmp, tmp_path)
    assert json_path.exists() and md_path.exists()
    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["queries"] == 30
    assert "optimal_fraction" in data
    assert "A*" in md_path.read_text(encoding="utf-8")
