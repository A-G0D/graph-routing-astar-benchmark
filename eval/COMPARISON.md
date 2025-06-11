# Dijkstra vs A* comparison

Evaluated over **200** random start/goal queries on the same graph, with Dijkstra as the optimality reference.

## Headline

- Queries where A* matched the optimal cost: **100.0%**
- Mean cost ratio (A* / optimal): **1.0000** (max 1.0000)
- Nodes expanded ratio (A* / Dijkstra): **0.027** -> 97.3% fewer
- Mean per-query speedup: **9.33x**

## Per-strategy means

| strategy | nodes expanded | latency (ms) | frontier peak |
| --- | ---: | ---: | ---: |
| dijkstra (baseline) | 309.7 | 6.7192 | 342.0 |
| a* (improved) | 8.3 | 0.7201 | 172.1 |

## Notes

- a* matched dijkstra on every reachable query
- a* expanded 97.3% fewer nodes on average
