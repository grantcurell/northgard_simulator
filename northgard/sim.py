from __future__ import annotations

from typing import List, Sequence

from .actions import (
    Action,
    AssignWorker,
    Build,
    ClearNeutral,
    Colonize,
    PurchasePathComplete,
    RecruitMielikki,
    RecruitTracker,
    SelectLore,
    SummonBrundr,
    SummonKaelinn,
    UnlockHunterNode,
    Upgrade,
    UpgradeTownHall,
    Wait,
)
from .building_times import build_duration_seconds
from .buildings import can_place_building, sync_derived_counters
from .clearing import estimate_clear_result
from .colonization import next_colonize_food_cost
from .data_loader import load_json
from .economy import advance_to, schedule_next_spawn
from .lore import LORE_COSTS, archery_mastery_first_tracker_free, archery_mastery_upgrade_cost_mult
from .map_graph import load_map_state, self_zones
from .recruitment import tracker_unit_cost
from .state import GameState, Resources, UnitCounts, ZoneState, total_population
from .trophies import can_unlock_next_node


def initial_state(map_id: str = "standard_hostile") -> GameState:
    economy = load_json("economy")
    sr = economy["starting_resources"]
    su = economy["starting_units"]
    zones = load_map_state(map_id)
    res = Resources(
        food=float(sr["food"]),
        wood=float(sr["wood"]),
        krowns=float(sr["krowns"]),
        stone=float(sr["stone"]),
        iron=float(sr["iron"]),
        lore=float(sr["lore"]),
        fame=float(sr["fame"]),
        trophies=float(sr["trophies"]),
    )
    units = UnitCounts(
        villagers=int(su["villagers"]),
        scouts=int(su["scouts"]),
        woodcutters=int(su["woodcutters"]),
        hunters=int(su["hunters"]),
        merchants=int(su["merchants"]),
        sailors=int(su["sailors"]),
        miners=int(su["miners"]),
        healers=int(su["healers"]),
        trackers=int(su["trackers"]),
        mielikki=int(su["mielikki"]),
        brundr=int(su["brundr"]),
        kaelinn=int(su["kaelinn"]),
    )
    state = GameState(
        t=0.0,
        month_index=0,
        in_winter=False,
        resources=res,
        units=units,
        housing_cap=0,
        happiness=float(economy.get("default_happiness", 1.0)),
        warband_cap=0,
        warband_used=0,
        zones=zones,
        lores=set(),
        hunter_nodes=set(),
        path_complete_purchases=0,
    )
    sync_derived_counters(state)
    state.warband_used = state.units.trackers
    state.colonized_zones = sum(1 for z in state.zones.values() if z.owner == "self")
    schedule_next_spawn(state, economy)
    return state


def _main_zone(state: GameState) -> str:
    for zid, z in state.zones.items():
        if z.owner == "self" and "main" in zid:
            return zid
    for zid, z in state.zones.items():
        if z.owner == "self":
            return zid
    return next(iter(state.zones))


def _has_archery_range(zone: ZoneState) -> bool:
    return any(b.startswith("archery_range") for b in zone.buildings)


def _has_woodcutter_lodge(state: GameState) -> bool:
    for z in state.zones.values():
        if z.owner == "self" and "woodcutter" in z.buildings:
            return True
    return False


def _neighbor_of_self(state: GameState, zone_id: str) -> bool:
    z = state.zones[zone_id]
    if z.owner != "neutral":
        return False
    for n in z.neighbors:
        if n in state.zones and state.zones[n].owner == "self":
            return True
    return False


