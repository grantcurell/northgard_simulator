#!/usr/bin/env python3
"""Replay a build from JSON action list (machine-readable)."""

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


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--map", default="standard_hostile")
    p.add_argument("--actions", default="[]", help="Python literal list of action reprs or JSON")
    args = p.parse_args()
    try:
        actions = json.loads(args.actions)
    except json.JSONDecodeError:
        actions = ast.literal_eval(args.actions)
    st = initial_state(args.map)
    final = simulate_to_horizon(st, actions, 1200.0)
    benchmarks = load_benchmarks()
    sc = score_final_state(final, benchmarks)
    print(json.dumps({"score": sc, "final_t": final.t}, indent=2))


if __name__ == "__main__":
    main()
