import pytest

from shared.determinism import seeded_rng
from src.algorithms import astar, dijkstra, path_cost
from src.graph import Graph, grid_graph, random_connected_graph
from src.heuristics import euclidean, manhattan, zero


def _small_graph() -> Graph:
    g = Graph()
    for i in range(5):
        g.add_node(i, (float(i), 0.0))
    g.add_edge(0, 1, 1.0)
    g.add_edge(1, 2, 1.0)
    g.add_edge(2, 3, 1.0)
    g.add_edge(3, 4, 1.0)
    g.add_edge(0, 4, 10.0)  # tempting but expensive shortcut
    return g


def test_dijkstra_finds_shortest_chain():
    g = _small_graph()
    res = dijkstra(g, 0, 4)
    assert res.path == [0, 1, 2, 3, 4]
    assert res.cost == pytest.approx(4.0)


def test_astar_matches_dijkstra_cost():
    g = _small_graph()
    d = dijkstra(g, 0, 4)
    a = astar(g, 0, 4, euclidean)
    assert a.cost == pytest.approx(d.cost)
    assert a.path == d.path


def test_same_node_is_zero_cost():
    g = _small_graph()
    res = dijkstra(g, 2, 2)
    assert res.cost == pytest.approx(0.0)
    assert res.path == [2]


def test_path_cost_validates_edges():
    g = _small_graph()
    assert path_cost(g, [0, 1, 2]) == pytest.approx(2.0)
    with pytest.raises(ValueError):
        path_cost(g, [0, 2])  # no direct edge


def test_unknown_endpoint_raises():
    g = _small_graph()
    with pytest.raises(KeyError):
        dijkstra(g, 0, 999)


def test_astar_optimal_on_grid_with_obstacles():
    rng = seeded_rng(31)
    g = grid_graph(25, 25, rng=rng, obstacle_ratio=0.15, weight_jitter=0.1)
    qrng = seeded_rng(123)
    nodes = g.nodes
    for _ in range(40):
        s = qrng.choice(nodes)
        t = qrng.choice(nodes)
        d = dijkstra(g, s, t)
        a = astar(g, s, t, euclidean)
        assert a.cost == pytest.approx(d.cost, rel=1e-9, abs=1e-9)


def test_astar_expands_no_more_than_dijkstra_on_random():
    rng = seeded_rng(204)
    g = random_connected_graph(400, rng=rng)
    qrng = seeded_rng(9)
    nodes = g.nodes
    saved = 0
    total = 0
    for _ in range(30):
        s, t = qrng.choice(nodes), qrng.choice(nodes)
        if s == t:
            continue
        d = dijkstra(g, s, t)
        a = astar(g, s, t, euclidean)
        assert a.cost == pytest.approx(d.cost, rel=1e-9, abs=1e-9)
        assert a.expanded <= d.expanded
        if a.expanded < d.expanded:
            saved += 1
        total += 1
    assert saved >= total * 0.6  # should win on most queries


def test_zero_heuristic_reduces_to_dijkstra():
    g = _small_graph()
    a = astar(g, 0, 4, zero)
    d = dijkstra(g, 0, 4)
    assert a.expanded == d.expanded
    assert a.cost == pytest.approx(d.cost)