def legal_actions(state: GameState, map_id: str = "standard_hostile") -> List[Action]:
    actions: List[Action] = []
    buildings = load_json("buildings")
    economy = load_json("economy")
    main = _main_zone(state)

    for zid, z in state.zones.items():
        if z.owner != "self":
            continue
        if can_place_building(z, z.building_capacity):
            if state.resources.wood >= buildings["house"]["cost_wood"] and state.resources.krowns >= buildings["house"]["cost_krowns"]:
                actions.append(Build("house", zid))
            if state.resources.wood >= buildings["woodcutter"]["cost_wood"]:
                actions.append(Build("woodcutter", zid))
            if state.resources.wood >= buildings["archery_range"]["cost_wood"]:
                actions.append(Build("archery_range", zid))
            if _has_woodcutter_lodge(state) and state.resources.wood >= buildings["forge"]["cost_wood"] and state.resources.krowns >= buildings["forge"]["cost_krowns"]:
                actions.append(Build("forge", zid))
            mk = buildings["marketplace"].get("cost_krowns", 0)
            if (
                _has_woodcutter_lodge(state)
                and state.resources.wood >= buildings["marketplace"]["cost_wood"]
                and state.resources.krowns >= mk
            ):
                actions.append(Build("marketplace", zid))
        if _has_archery_range(z):
            ar = buildings["archery_range"]
            st = ar["upgrade_cost_stone"]
            w = ar["upgrade_cost_wood"]
            k = int(ar["upgrade_cost_krowns"] * archery_mastery_upgrade_cost_mult(state.lores))
            if (
                "archery_range" in z.buildings
                and state.resources.wood >= w
                and state.resources.krowns >= k
                and state.resources.stone >= st
            ):
                actions.append(Upgrade("archery_range", zid))

        if "house" in z.buildings and "house_upgraded" not in z.buildings:
            hc = buildings["house"]
            if state.resources.wood >= hc["upgrade_cost_wood"] and state.resources.krowns >= hc["upgrade_cost_krowns"]:
                actions.append(Upgrade("house", zid))

        if "forge" in z.buildings and "forge_upgraded" not in z.buildings:
            fc = buildings["forge"]
            stc = fc.get("upgrade_cost_stone", 10)
            if (
                state.resources.wood >= fc.get("upgrade_cost_wood", 100)
                and state.resources.krowns >= fc.get("upgrade_cost_krowns", 50)
                and state.resources.stone >= stc
            ):
                actions.append(Upgrade("forge", zid))

    if not state.town_hall_upgraded:
        th = buildings["town_hall"]
        stc = th.get("upgrade_cost_stone", 10)
        if (
            state.resources.wood >= th["upgrade_cost_wood"]
            and state.resources.krowns >= th["upgrade_cost_krowns"]
            and state.resources.stone >= stc
        ):
            actions.append(UpgradeTownHall(main))

    nterr = len(economy["colonize_food_without_colonization_lore"])
    for zid, z in state.zones.items():
        if z.owner == "neutral" and _neighbor_of_self(state, zid):
            if state.colonized_zones >= nterr:
                continue
            food_cost = next_colonize_food_cost(state, economy)
            if state.resources.food >= food_cost:
                actions.append(Colonize(zid))

    for zid, z in state.zones.items():
        if z.owner != "self":
            continue
        if state.units.villagers > 0:
            actions.append(AssignWorker("villager", "woodcutter", zid))
        if state.units.woodcutters > 0:
            actions.append(AssignWorker("woodcutter", "villager", zid))

    for zid, z in state.zones.items():
        if z.owner != "self" or not _has_archery_range(z):
            continue
        cap = state.warband_cap - state.warband_used
        if cap <= 0:
            continue
        n = state.current_tracker_count_for_cost + 1
        cost = tracker_unit_cost(n)
        if archery_mastery_first_tracker_free(state.lores) and n == 1:
            cost = 0
        if state.resources.krowns >= cost:
            actions.append(RecruitTracker(zid))

    u = load_json("units")
    for zid, z in state.zones.items():
        if z.owner != "self" or not _has_archery_range(z):
            continue
        if state.units.mielikki < 1 and state.resources.krowns >= u["mielikki"]["cost_krowns"]:
            actions.append(RecruitMielikki(zid))
            break
    for zid, z in state.zones.items():
        if z.owner != "self" or not _has_archery_range(z):
            continue
        b = u["brundr"]
        if state.units.brundr < 1 and state.resources.krowns >= b["cost_krowns"] and state.resources.food >= b["cost_food"]:
            actions.append(SummonBrundr(zid))
            break
    for zid, z in state.zones.items():
        if z.owner != "self" or not _has_archery_range(z):
            continue
        k = u["kaelinn"]
        if state.units.kaelinn < 1 and state.resources.krowns >= k["cost_krowns"] and state.resources.food >= k["cost_food"]:
            actions.append(SummonKaelinn(zid))
            break

    for lore_id, cost in LORE_COSTS.items():
        if lore_id in state.lores:
            continue
        if state.resources.lore >= float(cost):
            actions.append(SelectLore(lore_id))

    order = ["caring_siblings", "double_shot", "wild_hunter"]
    next_node = None
    for node in order:
        if node in state.hunter_nodes:
            continue
        idx = len(state.hunter_nodes)
        if can_unlock_next_node(state.lifetime_trophies, idx):
            next_node = node
        break
    if next_node is not None:
        actions.append(UnlockHunterNode(next_node))

    path_trophy_cost = 50 + state.path_complete_purchases * 15
    if state.resources.trophies >= path_trophy_cost:
        actions.append(PurchasePathComplete())

    for zid, z in state.zones.items():
        if z.owner == "self" and z.neutral_pack:
            actions.append(ClearNeutral(zid))

    actions.append(Wait(5.0))
    actions.append(Wait(15.0))
    return actions


