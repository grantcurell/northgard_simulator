"""Report items that remain unknown or not publicly sourced (do not guess)."""

from __future__ import annotations

import argparse
from pathlib import Path

# IDs align with expert DATA_GAPS / request answers; message is part of the contract.
UNKNOWN_OR_UNSOURCED: list[tuple[str, str]] = [
    ("S1", "Default normal Lynx MP starting villagers and food/wood/kröwns — unknown / not publicly sourced; do not guess."),
    ("S2", "No direct published MP starting-happiness row — optional provisional net +1 in `economy.json` (Fandom Happiness derivation); not authoritative."),
    ("V1_calibration", "Happiness-page spawn formula — community wiki candidate, not official game data; use `happiness_page_candidate` mode only as calibration."),
    ("V2", "Brundr/Kaelinn housing, population limit, warband, upkeep vs warchief-style rules — unknown / not publicly sourced; do not guess."),
    ("M1", "Per-unit Tracker food/wood/kröwn upkeep breakdown — unknown / not publicly sourced; placeholders only."),
    ("L1", "Per-node lore point prices — unknown; Fandom aggregate totals exist in `data/lore_costs.json` (not a per-node schedule)."),
    ("L2", "Exact lore prerequisite graph — unknown; Lynx name order hint only in `lore_costs.json`."),
    ("C2", "Standard neutral-zone colonization duration — unknown / not publicly sourced; do not infer from special cases."),
    ("C3", "Full authoritative max building slots by zone type — partial rules in `zone_building_slots_partial.json`; do not guess beyond."),
    ("N1", "Neutral clear times / HP-loss benchmarks — unknown / not publicly sourced; measured or simulated parameters."),
    ("N2", "Per-clear trophy totals — derive from per-kill × composition + Great Hunt state; no universal per-clear table."),
    ("K1", "Attack speed for Mielikki, Brundr, Kaelinn — unknown / not publicly sourced; do not guess."),
    ("K3", "Double Shot targeting frequency / uptime — model assumption (`clustering`); not a published formula."),
    ("K4", "Authoritative 20-minute benchmark armies — `enemy_benchmarks.json` is a modeler test harness, not game data."),
    ("TH_upgrade_time", "Town Hall upgrade duration — unknown / not publicly sourced (build time is sourced separately)."),
    ("House_upgrade_time", "House upgrade build time — calibratable placeholder."),
]

# Kept in sync with docs/DATA_GAPS.md “Sourced in code” section.
SOURCED_IN_SIMULATOR: list[tuple[str, str, str]] = [
    ("B1", "House cost (50 wood / 10 kröwns) and 13-day build (northgard.wiki snippets / search; 403 on full page in some environments)", "`data/buildings.json`, `economy.json`"),
    ("B1", "Build times (days): Woodcutter 13, Scout Camp 8, Marketplace 25, Archery 20, Forge 20, Town Hall build 10", "`data/buildings.json`"),
    ("B1", "Town Hall upgrade cost 100 wood / 50 kröwns / 10 stone + listed upgrade effects (Fandom Town Hall)", "`data/buildings.json`"),
    ("V1", "Optional Happiness-page spawn formula (candidate)", "`economy.json` → `spawn_model`: `happiness_page_candidate`"),
    ("P4", "Hunting Trophies per-kill (Fandom)", "`data/trophy_income_per_kill.json`"),
    ("K2", "Supply malus by tile distance + yearly decay; Wild Hunter removes for Lynx military (Fandom)", "`data/supply_penalty.json`, `combat_eval`"),
]

# Partially sourced: public facts that do not replace full schedules/graphs.
PARTIAL_PUBLIC_FACTS: list[tuple[str, str, str]] = [
    ("S2", "Provisional starting happiness +1 inference (territory +2, Normal pop malus −1 for pop 1–10)", "`economy.json` `default_happiness` + `starting_happiness_note`"),
    ("L1", "Fandom aggregate lore costs: full tree 27,450; last knowledge 4,940 (not per-node schedule)", "`data/lore_costs.json` → `fandom_lore_aggregate_facts`"),
    ("L2", "Lynx lore names / branch order (hint only, not prerequisite graph)", "`data/lore_costs.json` → `lynx_lore_names_order_public_hint`"),
    ("C3", "Partial slot rules (ordinary tiles 2–4 range, main tile 5 incl. TH, Develop +1, swamp ~2)", "`data/zone_building_slots_partial.json`"),
]

