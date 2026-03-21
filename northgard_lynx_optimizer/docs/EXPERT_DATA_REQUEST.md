# Northgard expert data request — Lynx 20-minute lethality optimizer

This document lists **information we still need** to replace placeholders in the table-driven simulator and beam-search optimizer. Where possible, cite **patch version**, **game mode** (e.g. Ragnarok, FFA), and **source** (wiki page, in-game tooltip, or your own measurement).

Please answer **per section**; “unknown / not exposed” is a valid answer so we can keep parameters explicit and calibratable.

---

## 1. Time and economy scaling

| ID | Question | Why we need it |
|----|----------|----------------|
| T1 | How do **in-game months** (or UI “ticks”) map to **real time** in a standard multiplayer match? If variable, give a typical value or range. | We convert “+3 kröwns per month”, merchant rates, lore/month, etc. to per-second flows. |
| T2 | **Season / winter** timing: which months are winter, how long is a year in months, and does the match **start** in a fixed season? | Drives villager 4 vs 2.4 food, firewood, winter combat penalties. |
| T3 | Exact **Town Hall** passive: is “+3 kröwns” per month, per tick, or something else? Same for **upgraded Town Hall** kröwn production if it changes. | Core kröwn flow. |

---

## 2. Starting conditions (match start)

| ID | Question | Why we need it |
|----|----------|----------------|
| S1 | Default **starting villagers**, **starting food / wood / kröwns** (and other resources if any) for a typical Lynx spawn. | Initial state at t = 0. |
| S2 | **Happiness** at game start (or formula from buildings/lore at 0:00). | Gates villager spawning (happiness ≥ 0). |
| S3 | Confirm **housing**: Town Hall = 6 at start; anything else affecting cap before first House? | `housing_cap` vs population. |

---

## 3. Villager spawn (Town Hall)

The public docs describe **qualitative** rules (happiness, population slow spawn, Recruitment +25%, upgraded TH +20% growth). We use a **calibrated formula**, not the real one.

| ID | Question | Why we need it |
|----|----------|----------------|
| V1 | If you can: **measured time between villager spawns** at several points (low vs high population, with/without Recruitment, with/without TH upgrade, different happiness). Even 2–3 data points help fit `spawn_interval = f(happiness, population, bonuses)`. | Replace placeholder coefficients. |
| V2 | Confirm whether **spawn pauses** when `population >= housing_cap` (and whether military units count the same as villagers for cap). | Avoid invalid states in the sim. |

---

## 4. Buildings — costs, build times, prerequisites

For each row, we need **wood / kröwns / stone / iron** (as in game), **build time**, **upkeep** (kröwns per tick/month if applicable), and **prerequisites** (e.g. TH upgrade before other upgrades).

**Priority buildings for this project:** Town Hall, House (normal + upgraded), Woodcutter (or equivalent), Scout Camp if relevant, Marketplace, Archery Range (normal + upgraded), Forge (normal + upgraded).

| ID | Question | Why we need it |
|----|----------|----------------|
| B1 | Full **cost and build time** table for the above (including **Marketplace** placement cost — not only merchant slot numbers). | Actions must deduct the right resources and durations. |
| B2 | **House upgrade**: cost, build time, exact **+housing** (we use +5 base, +3 from upgrade → 8 total for an upgraded house — confirm). | Housing and happiness (“better houses” penalty removal). |
| B3 | **Town Hall upgrade**: full costs, build time, confirm **+2 population cap** and **+20% population growth** (and whether kröwn production changes). | Lore/econ timing. |
| B4 | **Archery Range** and **upgrade**: confirm warband (+2 / +1), Tracker attack +5% per upgraded range, and that **Mielikki / Brundr / Kaelinn** are recruited here with listed costs. | Military and Lynx-specific. |
| B5 | **Forge** upgrade: confirm **second smith** and **+20% forging speed**; costs/times for build and upgrade. | If we model tools/forging later. |
| B6 | Any **global** building upkeep rule (per month, per building type, what happens if unpaid). | Kröwn drain and “greedy army” tradeoff. |

---

## 5. Workers and gathering

| ID | Question | Why we need it |
|----|----------|----------------|
| W1 | Confirm **villager** gathering rates: **4** food (summer) and **2.4** (winter) — unit of measure (food per second per villager vs per month). | Already in wiki; need **time base** tied to T1. |
| W2 | **Woodcutter** (or villager on wood): summer vs winter **wood** rates. | We invented woodcutter rates in `units.json`. |
| W3 | **Merchant** kröwn rate per merchant (2 kröwns — per what time unit?). | Marketplace economy. |
| W4 | **Miner** stone (and iron if applicable) rates if we expand to mining camps. | Optional; currently placeholder. |

---

## 6. Military upkeep and population rules

