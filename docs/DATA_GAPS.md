# Data still unknown or calibratable

**Readable checklist (Markdown):** see **[DATA_STATUS.md](DATA_STATUS.md)** — same content as `python3 -m northgard.data_status` (regenerate with `python3 -m northgard.data_status --write`).

Values confirmed by the expert and merged into `data/` and code are summarized in `EXPERT_DATA_REQUEST_ANSWERS.md` and in JSON `*_source` / `*_note` fields.

**Developer rule:** If an item is unknown, conflicting, or not publicly sourced, keep it as a parameter or TODO and treat the answer as **unknown / not publicly sourced; do not guess** (not filler).

## Sourced in code (latest pass)

| ID | Topic | Where |
|----|--------|--------|
| B1 | House 50 wood / 10 kröwns; build **13** in-game days (northgard.wiki snippets; full page may 403) | `data/buildings.json` + `seconds_per_game_day` |
| B1 | Build times (days): Woodcutter 13, Scout Camp 8, Marketplace 25, Archery 20, Forge 20, Town Hall **build** 10 | `data/buildings.json` |
| B1 | Town Hall **upgrade** cost 100 / 50 / 10 stone; upgrade effects per Fandom (growth, cap, advanced buildings) | `data/buildings.json` |
| V1 | Happiness-page spawn formula — **community wiki candidate**, not official data dump | `spawn_model`: `happiness_page_candidate` in `economy.json` |
| P4 | Hunting Trophies **per-kill** (official Fandom) | `data/trophy_income_per_kill.json` |
| K2 | Supply malus table + yearly decay; Wild Hunter removes malus for Lynx military (Fandom) | `data/supply_penalty.json`, `combat_eval` |

## Partial public facts (do not over-interpret)

| ID | Topic | Where |
|----|--------|--------|
| S2 | Optional **provisional** starting happiness **+1** (Fandom derivation: +2 territory, −1 pop malus pop 1–10 Normal) — **not** a published MP start row | `economy.json` `default_happiness`, `starting_happiness_note` |
| L1 | Fandom **aggregate** lore: full tree **27,450** lore; last knowledge **4,940** — not a per-node schedule | `data/lore_costs.json` → `fandom_lore_aggregate_facts` |
| L2 | Lynx **lore names / branch order** on clan page — **not** a machine prerequisite graph | `data/lore_costs.json` → `lynx_lore_names_order_public_hint` |
| C3 | **Partial** slot rules (ordinary tiles 2–4 range, main tile 5 incl. TH, Develop +1, swamp ~2) | `data/zone_building_slots_partial.json` |

## Still unknown / placeholder (do not guess)

| ID | Topic | Status |
|----|--------|--------|
| S1 | Default Lynx MP starting villagers / food / wood / kröwns | `starting_resources_status` |
| S2 | Direct published “starting happiness = X” row | Use provisional inference only if you accept the derivation; see `economy.json` |
| V2 | Brundr/Kaelinn vs warchief-style housing / upkeep / warband | Not modeled explicitly |
| M1 | Numeric Tracker upkeep | `tracker_military_upkeep` placeholders |
| L1 | **Per-node** lore prices | Placeholder map + aggregate facts only |
| L2 | **Exact** prerequisite graph | Not enforced in sim |
| C2 | Standard neutral colonization **duration** | `colonization_duration_seconds_unknown_placeholder` |
| C3 | **Full** per-zone-type slot table | Partial JSON only |
| N1 | Clear-time / HP benchmarks | `clearing.py` — measured parameters |
| N2 | Per-clear trophies | Sum per-kill × composition; Great Hunt rows only when unlocked |
| K1 | Hero attack speeds | Calibratable |
| K3 | Double Shot frequency | `clustering` parameter |
| K4 | Benchmark armies | `enemy_benchmarks.json` `_meta` |
| TH | Town Hall **upgrade** duration | Placeholder seconds |

**Documentation conflict — Caring Siblings:** Brundr unit page **+20%** vs Path of the Hunter **+30%**. Code uses **`hunter_path.json`** (+30%) with `source_conflict_note` — Path page treated as stronger for this mechanic.

When you fill a gap, prefer **`data/*.json`** and short notes here with patch/version.
