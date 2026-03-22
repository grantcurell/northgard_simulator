"""Build a full-horizon 'what to do' playbook from an action sequence (Markdown)."""

from __future__ import annotations

from typing import Any, Dict, List

from .action_labels import describe_action
from .sim import apply_action, initial_state

_PASSIVE_PLAYER_GUIDANCE = (
    "**Sim / optimizer:** no further macro actions are queued in this stretch — production, upkeep, "
    "villager spawn, and lore ticks still run. "
    "**In a real match:** use this time for map awareness, scouting, military micro, trading, "
    "responding to attacks, and anything not modeled here. Keep economy running and avoid idle Town Hall."
)


def compute_action_intervals(map_id: str, actions: list) -> List[Dict[str, Any]]:
    """Each action with [t_start, t_end) on the sim clock (replay applies real durations)."""
    s = initial_state(map_id)
    out: List[Dict[str, Any]] = []
    for a in actions:
        t0 = float(s.t)
        apply_action(s, a)
        t1 = float(s.t)
        out.append(
            {
                "t_start": t0,
                "t_end": t1,
                "action": str(a),
                "summary": describe_action(a),
            }
        )
    return out


def _split_passive_chunk(start: float, end: float, max_chunk_sec: float) -> List[tuple[float, float]]:
    if end <= start + 1e-6:
        return []
    chunks: List[tuple[float, float]] = []
    x = start
    while x < end - 1e-6:
        ce = min(end, x + max_chunk_sec)
        chunks.append((x, ce))
        x = ce
    return chunks


def _fmt_range(start: float, end: float) -> str:
    return f"{_fmt_short(start)}–{_fmt_short(end)}"


def _fmt_short(sec: float) -> str:
    s = int(round(float(sec)))
    m, r = divmod(s, 60)
    return f"{m}:{r:02d}"


def build_playbook_sections(
    intervals: List[Dict[str, Any]],
    horizon_sec: float,
    passive_chunk_sec: float = 240.0,
) -> List[Dict[str, Any]]:
    """
    Cover [0, horizon_sec] with ordered sections: macro instants, macro durations, passive gaps.
    Each section: {kind, start, end, summary?}
    """
    horizon_sec = float(horizon_sec)
    sections: List[Dict[str, Any]] = []
    cursor = 0.0
    eps = 1e-6

    for it in intervals:
        t0 = float(it["t_start"])
        t1 = float(it["t_end"])
        if cursor + eps < t0:
            for ps, pe in _split_passive_chunk(cursor, t0, passive_chunk_sec):
                sections.append({"kind": "passive", "start": ps, "end": pe})
        act_s = str(it.get("action", ""))
        dur = t1 - t0
        if dur <= eps:
            sections.append(
                {
                    "kind": "instant",
                    "start": t0,
                    "end": t1,
                    "summary": it["summary"],
                    "action": act_s,
                }
            )
        elif act_s.strip().startswith("Wait("):
            sections.append(
                {
                    "kind": "wait",
                    "start": t0,
                    "end": t1,
                    "summary": it["summary"],
                    "action": act_s,
                }
            )
        else:
            sections.append(
                {
                    "kind": "timed",
                    "start": t0,
                    "end": t1,
                    "summary": it["summary"],
                    "action": act_s,
                }
            )
        cursor = t1

    if cursor + eps < horizon_sec:
        for ps, pe in _split_passive_chunk(cursor, horizon_sec, passive_chunk_sec):
            sections.append({"kind": "passive", "start": ps, "end": pe})

    return sections


def format_horizon_playbook_markdown(
    sections: List[Dict[str, Any]],
    horizon_sec: float,
) -> str:
    """Markdown: full-horizon player-facing playbook."""
    h = float(horizon_sec)
    title_min = h / 60.0
    title = f"## Full horizon playbook — what to do (0:00 → {_fmt_short(h)}, ~{title_min:.0f} min sim clock)"
    lines = [
        title,
        "",
        "This section **covers the entire scoring window** on the simulator clock. "
        "**Macro** lines are explicit optimizer actions; **passive** lines are stretches with **no extra macro queued** — "
        "the sim still accrues resources and runs rules; you fill the time in-game with micro and map play.",
        "",
    ]

    if not sections:
        lines.append("*No actions — entire horizon is passive economy.*")
        lines.append("")
        lines.append(_PASSIVE_PLAYER_GUIDANCE)
        return "\n".join(lines)

    for sec in sections:
        rng = _fmt_range(sec["start"], sec["end"])
        kind = sec["kind"]
        if kind == "passive":
            lines.append(f"### {rng} — Passive economy (no extra macro in plan)")
            lines.append("")
            lines.append(_PASSIVE_PLAYER_GUIDANCE)
        elif kind == "instant":
            lines.append(f"### At {_fmt_short(sec['start'])} — Instant macro")
            lines.append("")
            lines.append(sec.get("summary", "—"))
            lines.append("")
            lines.append(
                "*Resolve this click when the sim clock hits this moment; then continue.*"
            )
        elif kind == "wait":
            lines.append(f"### {rng} — Pass time (optimizer wait)")
            lines.append("")
            lines.append(sec.get("summary", "—"))
            lines.append("")
            lines.append(
                "*The search inserted idle clock time. In-game you rarely “do nothing” — use it for "
                "scouting, repositioning, or queuing the next task early.*"
            )
        else:
            lines.append(f"### {rng} — Action in progress")
            lines.append("")
            lines.append(sec.get("summary", "—"))
            lines.append("")
            lines.append(
                "*While this runs on the sim clock, keep economy active: workers on tiles, no idle production if possible.*"
            )
        lines.append("")

    lines.append(
        "---"
    )
    lines.append("")
    lines.append(
        "**Note:** Sim clock is **not** guaranteed to match real-world minutes 1:1; it is the model’s "
        "abstract timeline (see `economy.json` for month/second scaling)."
    )
    return "\n".join(lines)