def _repo_docs_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "docs"


def format_status_report_plain() -> str:
    """Legacy plain-text lines (for quick grep / logs)."""
    lines = ["Northgard simulator — data status (unknown / not publicly sourced; do not guess)", ""]
    for item_id, msg in UNKNOWN_OR_UNSOURCED:
        lines.append(f"  [{item_id}] {msg}")
    return "\n".join(lines)


def format_markdown_report() -> str:
    """Human-readable Markdown document: follow top to bottom."""
    lines: list[str] = []
    lines.append("# Northgard simulator — data status")
    lines.append("")
    lines.append(
        "This document lists **what the simulator treats as unknown or not publicly sourced** "
        "(do not guess), **partial public facts**, and **what is wired in from wiki / expert pass** with file pointers. "
        "Regenerate the copy under `docs/DATA_STATUS.md` after changing `northgard/data_status.py`."
    )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Developer rule")
    lines.append("")
    lines.append(
        "> If an item is unknown, conflicting, or not publicly sourced, keep it as a **parameter or TODO** "
        "and treat the answer as **unknown / not publicly sourced; do not guess** — not filler."
    )
    lines.append("")
    lines.append("## How to regenerate this file")
    lines.append("")
    lines.append("From the repository root:")
    lines.append("")
    lines.append("```bash")
    lines.append("python3 -m northgard.data_status --write")
    lines.append("```")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 1. Sourced in the simulator (with pointers)")
    lines.append("")
    lines.append("| ID | Topic | Where |")
    lines.append("|----|--------|--------|")
    for item_id, topic, where in SOURCED_IN_SIMULATOR:
        safe_topic = topic.replace("|", "\\|")
        safe_where = where.replace("|", "\\|")
        lines.append(f"| {item_id} | {safe_topic} | {safe_where} |")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 1a. Partial public facts (hints / aggregates — not full schedules)")
    lines.append("")
    lines.append("| ID | Topic | Where |")
    lines.append("|----|--------|--------|")
    for item_id, topic, where in PARTIAL_PUBLIC_FACTS:
        safe_topic = topic.replace("|", "\\|")
        safe_where = where.replace("|", "\\|")
        lines.append(f"| {item_id} | {safe_topic} | {safe_where} |")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 2. Unknown / not publicly sourced (checklist)")
    lines.append("")
    lines.append("| ID | Description |")
    lines.append("|----|-------------|")
    for item_id, msg in UNKNOWN_OR_UNSOURCED:
        safe_msg = msg.replace("|", "\\|")
        lines.append(f"| `{item_id}` | {safe_msg} |")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 3. Related documentation")
    lines.append("")
    lines.append("- [DATA_GAPS.md](DATA_GAPS.md) — table of gaps vs sourced items + developer rule")
    lines.append("- [EXPERT_DATA_REQUEST_ANSWERS.md](EXPERT_DATA_REQUEST_ANSWERS.md) — expert merge notes")
    lines.append("")
    return "\n".join(lines)


def write_markdown_to_docs(path: Path | None = None) -> Path:
    """Write `format_markdown_report()` to `docs/DATA_STATUS.md` (default)."""
    if path is None:
        path = _repo_docs_dir() / "DATA_STATUS.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(format_markdown_report(), encoding="utf-8")
    return path


def print_status_report() -> None:
    print(format_markdown_report())


def _main() -> None:
    import sys

    ap = argparse.ArgumentParser(description="Print or write data status as Markdown.")
    ap.add_argument(
        "--plain",
        action="store_true",
        help="Print legacy plain-text lines instead of Markdown",
    )
    ap.add_argument(
        "--write",
        action="store_true",
        help="Write Markdown to docs/DATA_STATUS.md (quiet on stdout; path on stderr)",
    )
    ap.add_argument(
        "--output",
        type=str,
        default=None,
        help="With --write, custom output path (default: docs/DATA_STATUS.md)",
    )
    ap.add_argument(
        "--also-print",
        action="store_true",
        help="With --write, also print the full Markdown to stdout",
    )
    args = ap.parse_args()
    if args.write:
        out = Path(args.output) if args.output else None
        p = write_markdown_to_docs(out)
        print(f"Wrote {p}", file=sys.stderr)
    if not args.write or args.also_print:
        if args.plain:
            print(format_status_report_plain())
        else:
            print(format_markdown_report())


if __name__ == "__main__":
    _main()
