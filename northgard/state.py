from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple


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
    owner: str
    neighbors: List[str]
    zone_tags: Set[str]
    building_capacity: int
    buildings: List[str]
    neutral_pack: Optional[str]
    lure_type: Optional[str]
    improved: bool = False


@dataclass
class BuildProgress:
    build_id: str
    kind: str
    target: str
    started_at: float
    completes_at: float


@dataclass
class GameState:
    t: float
    month_index: int
    in_winter: bool
    resources: Resources
    units: UnitCounts
    housing_cap: int
    happiness: float
    warband_cap: int
    warband_used: int
    zones: Dict[str, ZoneState]
    lores: Set[str]
    hunter_nodes: Set[str]
    path_complete_purchases: int
    build_queue: List[BuildProgress] = field(default_factory=list)
    current_tracker_count_for_cost: int = 0
    next_villager_spawn_at: Optional[float] = None
    town_hall_upgraded: bool = False
    lifetime_trophies: float = 0.0
    animal_kills: int = 0
    archery_ranges: int = 0
    archery_ranges_upgraded: int = 0
    houses: int = 0
    houses_upgraded: int = 0
    marketplaces: int = 0
    forges: int = 0
    forges_upgraded: int = 0
    woodcutter_huts: int = 0
    colonized_zones: int = 1
    lore_order: int = 0
    action_log: List[Dict[str, Any]] = field(default_factory=list)

    def clone(self) -> GameState:
        return copy.deepcopy(self)


def total_civilian_workers(units: UnitCounts) -> int:
    return (
        units.villagers
        + units.woodcutters
        + units.hunters
        + units.merchants
        + units.miners
        + units.sailors
        + units.healers
    )


def total_population(units: UnitCounts) -> int:
    return (
        total_civilian_workers(units)
        + units.scouts
        + units.trackers
        + units.mielikki
        + units.brundr
        + units.kaelinn
    )
