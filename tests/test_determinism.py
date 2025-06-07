"""Same seed should give the same numbers run to run."""
from shared.determinism import seeded_rng
from src.evaluation import compare, sample_queries
from src.graph import grid_graph, random_connected_graph
from src.heuristics import euclidean


def _run_grid():
    rng = seeded_rng(31)
    g = grid_graph(28, 28, rng=rng, obstacle_ratio=0.15, weight_jitter=0.1)
    qrng = seeded_rng(7)
    queries = sample_queries(g, 50, rng=qrng)
    cmp = compare(g, queries, heuristic=euclidean)
    return (len(g), g.num_edges, cmp.optimal_fraction,
            cmp.expansion_ratio, cmp.baseline.mean_expanded,
            cmp.improved.mean_expanded)


def _run_random():
    rng = seeded_rng(31)
    g = random_connected_graph(350, rng=rng)
    qrng = seeded_rng(7)
    queries = sample_queries(g, 50, rng=qrng)
    cmp = compare(g, queries, heuristic=euclidean)
    return (len(g), g.num_edges, cmp.optimal_fraction, cmp.expansion_ratio)


def test_grid_run_is_repeatable():
    a, b, c = _run_grid(), _run_grid(), _run_grid()
    assert a == b == c


def test_random_run_is_repeatable():
    assert _run_random() == _run_random()


def test_query_sampling_is_reproducible():
    rng = seeded_rng(31)
    g = grid_graph(20, 20, rng=rng)
    a = [(q.start, q.goal) for q in sample_queries(g, 40, rng=seeded_rng(99))]
    b = [(q.start, q.goal) for q in sample_queries(g, 40, rng=seeded_rng(99))]
    assert a == b
