from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

from .data_loader import load_json
from .lore import (
    hearthstone_winter_firewood_mult,
    hearthstone_winter_food_penalty_mult,
    recruitment_pop_bonus_pct,
    sharp_axes_mult,
)
from .population import villager_spawn_interval_seconds
from .state import GameState, Resources, total_civilian_workers, total_population


@dataclass
class NetFlows:
    food: float
    wood: float
    krowns: float
    stone: float
    iron: float
    lore: float
    fame: float
    trophies: float
    firewood: float


def _seconds_per_tick(economy: Dict) -> float:
    return float(economy["seconds_per_tick"])


def _lore_per_tick_from_population(pop: int, economy: Dict) -> float:
    if pop < 1:
        return 0.0
    for br in economy["lore_from_population_ticks"]:
        if int(br["min_pop"]) <= pop <= int(br["max_pop"]):
            return float(br["lore_per_tick"])
    return 0.0


def _krowns_upkeep_per_sec(state: GameState, economy: Dict) -> float:
    upkeep = load_json("building_upkeep_easy")
    year_sec = float(economy.get("seconds_per_year", 720.0))
    total_yearly = 0.0
    for z in state.zones.values():
        for b in z.buildings:
            if b in upkeep:
                total_yearly += float(upkeep[b])
    return total_yearly / year_sec


def _month_index_at_time(state: GameState, economy: Dict) -> Tuple[int, bool]:
    spm = economy["seconds_per_month"]
    elapsed = int(state.t // spm)
    idx = (economy["starting_month_index"] + elapsed) % economy["months_per_year"]
    in_winter = idx in economy["winter_month_indices"]
    return idx, in_winter


def update_month_and_winter_flags(state: GameState, economy: Dict | None = None) -> None:
    if economy is None:
        economy = load_json("economy")
    idx, in_winter = _month_index_at_time(state, economy)
    state.month_index = idx
    state.in_winter = in_winter


def compute_net_flows(state: GameState) -> NetFlows:
    economy = load_json("economy")
    buildings = load_json("buildings")
    units = load_json("units")
    spt = _seconds_per_tick(economy)

    _, in_winter = _month_index_at_time(state, economy)
    state.in_winter = in_winter

    if in_winter:
        food_tick = units["villager"]["winter_food_per_tick"]
        food_tick *= hearthstone_winter_food_penalty_mult(state.lores)
    else:
        food_tick = units["villager"]["summer_food_per_tick"]
    food_rate = (food_tick / spt) * state.units.villagers

    wood_tick = units["woodcutter"]["wood_per_tick"]
    wood_rate = (wood_tick / spt) * state.units.woodcutters * sharp_axes_mult("sharp_axes" in state.lores)

    th = buildings["town_hall"]
    krowns = (float(th["krowns_per_tick"]) / spt)

    mp = buildings["marketplace"]
    mpt = float(mp.get("merchant_krowns_per_tick", units["merchant"]["krowns_per_tick"]))
    krowns += (mpt / spt) * state.units.merchants

    pop = total_population(state.units)
    lore_tick = _lore_per_tick_from_population(pop, economy)
    lore = lore_tick / spt
    if "wise_one" in state.hunter_nodes and state.units.mielikki > 0:
        hp = load_json("hunter_path")
        lore += (
            float(hp["wise_one"]["mielikki_lore_out_of_combat"])
            / spt
            * state.units.mielikki
        )

    fame = float(economy.get("fame_per_population_per_sec", 0.05)) * pop
    trophies = 0.0

    firewood = 0.0
    if in_winter:
        base_fw = 0.15 * total_civilian_workers(state.units)
        firewood = base_fw * hearthstone_winter_firewood_mult(state.lores)

    stone = 0.0
    iron = 0.0
    if state.units.miners > 0:
        stone = float(units["miner"]["stone_per_sec"]) * state.units.miners

    krowns -= _krowns_upkeep_per_sec(state, economy)

    food_upkeep = 0.1 * state.units.trackers / spt
    wood_upkeep = 0.05 * state.units.trackers / spt
    food_rate -= food_upkeep
    wood_rate -= wood_upkeep + firewood

    return NetFlows(
        food=food_rate,
        wood=wood_rate,
        krowns=krowns,
        stone=stone,
        iron=iron,
        lore=lore,
        fame=fame,
        trophies=trophies,
        firewood=firewood,
    )


def apply_flows_to_resources(res: Resources, flows: NetFlows, dt: float) -> None:
    res.food += flows.food * dt
    res.wood += flows.wood * dt
    res.krowns += flows.krowns * dt
    res.stone += flows.stone * dt
    res.iron += flows.iron * dt
    res.lore += flows.lore * dt
    res.fame += flows.fame * dt
    res.trophies += flows.trophies * dt
    res.food = max(0.0, res.food)
    res.wood = max(0.0, res.wood)


def schedule_next_spawn(state: GameState, economy: Dict | None = None) -> None:
    if economy is None:
        economy = load_json("economy")
    cal = economy["spawn_calibration"]
    pop = total_population(state.units)
    rec = recruitment_pop_bonus_pct(state.lores)
    th = 20.0 if state.town_hall_upgraded else 0.0
    interval = villager_spawn_interval_seconds(
        state.happiness,
        pop,
        recruitment_bonus_pct=rec,
        townhall_bonus_pct=th,
        calibration=cal,
    )
    state.next_villager_spawn_at = state.t + interval


def advance_to(state: GameState, t_next: float) -> None:
    economy = load_json("economy")
    if t_next <= state.t:
        return
    while state.t < t_next - 1e-6:
        step = min(1.0, t_next - state.t)
        if state.next_villager_spawn_at is not None:
            rem = state.next_villager_spawn_at - state.t
            if rem > 0:
                step = min(step, rem)
        flows = compute_net_flows(state)
        apply_flows_to_resources(state.resources, flows, step)
        state.t += step
        update_month_and_winter_flags(state, economy)
        if state.next_villager_spawn_at is not None and state.t + 1e-6 >= state.next_villager_spawn_at:
            _try_spawn_villager(state, economy)


def _try_spawn_villager(state: GameState, economy: Dict) -> None:
    if state.happiness < 0:
        state.next_villager_spawn_at = state.t + 2.0
        return
    if total_population(state.units) >= state.housing_cap:
        state.next_villager_spawn_at = state.t + 2.0
        return
    state.units.villagers += 1
    schedule_next_spawn(state, economy)
