import math

import pytest

from shared.determinism import seeded_rng
from src.graph import Graph, grid_graph, random_connected_graph
from src.graph import _components  # type: ignore


def test_add_edge_is_symmetric():
    g = Graph()
    g.add_node(0, (0.0, 0.0))
    g.add_node(1, (1.0, 0.0))
    g.add_edge(0, 1, 2.5)
    assert g.edge_weight(0, 1) == 2.5
    assert g.edge_weight(1, 0) == 2.5
    assert g.num_edges == 1


def test_negative_weight_rejected():
    g = Graph()
    g.add_node(0, (0.0, 0.0))
    g.add_node(1, (1.0, 0.0))
    with pytest.raises(ValueError):
        g.add_edge(0, 1, -1.0)


def test_edge_requires_known_endpoints():
    g = Graph()
    g.add_node(0, (0.0, 0.0))
    with pytest.raises(KeyError):
        g.add_edge(0, 99, 1.0)


def test_parallel_edge_keeps_cheaper():
    g = Graph()
    g.add_node(0, (0.0, 0.0))
    g.add_node(1, (1.0, 0.0))
    g.add_edge(0, 1, 5.0)
    g.add_edge(0, 1, 2.0)
    assert g.edge_weight(0, 1) == 2.0


def test_open_grid_dimensions():
    rng = seeded_rng(31)
    g = grid_graph(10, 8, rng=rng)
    assert len(g) == 80
    assert g.num_edges == 10 * (8 - 1) + 8 * (10 - 1)


def test_grid_with_obstacles_is_connected():
    rng = seeded_rng(31)
    g = grid_graph(30, 30, rng=rng, obstacle_ratio=0.2)
    assert len(g) > 0
    assert len(g) < 900  # some cells removed
    assert len(_components(g)) == 1


def test_grid_jitter_only_raises_cost():
    rng = seeded_rng(7)
    g = grid_graph(12, 12, rng=rng, weight_jitter=0.3)
    for _a, _b, w in g.iter_edges():
        assert w >= 1.0 - 1e-9  # base orthogonal step is 1.0


def test_random_graph_is_connected_and_metric():
    rng = seeded_rng(204)
    g = random_connected_graph(200, rng=rng)
    assert len(g) == 200
    assert len(_components(g)) == 1
    for a, b, w in g.iter_edges():
        pa, pb = g.coords[a], g.coords[b]
        assert math.isclose(w, math.hypot(pa[0] - pb[0], pa[1] - pb[1]), rel_tol=1e-9)


def test_random_graph_too_small():
    rng = seeded_rng(31)
    with pytest.raises(ValueError):
        random_connected_graph(1, rng=rng)
