"""Admissibility checks: the heuristic must never exceed the true Dijkstra
distance to the goal."""
import pytest

from shared.determinism import seeded_rng
from src.algorithms import dijkstra
from src.graph import grid_graph, random_connected_graph
from src.heuristics import by_name, euclidean, manhattan, zero


def _true_distances(g, goal):
    return {n: dijkstra(g, n, goal).cost for n in g.nodes}


def test_euclidean_admissible_on_random_graph():
    rng = seeded_rng(204)
    g = random_connected_graph(120, rng=rng)
    goal = g.nodes[0]
    true = _true_distances(g, goal)
    for n, dist in true.items():
        assert euclidean(n, goal, g) <= dist + 1e-9


def test_manhattan_admissible_on_open_grid():
    rng = seeded_rng(31)
    g = grid_graph(15, 15, rng=rng)
    goal = g.nodes[-1]
    true = _true_distances(g, goal)
    for n, dist in true.items():
        assert manhattan(n, goal, g) <= dist + 1e-9


def test_euclidean_admissible_on_grid_with_obstacles():
    rng = seeded_rng(3)
    g = grid_graph(18, 18, rng=rng, obstacle_ratio=0.15, weight_jitter=0.2)
    goal = g.nodes[len(g) // 2]
    true = _true_distances(g, goal)
    for n, dist in true.items():
        assert euclidean(n, goal, g) <= dist + 1e-9


def test_zero_is_trivially_admissible():
    rng = seeded_rng(1)
    g = grid_graph(8, 8, rng=rng)
    for n in g.nodes:
        assert zero(n, g.nodes[0], g) == 0.0


def test_by_name_lookup_and_error():
    assert by_name("euclidean") is euclidean
    assert by_name("manhattan") is manhattan
    with pytest.raises(KeyError):
        by_name("octile")
