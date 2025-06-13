# graph routing engine

A small pathfinding engine, stdlib only. It generates synthetic weighted graphs
(grids with obstacles, random geometric graphs), routes between nodes with
Dijkstra and A*, and has a benchmark that compares the two on actual numbers.

I mostly wrote this to convince myself of the textbook claim: A* with an
admissible heuristic returns the same optimal paths as Dijkstra but expands far
fewer nodes. It does.

## layout

```
src/            the engine
  graph.py        weighted graph type + grid / random graph generators
  heuristics.py   euclidean / manhattan / zero
  algorithms.py   dijkstra + a* over a shared heap frontier
  planner.py      front-end with structured logging
  evaluation.py   metrics + comparison report
eval/           benchmark runner and generated artifacts
tests/          unit, integration and determinism tests
shared/         logging + seeding helpers
config.json     graphs + query count + seed
```

## running it

```
python -m pytest -q          # tests
python eval/run_benchmark.py # build graphs, route queries, write eval artifacts
```

## the two strategies

Dijkstra is uniform-cost search, so I use it as the ground truth for path cost.
A* adds an admissible heuristic to bias the search toward the goal instead of
expanding outward uniformly. As long as the heuristic never overestimates the
remaining distance it finds the same optimal cost while touching fewer nodes.

## results

Over 200 random queries on a 600-node random geometric graph, A* matched the
optimal cost on every query while expanding ~97% fewer nodes. The grids show a
smaller but still clear win. Numbers in [`eval/COMPARISON.md`](eval/COMPARISON.md).

See [`docs/design.md`](docs/design.md) for the data model and a couple of design
notes.
