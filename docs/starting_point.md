Here’s the handoff spec I’d give your Python developer.

The goal is not to recreate Northgard perfectly. The goal is to build a deterministic 0:00→20:00 simulator for Lynx that preserves the decisions that change 20-minute combat strength: economy, expansion, population growth, lore timing, trophy timing, unit recruitment, camp count/upgrades, and a final combat evaluator. Town Hall villager spawning, housing, villager base output, Tracker stats/cost ladder, Archery Range cap math, Lynx lore, Path of the Hunter bonuses, fame breakpoints, and winter penalties are all documented and should be treated as source-of-truth inputs. ([Northgard Wiki][1])

Use an event-driven simulation, not a frame loop. In this problem, the state only changes meaningfully when something completes or a threshold is crossed: villager spawn, colonization, building completion, lore unlock, trophy unlock, camp upgrade completion, forge completion, recruitment, or clear completion. The game’s resource UI is also discrete by time interval, and a month is six UI intervals, so an event queue is a natural fit. ([Northgard Wiki][2])

Project structure

```text
northgard_simulator/   (repo root)
  data/
    units.json
    buildings.json
    lores.json
    hunter_path.json
    fame.json
    economy.json
    maps/
      standard_hostile.json
      rich_shore.json
      no_shore_hostile.json
    enemy_benchmarks.json

  northgard/
    __init__.py
    state.py
    events.py
    actions.py
    map_graph.py
    economy.py
    population.py
    buildings.py
    recruitment.py
    lore.py
    trophies.py
    clearing.py
    combat_eval.py
    sim.py
    scoring.py

  search/
    beam_search.py
    heuristics.py
    constraints.py

  cli/
    run_optimizer.py
    run_single_build.py
    compare_builds.py

  tests/
    test_population.py
    test_tracker_costs.py
    test_archery_range.py
    test_lore_effects.py
    test_path_unlocks.py
    test_winter.py
    test_clear_timing.py
```

Core data model

Use plain dataclasses or pydantic models. I would not hide this behind ORMs or complicated frameworks.

```python
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

@dataclass
class Resources:
    food: float
    wood: float
    krowns: float
    stone: float
    iron: float
    lore: float
    fame: float
    trophies: float

@dataclass
class UnitCounts:
    villagers: int = 0
    scouts: int = 0
    woodcutters: int = 0
    hunters: int = 0
    merchants: int = 0
    sailors: int = 0
    miners: int = 0
    healers: int = 0
    trackers: int = 0
    mielikki: int = 0
    brundr: int = 0
    kaelinn: int = 0

@dataclass
class ZoneState:
    zone_id: str
    owner: str                  # "self", "neutral", "enemy"
    neighbors: List[str]
    zone_tags: Set[str]         # {"forest", "shore", "deer", "stone", ...}
    building_capacity: int
    buildings: List[str]
    neutral_pack: Optional[str] # e.g. "wolves_2", "draugr_3", None
    lure_type: Optional[str]    # None, "standard", "mythical"
    improved: bool = False

@dataclass
class BuildProgress:
    build_id: str
    kind: str                   # "building", "upgrade", "forge", "recruit", "colonize", "clear"
    target: str
    started_at: float
    completes_at: float

@dataclass
class GameState:
    t: float                    # seconds since match start
    month_index: int
    in_winter: bool
    resources: Resources
    units: UnitCounts
    housing_cap: int
    happiness: float
    warband_cap: int
    zones: Dict[str, ZoneState]
    lores: Set[str]
    hunter_nodes: Set[str]
    path_complete_purchases: int
    build_queue: List[BuildProgress] = field(default_factory=list)
    current_tracker_count_for_cost: int = 0
    next_villager_spawn_at: Optional[float] = None
```

Data tables to define first

Your developer should not hardcode game values into logic. Put them in JSON/YAML and let the engine read them.

`units.json`

```json
{
  "villager": {
    "summer_food_rate": 4.0,
    "winter_food_rate": 2.4
  },
  "tracker": {
    "health": 50,
    "attack": 10,
    "defense": 3,
    "cost_formula": "25 + 5*(n-1)"
  },
  "warchief_default": {
    "health": 75,
    "attack": 15,
    "defense": 10,
    "cost_krowns": 150,
    "cost_iron": 5,
    "consumes_food": false,
    "consumes_wood": false,
    "counts_toward_population": false
  },
  "mielikki_override": {
    "cost_iron": 0
  },
  "brundr": {
    "cost_krowns": 60,
    "cost_food": 40
  },
  "kaelinn": {
    "cost_krowns": 40,
    "cost_food": 60
  }
}
```

