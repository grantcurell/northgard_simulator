#!/usr/bin/env python3
"""Run beam search for Lynx 20-minute lethality; prints a plan (Markdown or JSON)."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import northgard.gpu_ops  # noqa: F401 — side effect: require working CUDA GPU

from northgard.action_labels import describe_action
from northgard.data_loader import load_benchmarks
from northgard.horizon_playbook import (
    build_playbook_sections,
    compute_action_intervals,
    format_horizon_playbook_markdown,
)
from northgard.search.beam_search import beam_search
from northgard.sim import apply_action, initial_state


def _fmt_sim_clock_seconds(sec: float) -> str:
    s = int(round(float(sec)))
    m, r = divmod(s, 60)
    return f"{m}m {r:02d}s ({s} s sim clock)"


_WAIT_RE = re.compile(r"^Wait\(seconds=([\d.]+)\)\s*$")


def _wait_seconds_from_action_repr(action: str) -> float | None:
    m = _WAIT_RE.match(action.strip())
    return float(m.group(1)) if m else None


def _format_timeline_markdown_lines(timeline: list) -> list[str]:
    """One line per logical step; merges consecutive identical Wait(...) for readability."""
    lines: list[str] = []
    n = 1
    i = 0
    while i < len(timeline):
        step = timeline[i]
        act = str(step.get("action", ""))
        ws = _wait_seconds_from_action_repr(act)
        if ws is not None:
            j = i
            while (
                j + 1 < len(timeline)
                and _wait_seconds_from_action_repr(str(timeline[j + 1].get("action", ""))) == ws
            ):
                j += 1
            k = j - i + 1
            t0 = float(step["t"])
            t_end = t0 + k * ws
            lines.append(
                f"{n}. **{_fmt_sim_clock_seconds(t0)} → {_fmt_sim_clock_seconds(t_end)}** — "
                f"Pass time: **{k}×{ws:g}s** wait (consecutive; no builds/recruits in these steps)."
            )
            n += 1
            i = j + 1
            continue
        t = step["t"]
        clock = _fmt_sim_clock_seconds(t)
        summary = step.get("summary")
        if not summary:
            summary = act.replace("\n", " ")
        lines.append(f"{n}. **Sim clock {clock}** — {summary}")
        n += 1
        i += 1
    return lines


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


def format_run_report_markdown(out: dict) -> str:
    """Human-readable Markdown document from the optimizer result dict."""
    lines: list[str] = []
    lines.append("# Northgard Lynx optimizer — run report")
    lines.append("")
    pb_secs = out.get("playbook_sections")
    hzn = float(out.get("assumptions", {}).get("horizon_sec", 1200.0))
    if pb_secs is not None:
        lines.append(format_horizon_playbook_markdown(pb_secs, hzn))
        lines.append("")
    meta = out.get("meta") or {}
    if meta.get("horizon_sec") is not None:
        h = float(meta["horizon_sec"])
        last_t = float(meta.get("last_macro_action_sec", 0))
        passive = float(meta.get("passive_seconds_to_horizon", 0))
        lines.append("> **Run summary**")
        lines.append(">")
        lines.append(
            f"> - **Horizon (scoring clock):** {_fmt_sim_clock_seconds(h)} — `{h:.0f}` s total."
        )
        lines.append(f"> - **Last macro action starts at:** {_fmt_sim_clock_seconds(last_t)}")
        lines.append(
            f"> - **After that:** `{passive:.0f}` s of **passive economy** (production/upkeep, no new builds in the list) until the horizon."
        )
        lines.append(
            "> - **Why `--horizon 3600` did not add more steps:** horizon only extends *evaluation time*. "
            "The search can still return the **same** macro sequence; raising horizon does **not** invent extra builds. "
            "For more actions, raise search budget (`--expansions`, `--rounds`, `--beam`) or change balance/heuristics."
        )
        lines.append("")
    lines.append("## What this is")
    lines.append("")
    lines.append(
        "This is a **macro plan** produced by the simulator’s search: a ordered list of "
        "**builds, expansion, recruits, hunter-path unlocks, and time skips** the model thinks "
        "are good for a Lynx-style opening toward the **horizon** below. "
        "It is *not* a minute-by-minute gameplay guide — times are **simulator seconds** (an abstract clock), "
        "not real-world minutes."
    )
    lines.append("")
    lines.append("**How to read the timeline:** each numbered step is one decision. "
                   "**Sim clock** is where you are in the model after previous steps; "
                   "the text explains what that step *means* in plain language."
    )
    lines.append("")
    lines.append(
        "**Important:** the timeline usually **ends earlier than the horizon**. After the last listed "
        "step, the sim still runs **production, upkeep, and scoring up to the horizon** you set with `--horizon`. "
        "That “gap” is not missing gameplay in the model — it is **passive economy time** with no extra macro actions in this plan."
    )
    lines.append("")
    a = out["assumptions"]
    lines.append("## Assumptions")
    lines.append("")
    lines.append(f"- **Map:** `{a['map']}`")
    lines.append(f"- **Horizon:** {a['horizon_sec']} s (~{a['horizon_sec'] / 60.0:.1f} min)")
    lines.append(f"- **Beam width:** {a['beam_width']}")
    lines.append(f"- **Search rounds:** {a.get('max_rounds', '—')}")
    lines.append(f"- **Max expansions:** {a.get('max_expansions', '—')}")
    lines.append(f"- **GPU batch heuristic:** {a.get('gpu_batch_heuristic', True)}")
    lines.append("")
    lines.append("## Scores")
    lines.append("")
    sc = out.get("score", {})
    lines.append(f"- **Mean benchmark score:** {sc.get('mean_benchmark_score', '—')}")
    lines.append(f"- **Heuristic score:** {sc.get('heuristic_score', '—')}")
    lines.append("")
    lines.append("## Action timeline")
    lines.append("")
    if not out.get("timeline"):
        lines.append("*No actions in sequence.*")
    else:
        lines.extend(_format_timeline_markdown_lines(out["timeline"]))
    lines.append("")
    meta = out.get("meta") or {}
    if meta.get("passive_seconds_to_horizon", 0) > 0.5:
        h = meta.get("horizon_sec", 0)
        last_t = meta.get("last_macro_action_sec", 0)
        lines.append("### Time after the last macro action")
        lines.append("")
        lines.append(
            f"- **Last action ends at:** {_fmt_sim_clock_seconds(last_t)}"
        )
        lines.append(
            f"- **Scoring / final snapshot at:** {_fmt_sim_clock_seconds(h)} (full **horizon**)"
        )
        lines.append(
            f"- **Passive stretch:** `{meta['passive_seconds_to_horizon']:.0f}` s of sim clock with "
            "no further builds/recruits in this plan — income and upkeep still run."
        )
        if float(meta.get("horizon_sec", 0)) < 1800:
            lines.append(
                "- **Longer evaluation window:** `--horizon 3600` ≈ 60 min sim clock (does not by itself add macro steps; see Run summary above)."
            )
        else:
            lines.append(
                "- **More macro actions in the list:** increase `--expansions`, `--rounds`, or `--beam`, or tune `data/` — not `--horizon` alone."
            )
        lines.append("")
    fs = out.get("final_state", {})
    fs_t = fs.get("t", "—")
    lines.append("## Final state snapshot")
    lines.append("")
    lines.append(
        "State of the **economy sim** at the **full horizon** (after the last action plus any "
        "**passive time** to reach the horizon): resources, army, lores, hunter nodes, etc."
    )
    lines.append("")
    if isinstance(fs_t, (int, float)):
        lines.append(f"- **Sim time:** {_fmt_sim_clock_seconds(fs_t)}")
    else:
        lines.append(f"- **Sim time:** {fs_t}")
    res = fs.get("resources", {})
    lines.append("- **Resources:**")
    for k in ("food", "wood", "krowns", "stone", "iron", "lore", "fame", "trophies"):
        if k in res:
            lines.append(f"  - {k}: {res[k]}")
    lines.append(f"- **Population (workers + army):** {fs.get('population', '—')}")
    lines.append(f"- **Housing cap:** {fs.get('housing_cap', '—')}")
    lines.append(f"- **Warband cap:** {fs.get('warband_cap', '—')}")
    army = fs.get("army", {})
    lines.append("- **Army:**")
    for k, v in army.items():
        lines.append(f"  - {k}: {v}")
    lines.append(f"- **Lores:** {', '.join(fs.get('lores', [])) or '—'}")
    lines.append(f"- **Hunter path nodes:** {', '.join(fs.get('hunter_nodes', [])) or '—'}")
    lines.append(f"- **Path complete purchases:** {fs.get('path_complete_purchases', '—')}")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    p = argparse.ArgumentParser(description="Northgard Lynx 20m build optimizer (GPU-batched beam)")
    p.add_argument("--map", default="standard_hostile", help="Map id under data/maps/")
    p.add_argument("--beam", type=int, default=24)
    p.add_argument("--horizon", type=float, default=1200.0, help="Seconds (20 min = 1200)")
    p.add_argument("--rounds", type=int, default=80)
    p.add_argument("--expansions", type=int, default=6000)
    p.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
        help="Output format: human-readable Markdown (default) or JSON for scripts",
    )
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
        timeline.append(
            {
                "t": round(replay.t, 1),
                "action": str(a),
                "summary": describe_action(a),
            }
        )
        apply_action(replay, a)

    last_macro_sec = float(replay.t)
    horizon_sec = float(args.horizon)
    passive_sec = max(0.0, horizon_sec - last_macro_sec)

    action_intervals = compute_action_intervals(args.map, result.actions)
    playbook_sections = build_playbook_sections(action_intervals, horizon_sec)

    out = {
        "assumptions": {
            "map": args.map,
            "horizon_sec": args.horizon,
            "beam_width": args.beam,
            "max_rounds": args.rounds,
            "max_expansions": args.expansions,
            "gpu_batch_heuristic": True,
        },
        "meta": {
            "horizon_sec": horizon_sec,
            "last_macro_action_sec": round(last_macro_sec, 2),
            "passive_seconds_to_horizon": round(passive_sec, 2),
        },
        "action_intervals": action_intervals,
        "playbook_sections": playbook_sections,
        "timeline": timeline,
        "final_state": _state_to_json(result.final_state),
        "score": {
            "mean_benchmark_score": round(result.combat_score, 3),
            "heuristic_score": round(result.heuristic_score, 3),
        },
    }
    if args.format == "json":
        print(json.dumps(out, indent=2))
    else:
        print(format_run_report_markdown(out))


if __name__ == "__main__":
    main()