| ID | Question | Why we need it |
|----|----------|----------------|
| M1 | **Trackers** (and other military): **food** and **wood** consumption rates while idle; **kröwn** upkeep if any. | We used invented per-second upkeep. |
| M2 | **Warband**: confirm Archery Range caps (+2 base, +3 upgraded) stacking with **multiple ranges**. | `warband_cap` vs recruits. |
| M3 | **Warchiefs / Mielikki / Brundr / Kaelinn**: confirm **no food/wood** for Mielikki-type, **no population** count for warchief — and whether **Brundr/Kaelinn** consume housing or upkeep differently. | Recruitment legality and economy. |
| M4 | **Tracker cost ladder**: confirm formula `25 + 5*(n-1)` per unit and that **Archery Mastery** makes the **first Tracker free** and **halves Archery Range upgrade cost** (which resources halved?). | Exact kröwn costs. |

---

## 7. Lore — costs and unlock rules

We have **effect magnitudes** from the handoff; we still need **lore point costs** and **unlock order rules**.

| ID | Question | Why we need it |
|----|----------|----------------|
| L1 | **Lore price** (lore points) for each node we model: Sharp Axes, Colonization, Recruitment, Hearthstone, Shiny Happy People, Weaponsmith, Archery Mastery, Feeling Safe, Spoils of Plenty, etc. | Replace invented `LORE_COSTS`. |
| L2 | Are there **clan-specific** costs or **prerequisites** (e.g. number of lores before Weaponsmith)? | Search legality. |
| L3 | **Lore generation**: base rate from **non-combat** sources (villagers, Silo, other) in points per month (or per tick). | `resources.lore` integration. |

---

## 8. Colonization and map

| ID | Question | Why we need it |
|----|----------|----------------|
| C1 | **Base food cost** to colonize a neutral tile (before Colonization lore −30%). Does it vary by tile type or distance? | Replace invented `colonize_base_food`. |
| C2 | **Time** to complete colonization (if any) or if it is instant upon payment. | Event timing. |
| C3 | For our **map JSON**: max **building slots** per zone type, and whether **shore / stone / forest** tags change costs or yields. | Map graphs and expansion value. |

---

## 9. Lynx — Hunting trophies and Path of the Hunter

| ID | Question | Why we need it |
|----|----------|----------------|
| P1 | Confirm **cumulative trophy thresholds** for unlock slots: 30, 80, 130, … (full list). | Already documented; confirm unchanged on current patch. |
| P2 | For each **purchasable node**: does buying consume **trophies**, only **gate** on lifetime trophies, or both? | Economy of Path nodes. |
| P3 | **Path Complete**: exact **cost** (trophies? fame? repeat scaling) and confirm **+5%** attack speed, range, move speed **per purchase** when the condition is met. | Repeat purchases. |
| P4 | **Trophy income**: typical trophies per **wolf / deer / draugr / bear** (or formula). | Trophy stock for unlocks and clears. |
| P5 | **Fame** 200 / 500: confirm unlocks (**Mythical Lure**, **Oskoreia**) and any **numeric** effects we should model (feast discount formula, wave scaling). | Fame breakpoints. |

---

## 10. Neutral clears (PvE)

We use a **compositional approximation** (clear time, trophies, losses). We need either **real timings** or **your tuned parameters**.

| ID | Question | Why we need it |
|----|----------|----------------|
| N1 | Typical **time to clear** common early camps (2 wolves, 3 draugr, etc.) with **N Trackers** or **Trackers + heroes** — even rough ranges. | Replace `clear_difficulty` and formulas in `clearing.py`. |
| N2 | **Trophies** granted per clear type (and whether it scales with difficulty). | Trophy progression. |
| N3 | Whether **winter** or **zone type** changes clear speed or losses for neutrals. | Winter benchmark. |

---

## 11. Combat model (for benchmark scoring at 20:00)

We do **not** need a full engine clone; we need **enough** to rank build orders consistently.

| ID | Question | Why we need it |
|----|----------|----------------|
| K1 | **Brundr** and **Kaelinn** (and **Mielikki**): current **HP, attack, defense** (and attack speed if DPS matters). | Replace placeholder hero numbers in `combat_eval.py`. |
| K2 | **Winter attack penalty** for military (%) without Wild Hunter; **supply** malus if we model territory edge. | `winter_attack_mult` etc. |
| K3 | **Double Shot**: confirm secondary hit **30%** damage and how often it applies (e.g. vs clumped units — we use a **clustering** parameter 0–1). | Expected DPS multiplier. |
| K4 | Optional: **2–3 benchmark enemy compositions** you consider representative for “20 min army check” (unit types and counts). | Replace fabricated `enemy_benchmarks.json`. |

---

## 12. Patch and mode metadata

| ID | Question | Why we need it |
|----|----------|----------------|
| X1 | Game **version / patch** and whether numbers differ in **Ranked vs Custom**. | Versioning our data tables. |
| X2 | Anything **Lynx-specific** that changed recently (Path, trophy ladder, unit costs). | Avoid stale wiki. |

---

## How to return answers

Preferred formats (any one is fine):

1. **Filled tables** (copy section headings, add a column “Answer / value”).
2. **Spreadsheet** with columns: `ID`, `value`, `notes`, `source`.
3. **Screenshots** of in-game tooltips for costs/times (with patch noted).

We will map your answers into `data/*.json` and remove or mark remaining `calibration` fields explicitly.

Thank you — this closes the gap between “documented design” and **game-accurate** parameters for the optimizer.
