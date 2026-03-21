from __future__ import annotations

from typing import Dict

from .data_loader import load_json
from .state import GameState, ZoneState


def house_capacity(
    base: int,
    total_houses: int,
    upgraded_houses: int,
    extra_from_th: int = 0,
) -> int:
    """Town Hall base + each house +5; each upgraded house is +8 total (5+3)."""
    basic = total_houses - upgraded_houses
    return base + basic * 5 + upgraded_houses * 8 + extra_from_th


def count_archery_range_buildings(state: GameState) -> tuple[int, int]:
    base = 0
    upgraded = 0
    for z in state.zones.values():
        for b in z.buildings:
            if b == "archery_range":
                base += 1
            elif b == "archery_range_upgraded":
                upgraded += 1
    return base, upgraded


def compute_warband_cap(state: GameState) -> int:
    cap = 0
    for zone in state.zones.values():
        for b in zone.buildings:
            if b == "archery_range":
                cap += 2
            elif b == "archery_range_upgraded":
                cap += 3
    return cap


def sync_derived_counters(state: GameState, buildings_data: Dict | None = None) -> None:
    if buildings_data is None:
        buildings_data = load_json("buildings")
    th = buildings_data["town_hall"]
    base_housing = th["housing"]
    extra_th = th["upgrade_extra_housing"] if state.town_hall_upgraded else 0
    house_cfg = buildings_data["house"]
    n_basic = 0
    n_up = 0
    state.archery_ranges = 0
    state.archery_ranges_upgraded = 0
    state.marketplaces = 0
    state.forges = 0
    state.forges_upgraded = 0
    state.woodcutter_huts = 0
    for z in state.zones.values():
        for b in z.buildings:
            if b == "house":
                n_basic += 1
            elif b == "house_upgraded":
                n_up += 1
            elif b == "archery_range":
                state.archery_ranges += 1
            elif b == "archery_range_upgraded":
                state.archery_ranges += 1
                state.archery_ranges_upgraded += 1
            elif b == "marketplace":
                state.marketplaces += 1
            elif b == "forge":
                state.forges += 1
            elif b == "forge_upgraded":
                state.forges += 1
                state.forges_upgraded += 1
            elif b == "woodcutter":
                state.woodcutter_huts += 1
    state.houses = n_basic + n_up
    state.houses_upgraded = n_up
    state.housing_cap = house_capacity(
        base_housing,
        state.houses,
        state.houses_upgraded,
        extra_th,
    )
    state.warband_cap = compute_warband_cap(state)


def zone_building_count(zone: ZoneState) -> int:
    return len(zone.buildings)


def can_place_building(zone: ZoneState, building_slots: int) -> bool:
    return zone_building_count(zone) < building_slots
