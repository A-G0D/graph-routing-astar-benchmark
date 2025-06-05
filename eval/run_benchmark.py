"""Builds the graphs in config.json, samples queries, runs both strategies and
writes the eval artifacts. Run from the project root: python eval/run_benchmark.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from shared.determinism import seeded_rng, set_seed
from shared.obs import Observer

from src.evaluation import compare, sample_queries, write_reports
from src.graph import grid_graph, random_connected_graph
from src.heuristics import by_name

ROOT = Path(__file__).resolve().parent.parent


def load_config() -> dict:
    return json.loads((ROOT / "config.json").read_text(encoding="utf-8"))


def build_graph(spec: dict, rng):
    kind = spec["kind"]
    if kind == "grid":
        return grid_graph(
            spec["width"],
            spec["height"],
            rng=rng,
            obstacle_ratio=spec.get("obstacle_ratio", 0.0),
            diagonal=spec.get("diagonal", False),
            weight_jitter=spec.get("weight_jitter", 0.0),
        )
    if kind == "random":
        return random_connected_graph(
            spec["n"], rng=rng, radius=spec.get("radius", 0.0)
        )
    raise ValueError(f"unknown graph kind {kind!r}")


def main() -> None:
    cfg = load_config()
    seed = cfg.get("seed", 913)
    set_seed(seed)

    heuristic = by_name(cfg.get("heuristic", "euclidean"))
    log_path = ROOT / "logs" / "benchmark.jsonl"
    obs = Observer("benchmark", sink=log_path, deterministic=True)

    aggregate = {"seed": seed, "graphs": []}
    last_cmp = None
    for spec in cfg["graphs"]:
        rng = seeded_rng(seed)
        g = build_graph(spec, rng)
        qrng = seeded_rng(seed + 1)
        queries = sample_queries(g, cfg.get("queries", 200), rng=qrng)
        # Manhattan only makes sense on the axis-aligned grids.
        h = by_name("manhattan") if spec["kind"] == "grid" and not spec.get(
            "diagonal", False
        ) else heuristic
        cmp = compare(g, queries, heuristic=h, observer=obs)
        last_cmp = cmp
        aggregate["graphs"].append(
            {
                "name": spec.get("name", spec["kind"]),
                "nodes": len(g),
                "edges": g.num_edges,
                "optimal_fraction": cmp.optimal_fraction,
                "expansion_ratio": cmp.expansion_ratio,
                "speedup": cmp.speedup,
            }
        )
        print(
            f"[{spec.get('name', spec['kind'])}] nodes={len(g)} edges={g.num_edges} "
            f"optimal={cmp.optimal_fraction * 100:.1f}% "
            f"expansion_ratio={cmp.expansion_ratio:.3f} speedup={cmp.speedup:.2f}x"
        )

    obs.close()
    (ROOT / "eval" / "summary.json").write_text(
        json.dumps(aggregate, indent=2), encoding="utf-8"
    )
    if last_cmp is not None:
        write_reports(last_cmp, ROOT / "eval")
    print(f"wrote artifacts to {ROOT / 'eval'}")


if __name__ == "__main__":
    main()