def _log(state: GameState, action: Action) -> None:
    state.action_log.append({"t": state.t, "action": str(action)})


def apply_action(state: GameState, action: Action) -> None:
    buildings = load_json("buildings")
    economy = load_json("economy")
    units_data = load_json("units")

    if isinstance(action, Wait):
        advance_to(state, state.t + action.seconds)
        _log(state, action)
        sync_derived_counters(state)
        return

    if isinstance(action, Build):
        z = state.zones[action.zone_id]
        cfg = buildings[action.building_type]
        wood = cfg["cost_wood"]
        krowns = cfg.get("cost_krowns", 0)
        if action.building_type == "house":
            state.resources.wood -= wood
            state.resources.krowns -= krowns
            dur = build_duration_seconds("house", buildings, economy)
        elif action.building_type == "woodcutter":
            state.resources.wood -= wood
            dur = build_duration_seconds("woodcutter", buildings, economy)
        elif action.building_type == "archery_range":
            state.resources.wood -= wood
            dur = build_duration_seconds("archery_range", buildings, economy)
        elif action.building_type == "forge":
            if not _has_woodcutter_lodge(state):
                return
            state.resources.wood -= wood
            state.resources.krowns -= krowns
            dur = build_duration_seconds("forge", buildings, economy)
        elif action.building_type == "marketplace":
            if not _has_woodcutter_lodge(state):
                return
            state.resources.wood -= wood
            state.resources.krowns -= krowns
            dur = build_duration_seconds("marketplace", buildings, economy)
        else:
            return
        advance_to(state, state.t + dur)
        tag = "archery_range" if action.building_type == "archery_range" else action.building_type
        z.buildings.append(tag)
        _log(state, action)
        sync_derived_counters(state)
        state.warband_used = state.units.trackers
        return

    if isinstance(action, Upgrade) and action.building_type == "archery_range":
        z = state.zones[action.zone_id]
        ar = buildings["archery_range"]
        w = ar["upgrade_cost_wood"]
        k = int(ar["upgrade_cost_krowns"] * archery_mastery_upgrade_cost_mult(state.lores))
        st = ar["upgrade_cost_stone"]
        state.resources.wood -= w
        state.resources.krowns -= k
        state.resources.stone -= st
        dur = ar["upgrade_build_time_sec"]
        advance_to(state, state.t + dur)
        z.buildings = [b for b in z.buildings if b != "archery_range"]
        z.buildings.append("archery_range_upgraded")
        _log(state, action)
        sync_derived_counters(state)
        state.warband_used = state.units.trackers
        return

    if isinstance(action, Upgrade) and action.building_type == "house":
        z = state.zones[action.zone_id]
        hc = buildings["house"]
        state.resources.wood -= hc["upgrade_cost_wood"]
        state.resources.krowns -= hc["upgrade_cost_krowns"]
        dur = hc["upgrade_build_time_sec"]
        advance_to(state, state.t + dur)
        z.buildings = [b for b in z.buildings if b != "house"]
        z.buildings.append("house_upgraded")
        _log(state, action)
        sync_derived_counters(state)
        return

    if isinstance(action, Upgrade) and action.building_type == "forge":
        z = state.zones[action.zone_id]
        fc = buildings["forge"]
        state.resources.wood -= fc.get("upgrade_cost_wood", 100)
        state.resources.krowns -= fc.get("upgrade_cost_krowns", 50)
        state.resources.stone -= fc.get("upgrade_cost_stone", 10)
        dur = fc["upgrade_build_time_sec"]
        advance_to(state, state.t + dur)
        z.buildings = [b for b in z.buildings if b != "forge"]
        z.buildings.append("forge_upgraded")
        _log(state, action)
        sync_derived_counters(state)
        return

    if isinstance(action, UpgradeTownHall):
        th = buildings["town_hall"]
        state.resources.wood -= th["upgrade_cost_wood"]
        state.resources.krowns -= th["upgrade_cost_krowns"]
        state.resources.stone -= th.get("upgrade_cost_stone", 10)
        dur_th = float(economy.get("town_hall_upgrade_duration_seconds_unknown_placeholder", 25.0))
        advance_to(state, state.t + dur_th)
        state.town_hall_upgraded = True
        _log(state, action)
        sync_derived_counters(state)
        return

    if isinstance(action, Colonize):
        z = state.zones[action.zone_id]
        food_cost = next_colonize_food_cost(state, economy)
        state.resources.food -= food_cost
        col_dur = float(economy.get("colonization_duration_seconds_unknown_placeholder", 8.0))
        advance_to(state, state.t + col_dur)
        z.owner = "self"
        state.colonized_zones += 1
        _log(state, action)
        sync_derived_counters(state)
        return

    if isinstance(action, AssignWorker):
        if action.from_job == "villager" and action.to_job == "woodcutter":
            if state.units.villagers <= 0:
                return
            state.units.villagers -= 1
            state.units.woodcutters += 1
        elif action.from_job == "woodcutter" and action.to_job == "villager":
            if state.units.woodcutters <= 0:
                return
            state.units.woodcutters -= 1
            state.units.villagers += 1
        _log(state, action)
        return

    if isinstance(action, RecruitTracker):
        n = state.current_tracker_count_for_cost + 1
        cost = tracker_unit_cost(n)
        if archery_mastery_first_tracker_free(state.lores) and n == 1:
            cost = 0
        state.resources.krowns -= cost
        state.units.trackers += 1
        state.current_tracker_count_for_cost += 1
        state.warband_used = state.units.trackers
        _log(state, action)
        return

    if isinstance(action, RecruitMielikki):
        k = units_data["mielikki"]["cost_krowns"]
        state.resources.krowns -= k
        state.units.mielikki += 1
        _log(state, action)
        return

    if isinstance(action, SummonBrundr):
        b = units_data["brundr"]
        state.resources.krowns -= b["cost_krowns"]
        state.resources.food -= b["cost_food"]
        state.units.brundr += 1
        _log(state, action)
        return

    if isinstance(action, SummonKaelinn):
        k = units_data["kaelinn"]
        state.resources.krowns -= k["cost_krowns"]
        state.resources.food -= k["cost_food"]
        state.units.kaelinn += 1
        _log(state, action)
        return

    if isinstance(action, SelectLore):
        cost = LORE_COSTS.get(action.lore_id, 50)
        state.resources.lore -= float(cost)
        state.lores.add(action.lore_id)
        state.lore_order += 1
        _log(state, action)
        return

    if isinstance(action, UnlockHunterNode):
        if not can_unlock_next_node(state.lifetime_trophies, len(state.hunter_nodes)):
            return
        if action.node_id in state.hunter_nodes:
            return
        state.hunter_nodes.add(action.node_id)
        _log(state, action)
        return

    if isinstance(action, PurchasePathComplete):
        cost = 50 + state.path_complete_purchases * 15
        if state.resources.trophies < cost:
            return
        state.resources.trophies -= cost
        state.path_complete_purchases += 1
        _log(state, action)
        return

    if isinstance(action, ClearNeutral):
        z = state.zones[action.zone_id]
        if not z.neutral_pack:
            return
        ff = {
            "attack_power": 10.0 + state.units.trackers * 3.0,
            "brundr_with_kaelinn": state.units.brundr > 0 and state.units.kaelinn > 0,
        }
        est = estimate_clear_result(ff, z.neutral_pack, state)
        advance_to(state, state.t + float(est["clear_time_sec"]))
        tr = float(est["trophies_gained"])
        state.resources.trophies += tr
        state.lifetime_trophies += tr
        state.animal_kills += 1
        z.neutral_pack = None
        _log(state, action)
        return


def simulate_to_horizon(
    state: GameState,
    actions: Sequence[Action],
    horizon_sec: float = 1200.0,
) -> GameState:
    s = state.clone()
    for a in actions:
        if s.t >= horizon_sec:
            break
        apply_action(s, a)
        if s.t >= horizon_sec:
            break
    advance_to(s, horizon_sec)
    sync_derived_counters(s)
    s.warband_used = s.units.trackers
    return s