Those values are directly documented except where you’ll later calibrate special combat behavior. Villagers gather 4 food in summer and 2.4 in winter, Trackers have 50 HP / 10 attack / 3 defense and a rising kröwn ladder starting at 25, generic Warchiefs have 75 HP / 15 attack / 10 defense and cost 150 kröwns plus 5 iron, while Mielikki is one of the exceptions that does not cost iron; Warchiefs do not consume food or wood and do not count toward population. Brundr and Kaelinn are summoned via the Archery Range and their summon costs are listed separately on the Lynx page. ([Northgard Wiki][3])

`buildings.json`

```json
{
  "town_hall": {
    "krowns_per_tick_unit": 3.0,
    "housing": 6
  },
  "house": {
    "cost_wood": 50,
    "cost_krowns": 10,
    "housing": 5,
    "upgrade_extra_housing": 3
  },
  "marketplace": {
    "merchant_slots": 2,
    "merchant_krowns_rate": 2.0,
    "buy_price_food": 2,
    "buy_price_wood": 3,
    "buy_price_stone": 40,
    "buy_price_iron": 50
  },
  "archery_range": {
    "cost_wood": 50,
    "warband_cap": 2,
    "upgrade_cost_wood": 100,
    "upgrade_cost_krowns": 50,
    "upgrade_cost_stone": 10,
    "upgrade_extra_warband": 1,
    "upgrade_tracker_attack_bonus_pct": 5
  },
  "forge": {
    "cost_wood": 60,
    "cost_krowns": 15,
    "upgrade_second_smith": true,
    "upgrade_forge_speed_pct": 20
  }
}
```

Town Hall gives +3 kröwns and 6 housing. House is 50 wood + 10 kröwns and adds +5 housing; upgraded House adds +3 more and removes the “better houses” happiness penalty. Marketplace gives two Merchant slots at 2 kröwns each and the posted buy prices are 2/3/40/50 for food/wood/stone/iron. Archery Range costs 50 wood, adds +2 warband, upgrades for 100 wood + 50 kröwns + 10 stone, and an upgrade adds +1 warband plus +5% Tracker attack. Forge costs 60 wood + 15 kröwns, and the upgraded Forge adds a second smith and +20% forging speed. ([Northgard Wiki][1])

`lores.json`

```json
{
  "sharp_axes": {"woodcutter_prod_pct": 20},
  "colonization": {"colonize_food_cost_pct": -30},
  "spoils_of_plenty": {
    "max_standard_lures": 2,
    "savage_deer_meat_bonus_pct": 10,
    "hunter_tool_free": true,
    "hunter_forge_time_pct": -50
  },
  "recruitment": {"pop_growth_speed_pct": 25},
  "hearthstone": {
    "winter_firewood_pct": -50,
    "winter_food_penalty_pct": -20
  },
  "shiny_happy_people": {"population_happiness_requirement_pct": -20},
  "weaponsmith": {"military_attack_pct": 20},
  "archery_mastery": {
    "first_tracker_free": true,
    "archery_range_upgrade_cost_pct": -50
  },
  "feeling_safe": {
    "happiness_if_warchief": 3,
    "happiness_per_upgraded_military_camp": 1
  }
}
```

All of those are explicitly listed on the Lynx page. ([Northgard Wiki][4])

`hunter_path.json`

```json
{
  "unlock_thresholds": [30, 80, 130, 190, 250, 310, 380, 440, 510, 590, 660, 740],
  "caring_siblings": {
    "brundr_attack_pct_if_with_kaelinn": 30,
    "regen_same_allied_zone": true
  },
  "sibling_rivalry": {
    "kaelinn_defense_pct_if_with_brundr": 40,
    "lynxes_produce_food_in_territory": true
  },
  "wise_one": {"mielikki_lore_out_of_combat": 3},
  "double_shot": {
    "extra_arrow": 1,
    "secondary_damage_pct": 30
  },
  "wild_hunter": {
    "ignore_supply_malus": true,
    "ignore_winter_attack_penalty": true
  },
  "path_complete": {
    "tracker_attack_speed_pct_per_buy": 5,
    "tracker_range_pct_per_buy": 5,
    "tracker_move_speed_pct_per_buy": 5
  }
}
```

