# graph routing engine

A small pathfinding engine, stdlib only. It generates synthetic weighted graphs,
routes between nodes with Dijkstra and A*, and has a benchmark comparing the two.

## layout

```
src/            the engine
eval/           benchmark runner and generated artifacts
tests/          unit, integration and determinism tests
shared/         logging + seeding helpers
config.json     graphs + query count + seed
```

## running it

```
python -m pytest -q
python eval/run_benchmark.py
```

## results

A* with an admissible heuristic matches Dijkstra's optimal cost while expanding
far fewer nodes. Numbers in `eval/COMPARISON.md`.
