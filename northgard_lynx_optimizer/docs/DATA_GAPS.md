# Data still unknown or calibratable

Values confirmed by the expert and merged into `data/` and code are summarized in `EXPERT_DATA_REQUEST_ANSWERS.md` (calendar, tick rates, colonization tables, upkeep, hero stats, winter combat penalties, etc.).

These items were marked **unknown / not exposed / do not guess** in that document. The simulator keeps **explicit placeholders** or **TODO** behavior until you supply values.

| ID | Topic | Status |
|----|--------|--------|
| S1 | Default starting **villagers**, **food / wood / kröwns** (normal Lynx MP) | Unknown — `economy.json` still uses placeholder starts |
| S2 | **Starting happiness** numeric | Unknown — `default_happiness` is a placeholder |
| V1 | Exact **villager spawn** formula / coefficients | Calibratable — `spawn_calibration` in `economy.json` |
| V2 | **Brundr / Kaelinn** housing & upkeep vs warchief rules | Unknown — code does not special-case |
| B1 | **House** base **wood/kröwn** cost & **build time** | Not found in wiki excerpts — table values retained |
| B1 | Most building **build times** (seconds) | Unknown — `build_time_sec` entries remain placeholders |
| C2 | **Colonization** completion **time** | Unknown — `sim.py` still uses a fixed delay |
| C3 | Full **max building slots per zone type** | Unknown — map JSON uses ad hoc capacities |
| L1 | **Lore point price** per node | Unknown — `lore.py` `LORE_COSTS` still placeholder |
| L2 | **Lore prerequisite graph** | Unknown — not enforced in sim |
| M1 | Numeric **military food/wood/kröwn upkeep** per unit | Calibratable — simplified upkeep remains |
| P4 | **Trophies per creature** (wolf, deer, …) | Unknown — clearing uses stub trophies |
| N1–N2 | **Neutral clear time** & **trophy** tables | Calibratable — `clearing.py` |
| K1 | **Attack speed** for heroes | Unknown |
| K2 | Numeric **supply malus** | Unknown — not modeled |
| K3 | Double Shot **targeting frequency** | Model uses **clustering** parameter only |
| K4 | **Authoritative benchmark armies** | `enemy_benchmarks.json` is a **test harness**, not game data |
| — | **House upgraded** upkeep (if different from base house) | Not isolated in wiki excerpt — may match maintenance table later |

**Documentation conflict:** Brundr/Kaelinn pages vs Path of the Hunter for **Caring Siblings** (+20% vs +30%). Code uses **`hunter_path.json`** (+30%) per expert guidance.

When you fill a gap, prefer **`data/*.json`** and short notes here with patch/version.