The threshold ladder and node effects are on the Lynx and Path of the Hunter pages. ([Northgard Wiki][4])

`fame.json`

```json
{
  "fame_200": {
    "unlock": "mythical_lure",
    "feast_discount_per_animal_kill_pct": 7.5,
    "feast_discount_cap_pct": 50
  },
  "fame_500": {
    "unlock": "oskoreia"
  }
}
```

Those breakpoint effects are listed on the Lynx page. ([Northgard Wiki][4])

Simulation semantics

The engine advances by popping the next scheduled event. Between events, resources integrate linearly.

Use:

```python
def advance_to(state: GameState, t_next: float) -> GameState:
    dt = t_next - state.t
    flows = compute_net_flows(state)
    state.resources.food += flows.food * dt
    state.resources.wood += flows.wood * dt
    state.resources.krowns += flows.krowns * dt
    state.resources.lore += flows.lore * dt
    state.resources.fame += flows.fame * dt
    state.resources.trophies += flows.trophies * dt
    state.t = t_next
    update_month_and_winter_flags(state)
    return state
```

`compute_net_flows` should sum the production and upkeep of all assigned workers and passive buildings, then apply seasonal modifiers and lore modifiers. Villagers produce 4 food in summer and 2.4 in winter; Town Hall produces +3 kröwns; Merchants produce 2 kröwns each; winter reduces food production and increases wood burden, and outside-territory winter combat penalties matter unless Wild Hunter is unlocked. ([Northgard Wiki][3])

Population model

This is the only part I would tell him not to overfit on day one.

The exact villager spawn interval is not cleanly documented in the sources I found, but the dependencies are documented: villagers spawn from Town Hall if happiness is at least 0; higher happiness means faster spawn; higher population means slower spawn. Recruitment permanently speeds growth by 25%, and upgraded Town Hall speeds population growth by 20%. ([Northgard Wiki][3])

So implement:

```python
def villager_spawn_interval_seconds(
    happiness: float,
    population: int,
    recruitment_bonus_pct: float = 0.0,
    townhall_bonus_pct: float = 0.0,
    calibration: dict | None = None,
) -> float:
    """
    Returns time until next villager.
    Parameterized and calibratable from recordings.
    """
```

Use a calibratable formula such as:

```python
base = calibration["base_interval_sec"]
happy_term = 1.0 / (1.0 + calibration["happy_coef"] * max(happiness, 0))
pop_term = 1.0 + calibration["pop_coef"] * max(population - calibration["pop_ref"], 0)
bonus_term = 1.0 / (1.0 + recruitment_bonus_pct/100.0 + townhall_bonus_pct/100.0)
return base * happy_term * pop_term * bonus_term
```

That keeps the dependency structure right while you calibrate later from test footage.

Tracker recruitment math

This one should be exact.

```python
def tracker_unit_cost(nth_tracker: int) -> int:
    return 25 + 5 * (nth_tracker - 1)

def tracker_total_cost(n: int) -> int:
    return sum(tracker_unit_cost(i) for i in range(1, n + 1))
```

The wiki lists the exact ladder: 25, 30, 35, … and totals 340 for 8, 475 for 10, 630 for 12. ([Northgard Wiki][5])

Warband model

Warband cap is a deterministic sum.

```python
def compute_warband_cap(state: GameState) -> int:
    cap = 0
    for zone in state.zones.values():
        for b in zone.buildings:
            if b == "archery_range":
                cap += 2
            elif b == "archery_range_upgraded":
                cap += 3
    return cap
```

That matches the base +2 and upgrade +1 on the Archery Range page. ([Northgard Wiki][6])

Action model

Actions should be high-level, legal, and deterministic.

```python
class Action:
    pass

@dataclass
class Build(Action):
    building_type: str
    zone_id: str

@dataclass
class Upgrade(Action):
    building_type: str
    zone_id: str

@dataclass
class Colonize(Action):
    zone_id: str

@dataclass
class AssignWorker(Action):
    from_job: str
    to_job: str
    zone_id: str

@dataclass
class RecruitTracker(Action):
    zone_id: str

@dataclass
class RecruitMielikki(Action):
    zone_id: str

@dataclass
class SummonBrundr(Action):
    zone_id: str

@dataclass
class SummonKaelinn(Action):
    zone_id: str

@dataclass
class SelectLore(Action):
    lore_id: str

@dataclass
class UnlockHunterNode(Action):
    node_id: str

@dataclass
class PlaceLure(Action):
    zone_id: str
    lure_type: str   # "standard" or "mythical"

@dataclass
class ClearNeutral(Action):
    zone_id: str
    force_comp: dict
```

