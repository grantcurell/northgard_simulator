# Northgard Lynx optimizer — how it works

This project is a **small, table-driven model** of a Northgard match focused on one question: **what sequence of macro decisions (builds, lore, expansion, recruits) yields the strongest Lynx army around the 20-minute mark**, as scored by a simple combat benchmark suite.

It is **not** a full game simulation. Think of it as a **spreadsheet with rules**: resources update over time, actions cost resources and time, and the optimizer searches among legal actions.

---

## The big picture

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  data/*.json │ ──▶ │  GameState       │ ──▶ │  Combat score   │
│  (costs,    │     │  + advance time  │     │  (benchmarks)   │
│   caps)     │     │  + apply actions │     └────────▲────────┘
└─────────────┘     └────────┬─────────┘              │
                             │                        │
                             ▼                        │
                    ┌─────────────────┐              │
                    │  Beam search    │──────────────┘
                    │  (GPU batch     │   picks sequences
                    │   scoring)      │   that maximize score
                    └─────────────────┘
```

1. **Data** — Numbers live in JSON (`data/`) so you can edit costs and effects without touching Python logic.
2. **Simulator** — `GameState` holds time, resources, units, zones, lores, and hunter path. **Advancing time** applies production and upkeep; **actions** apply instant costs and time skips (e.g. build duration).
3. **Combat** — At the end of the horizon, **no real fight is simulated**. A separate **evaluator** turns the final army + buffs into a scalar score against fixed “benchmark” enemy armies (`data/enemy_benchmarks.json`).
4. **Search** — **Beam search** explores many action sequences, keeps the best partial paths per a heuristic, then **finalizes** states to the 20-minute clock and ranks by mean benchmark score. **Batch heuristic and top-k scoring run on the GPU** via **CuPy**; importing `northgard.gpu_ops` **fails immediately** if CUDA is missing or kernels cannot execute. The macro simulator (state updates, actions) still runs on the CPU in Python.

---

## Conceptual model: discrete time, not a game loop

Northgard does not need to be modeled frame-by-frame. The code follows an **event-style** idea:

- **Between events**, resources change with **net flows** (food from villagers, kröwns from Town Hall, etc.), scaled by a configurable “month length” in seconds.
- **Actions** (build, recruit, colonize, …) **spend resources** and **advance the clock** by a duration (build time) or apply **instantly** (some recruits, lore unlocks).

So the simulator is **deterministic** given a fixed action list: same inputs → same final state.

---

## Main Python modules (mental map)

| Area | Module(s) | Role |
|------|-----------|------|
| **State** | `northgard/state.py` | `GameState`, `Resources`, `UnitCounts`, per-zone buildings. Everything the sim needs to know at time *t*. |
| **Economy** | `northgard/economy.py` | Integrates **flows** over time (`advance_to`), villager spawn scheduling, winter/month flags. |
| **Rules** | `northgard/buildings.py`, `recruitment.py`, `population.py`, `lore.py`, `trophies.py` | Housing, warband cap, tracker cost ladder, spawn interval formula, lore multipliers, trophy thresholds. |
| **Map** | `northgard/map_graph.py`, `data/maps/*.json` | Zones, neighbors, who owns a tile, building slots. |
| **Actions** | `northgard/actions.py`, `northgard/sim.py` | **What** can be done (`Build`, `RecruitTracker`, …) and **legality** + **effects** (`legal_actions`, `apply_action`). |
| **PvE stub** | `northgard/clearing.py` | Rough **clear time** and **trophies** for neutral packs; not tactical combat. |
| **Combat scoring** | `northgard/combat_eval.py`, `northgard/scoring.py` | Turns **final state** into benchmark scores (effective DPS-style value + simple win heuristic). |
| **GPU batch** | `northgard/gpu_ops.py` | Encodes features on the host, then scores **batches** on the GPU (heuristic + combat proxy, top-k). **Requires a working CUDA device** — no CPU fallback. |
| **Search** | `northgard/search/beam_search.py`, `heuristics.py` | Beam search loop; top-k selection of expanded states. |
| **CLI** | `cli/run_optimizer.py` | Loads map + benchmarks, runs beam search, prints JSON (timeline + final state + score). |

The top-level **`search/`** package only **re-exports** `northgard.search` for import convenience.

---

## Data flow

- **`data_loader.py`** resolves paths relative to the package and loads `data/*.json`.
- Changing **balance** should start in **`data/`** (and documented expert answers in `docs/EXPERT_DATA_REQUEST.md` when you replace placeholders).

---

## Running it

**Prerequisite:** an **NVIDIA GPU** with drivers, CUDA libraries compatible with your **CuPy** wheel, and a successful probe kernel on device 0. If CuPy cannot import or run on the GPU, the optimizer **exits with an error** (no silent CPU fallback).

From the **repository root** (this directory), with dependencies installed:

```bash
python -m pytest tests/ -q
python cli/run_optimizer.py --beam 24 --rounds 60 --expansions 6000
```

Use a virtualenv and `pip install -r requirements.txt` as needed (`cupy-cuda12x` or the variant matching your CUDA version).

---

## What to trust vs. calibrate

- **Documented** costs and percentages from the design docs are **wired in** where they exist in JSON.
- **Unknown** timings (e.g. exact build seconds), **spawn rates**, **lore point prices**, and **combat** beyond simple buffs are **placeholders or tunable**; see `docs/EXPERT_DATA_REQUEST.md` for the gap list.

The README is the **conceptual** map; the **authoritative list of invented values** is the expert request + inline comments in `economy.json` / `sim.py` where still approximate.

---

## Further reading

- `docs/build_doc.md` — design philosophy (stock-flow, event-driven, what to model).
- `docs/starting_point.md` — original handoff (structure, milestones, JSON shapes).
- `docs/EXPERT_DATA_REQUEST.md` — original questions to a Northgard expert.
- `docs/EXPERT_DATA_REQUEST_ANSWERS.md` — expert-sourced values (merged into `data/` where applicable).
- `docs/DATA_GAPS.md` — values still unknown or calibratable (**do not guess**).
