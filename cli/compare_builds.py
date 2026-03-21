#!/usr/bin/env python3
"""Compare mean benchmark scores for two action sequences."""

from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import northgard.gpu_ops  # noqa: F401 — require working CUDA GPU

from northgard.data_loader import load_benchmarks
from northgard.scoring import score_final_state
from northgard.sim import initial_state, simulate_to_horizon


def _parse(s: str):
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        return ast.literal_eval(s)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--map", default="standard_hostile")
    p.add_argument("--a", required=True)
    p.add_argument("--b", required=True)
    args = p.parse_args()
    benchmarks = load_benchmarks()
    sa = simulate_to_horizon(initial_state(args.map), _parse(args.a), 1200.0)
    sb = simulate_to_horizon(initial_state(args.map), _parse(args.b), 1200.0)
    print(
        json.dumps(
            {
                "a": score_final_state(sa, benchmarks),
                "b": score_final_state(sb, benchmarks),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