The action validator needs to enforce: enough resources, prerequisites, housing availability, camp availability, warband cap, one Warchief only, Town Hall upgraded before building upgrades, path thresholds met, and Lure prerequisites met. Those prerequisites follow directly from the building and lore pages. ([Northgard Wiki][1])

Neutral clearing model

Do not attempt full tactical simulation first. Use a compositional combat-clear approximation for neutral packs.

Each neutral pack config should define:

```json
{
  "wolves_2": {
    "enemy_units": [{"type": "wolf", "count": 2}],
    "clear_difficulty": 1.0,
    "expected_trophies": 2,
    "expected_damage_model": "wolves_2"
  }
}
```

Then implement:

```python
def estimate_clear_result(
    friendly_force: dict,
    neutral_pack: str,
    state: GameState
) -> dict:
    """
    Returns clear_time_sec, hp_losses, deaths, trophies_gained, success_prob.
    """
```

This function should apply the key Lynx modifiers that change expansion timing: Brundr and Kaelinn availability, paired bonuses if together, Mielikki presence, Weaponsmith, relevant Hunter nodes, winter, and whether Trackers are already online. Lynx specifically earns Hunting Trophies on animal kills, and trophies unlock the Hunter path, so clear order is not just map access; it is tech progression too. ([Northgard Wiki][4])

Combat evaluator

Separate macro from combat. The macro simulator outputs a final 20:00 state; then you score that state against benchmark enemy armies.

Start with:

```python
@dataclass
class CombatScore:
    win: bool
    remaining_friendly_value: float
    destroyed_enemy_value: float
    hero_survival_bonus: float
    time_to_kill: float
    total_score: float
```

Use a simple effective-value model first:

```python
def effective_tracker_dps(state: GameState) -> float:
    base = 10.0
    attack_mult = 1.0
    if "weaponsmith" in state.lores:
        attack_mult *= 1.20
    attack_mult *= 1.0 + 0.05 * count_upgraded_archery_ranges(state)
    if "double_shot" in state.hunter_nodes:
        # expected multiplier depends on clustering assumption
        attack_mult *= 1.0 + expected_double_shot_bonus(state)
    return base * attack_mult * attack_speed_multiplier(state)
```

For `attack_speed_multiplier`, use `1 + 0.05 * path_complete_purchases` when the “can attack from distance” condition is assumed true, because Path Complete is repeat-purchasable and adds 5% attack speed, 5% range, and 5% move speed per purchase. For Brundr and Kaelinn, apply paired-zone bonuses when you assume same-zone combat: Brundr gets +30% attack with Kaelinn from Caring Siblings, and Kaelinn gets +40% defense with Brundr from Sibling Rivalry. Wild Hunter removes supply malus and winter attack penalty. Weaponsmith gives +20% attack to all military units. Upgraded Archery Ranges add +5% Tracker attack per upgrade. ([Northgard Wiki][7])

That’s enough to rank builds before you build a richer combat simulator.

Scoring objective

Do not optimize one scalar like “army size.” Optimize average combat performance at 20:00 over a benchmark suite.

```python
def score_final_state(state: GameState, benchmarks: list[dict]) -> float:
    scores = []
    for bench in benchmarks:
        result = simulate_battle(state, bench)
        scores.append(result.total_score)
    return sum(scores) / len(scores)
```

Use several benchmark contexts: open field, choke, winter fight, high-body-count enemy, elite enemy. Wild Hunter and paired-lynx bonuses make fight context matter. ([Northgard Wiki][7])

Search strategy

Start with beam search, not RL.

```python
def beam_search(initial_state: GameState, beam_width: int, horizon_sec: float):
    frontier = [initial_state]
    while frontier:
        expanded = []
        for state in frontier:
            if state.t >= horizon_sec:
                expanded.append(state)
                continue
            for action in legal_actions(state):
                s2 = simulate_action(state, action)
                expanded.append(s2)
        frontier = keep_best(expanded, beam_width)
    return sorted(frontier, key=final_score, reverse=True)
```

The partial-state heuristic before 20:00 should combine:

```python
heuristic =
    eco_value(state)
    + expansion_value(state)
    + lore_progress_value(state)
    + trophy_progress_value(state)
    + military_shell_value(state)
    - risk_penalty(state)
```

