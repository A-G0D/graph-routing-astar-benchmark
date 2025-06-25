# design notes

## data model

One graph type, `Graph`: an undirected weighted graph stored as a nested
adjacency dict `{node: {neighbour: weight}}`. Nodes are integer ids and each one
also has a 2D coordinate in `Graph.coords`.

Putting a coordinate on every node is the decision the rest of the code leans on.
A*'s heuristic needs a position to estimate the remaining distance, and once the
positions are there the edge weights can just be the geometric distances. That's
also what keeps the heuristics admissible without having to prove anything.

## graph generators

Both generators are deterministic given an RNG and always return a single
connected component, so any start/goal pair you sample is reachable.

The grid lays out a lattice and can block cells to model obstacles; after
carving them it keeps the largest component. The random geometric generator
scatters points in the unit square, links nearby pairs, and stitches any
leftover components together with the shortest cross-component edges.

## search

`dijkstra` and `astar` share a binary-heap frontier and the same lazy-deletion
trick. Both report `expanded`, which is the metric I use to compare search
effort across the two.
