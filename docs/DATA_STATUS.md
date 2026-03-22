# Northgard simulator — data status

This document lists **what the simulator treats as unknown or not publicly sourced** (do not guess), **partial public facts**, and **what is wired in from wiki / expert pass** with file pointers. Regenerate the copy under `docs/DATA_STATUS.md` after changing `northgard/data_status.py`.

---

## Developer rule

> If an item is unknown, conflicting, or not publicly sourced, keep it as a **parameter or TODO** and treat the answer as **unknown / not publicly sourced; do not guess** — not filler.

## How to regenerate this file

From the repository root:

```bash
python3 -m northgard.data_status --write
```

---

## 1. Sourced in the simulator (with pointers)

| ID | Topic | Where |
|----|--------|--------|
| B1 | House cost (50 wood / 10 kröwns) and 13-day build (northgard.wiki snippets / search; 403 on full page in some environments) | `data/buildings.json`, `economy.json` |
| B1 | Build times (days): Woodcutter 13, Scout Camp 8, Marketplace 25, Archery 20, Forge 20, Town Hall build 10 | `data/buildings.json` |
| B1 | Town Hall upgrade cost 100 wood / 50 kröwns / 10 stone + listed upgrade effects (Fandom Town Hall) | `data/buildings.json` |
| V1 | Optional Happiness-page spawn formula (candidate) | `economy.json` → `spawn_model`: `happiness_page_candidate` |
| P4 | Hunting Trophies per-kill (Fandom) | `data/trophy_income_per_kill.json` |
| K2 | Supply malus by tile distance + yearly decay; Wild Hunter removes for Lynx military (Fandom) | `data/supply_penalty.json`, `combat_eval` |

---

## 1a. Partial public facts (hints / aggregates — not full schedules)

| ID | Topic | Where |
|----|--------|--------|
| S2 | Provisional starting happiness +1 inference (territory +2, Normal pop malus −1 for pop 1–10) | `economy.json` `default_happiness` + `starting_happiness_note` |
| L1 | Fandom aggregate lore costs: full tree 27,450; last knowledge 4,940 (not per-node schedule) | `data/lore_costs.json` → `fandom_lore_aggregate_facts` |
| L2 | Lynx lore names / branch order (hint only, not prerequisite graph) | `data/lore_costs.json` → `lynx_lore_names_order_public_hint` |
| C3 | Partial slot rules (ordinary tiles 2–4 range, main tile 5 incl. TH, Develop +1, swamp ~2) | `data/zone_building_slots_partial.json` |

---

## 2. Unknown / not publicly sourced (checklist)

| ID | Description |
|----|-------------|
| `S1` | Default normal Lynx MP starting villagers and food/wood/kröwns — unknown / not publicly sourced; do not guess. |
| `S2` | No direct published MP starting-happiness row — optional provisional net +1 in `economy.json` (Fandom Happiness derivation); not authoritative. |
| `V1_calibration` | Happiness-page spawn formula — community wiki candidate, not official game data; use `happiness_page_candidate` mode only as calibration. |
| `V2` | Brundr/Kaelinn housing, population limit, warband, upkeep vs warchief-style rules — unknown / not publicly sourced; do not guess. |
| `M1` | Per-unit Tracker food/wood/kröwn upkeep breakdown — unknown / not publicly sourced; placeholders only. |
| `L1` | Per-node lore point prices — unknown; Fandom aggregate totals exist in `data/lore_costs.json` (not a per-node schedule). |
| `L2` | Exact lore prerequisite graph — unknown; Lynx name order hint only in `lore_costs.json`. |
| `C2` | Standard neutral-zone colonization duration — unknown / not publicly sourced; do not infer from special cases. |
| `C3` | Full authoritative max building slots by zone type — partial rules in `zone_building_slots_partial.json`; do not guess beyond. |
| `N1` | Neutral clear times / HP-loss benchmarks — unknown / not publicly sourced; measured or simulated parameters. |
| `N2` | Per-clear trophy totals — derive from per-kill × composition + Great Hunt state; no universal per-clear table. |
| `K1` | Attack speed for Mielikki, Brundr, Kaelinn — unknown / not publicly sourced; do not guess. |
| `K3` | Double Shot targeting frequency / uptime — model assumption (`clustering`); not a published formula. |
| `K4` | Authoritative 20-minute benchmark armies — `enemy_benchmarks.json` is a modeler test harness, not game data. |
| `TH_upgrade_time` | Town Hall upgrade duration — unknown / not publicly sourced (build time is sourced separately). |
| `House_upgrade_time` | House upgrade build time — calibratable placeholder. |

---

## 3. Related documentation

- [DATA_GAPS.md](DATA_GAPS.md) — table of gaps vs sourced items + developer rule
- [EXPERT_DATA_REQUEST_ANSWERS.md](EXPERT_DATA_REQUEST_ANSWERS.md) — expert merge notes