Then the final ranking at 20:00 comes from the combat benchmarks.

Recommended first milestone

Tell him not to code “all mechanics” first. Code this exact slice in order:

```text
M1:
- Resources
- Town Hall / House / Marketplace / Archery Range / Forge
- Villager spawn with calibratable formula
- Worker assignments
- Winter flag
- Tracker cost ladder
- Mielikki / Brundr / Kaelinn recruitment
- Lore: Sharp Axes, Recruitment, Weaponsmith, Archery Mastery
- Path nodes: Caring Siblings, Double Shot, Wild Hunter, Path Complete
- Neutral clear approximation
- Final combat evaluator
- Beam search
```

That already captures the main decision gradients for your 20-minute Lynx problem. The rest can layer on after. Those mechanics are the ones with the clearest documented effects and the biggest impact on 20-minute lethality. ([Northgard Wiki][4])

Test cases he should write immediately

```python
def test_tracker_costs():
    assert tracker_unit_cost(1) == 25
    assert tracker_unit_cost(10) == 70
    assert tracker_total_cost(8) == 340
    assert tracker_total_cost(10) == 475

def test_archery_range_cap():
    assert cap_for_ranges(1, 0) == 2
    assert cap_for_ranges(1, 1) == 3
    assert cap_for_ranges(5, 2) == 12

def test_house_capacity():
    assert house_capacity(base=6, houses=2, upgraded_houses=0) == 16
    assert house_capacity(base=6, houses=2, upgraded_houses=1) == 19

def test_lore_mods():
    assert sharp_axes_mult(False) == 1.0
    assert sharp_axes_mult(True) == 1.2
    assert weaponsmith_mult(True) == 1.2
```

Those exact values come straight from the sources above. ([Northgard Wiki][5])

Output format

The program should return both machine-readable and human-readable output.

```json
{
  "assumptions": {
    "map": "standard_hostile",
    "shore": true,
    "forced_units": ["mielikki", "brundr", "kaelinn"]
  },
  "timeline": [
    {"t": 0, "action": "assign_initial_workers"},
    {"t": 22, "action": "build", "what": "woodcutter", "zone": "main"},
    {"t": 90, "action": "build", "what": "house", "zone": "main"},
    {"t": 180, "action": "summon", "what": "brundr"}
  ],
  "final_state": {
    "resources": {"food": 80, "wood": 20, "krowns": 15},
    "population": 20,
    "warband_cap": 11,
    "army": {"mielikki": 1, "brundr": 1, "kaelinn": 1, "trackers": 8},
    "lores": ["sharp_axes", "recruitment", "weaponsmith", "archery_mastery"],
    "hunter_nodes": ["caring_siblings", "double_shot", "wild_hunter"]
  },
  "score": {
    "mean_benchmark_score": 812.4,
    "win_rate": 0.78
  }
}
```

Bottom line for the developer

Build a table-driven event simulator with exact documented resource costs, caps, and major bonuses; keep villager spawn and detailed combat parameterized where the public formulas are unclear; search over legal high-level actions with beam search; and rank 20-minute outputs using a combat benchmark suite rather than raw unit count. The public sources are sufficient for the first working version of that system, especially for Town Hall / population gating, villager baseline production, House capacity, Marketplace rates, Tracker ladder, Archery Range cap math, Lynx lore, fame, and Hunter-path bonuses. ([Northgard Wiki][1])

I can turn this into a one-file `README_for_dev.md` next, in a cleaner handoff format with acceptance criteria.

[1]: https://northgard.fandom.com/wiki/Town_Hall "Town Hall - Official Northgard Wiki"
[2]: https://northgard.fandom.com/wiki/Economy?utm_source=chatgpt.com "Economy - Official Northgard Wiki"
[3]: https://northgard.fandom.com/wiki/Villager "Villager - Official Northgard Wiki"
[4]: https://northgard.fandom.com/wiki/Brundr_and_Kaelinn "Brundr and Kaelinn - Official Northgard Wiki"
[5]: https://northgard.fandom.com/wiki/Tracker "Tracker - Official Northgard Wiki"
[6]: https://northgard.fandom.com/wiki/Archery_Range?utm_source=chatgpt.com "Archery Range - Official Northgard Wiki"
[7]: https://northgard.fandom.com/wiki/Path_of_the_Hunter "Path of the Hunter - Official Northgard Wiki"
