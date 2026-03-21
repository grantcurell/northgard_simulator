#!/usr/bin/env python3
"""Run beam search for Lynx 20-minute lethality; prints JSON plan."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import northgard.gpu_ops  # noqa: F401 — side effect: require working CUDA GPU

from northgard.data_loader import load_benchmarks
from northgard.search.beam_search import beam_search
from northgard.sim import apply_action, initial_state


def _state_to_json(state):
    return {
        "resources": {
            "food": round(state.resources.food, 2),
            "wood": round(state.resources.wood, 2),
            "krowns": round(state.resources.krowns, 2),
            "stone": round(state.resources.stone, 2),
            "iron": round(state.resources.iron, 2),
            "lore": round(state.resources.lore, 2),
            "fame": round(state.resources.fame, 2),
            "trophies": round(state.resources.trophies, 2),
        },
        "population": state.units.villagers
        + state.units.woodcutters
        + state.units.trackers
        + state.units.mielikki
        + state.units.brundr
        + state.units.kaelinn,
        "housing_cap": state.housing_cap,
        "warband_cap": state.warband_cap,
        "army": {
            "mielikki": state.units.mielikki,
            "brundr": state.units.brundr,
            "kaelinn": state.units.kaelinn,
            "trackers": state.units.trackers,
        },
        "lores": sorted(state.lores),
        "hunter_nodes": sorted(state.hunter_nodes),
        "path_complete_purchases": state.path_complete_purchases,
        "t": round(state.t, 2),
    }


def main() -> None:
    p = argparse.ArgumentParser(description="Northgard Lynx 20m build optimizer (GPU-batched beam)")
    p.add_argument("--map", default="standard_hostile", help="Map id under data/maps/")
    p.add_argument("--beam", type=int, default=24)
    p.add_argument("--horizon", type=float, default=1200.0, help="Seconds (20 min = 1200)")
    p.add_argument("--rounds", type=int, default=80)
    p.add_argument("--expansions", type=int, default=6000)
    args = p.parse_args()

    benchmarks = load_benchmarks()
    init = initial_state(args.map)
    result = beam_search(
        init,
        benchmarks,
        beam_width=args.beam,
        horizon_sec=args.horizon,
        max_rounds=args.rounds,
        max_expansions=args.expansions,
    )

    timeline = []
    replay = initial_state(args.map)
    for a in result.actions:
        timeline.append({"t": round(replay.t, 1), "action": str(a)})
        apply_action(replay, a)

    out = {
        "assumptions": {
            "map": args.map,
            "horizon_sec": args.horizon,
            "beam_width": args.beam,
            "gpu_batch_heuristic": True,
        },
        "timeline": timeline,
        "final_state": _state_to_json(result.final_state),
        "score": {
            "mean_benchmark_score": round(result.combat_score, 3),
            "heuristic_score": round(result.heuristic_score, 3),
        },
    }
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
