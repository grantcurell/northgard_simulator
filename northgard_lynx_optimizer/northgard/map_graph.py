from __future__ import annotations

from typing import Dict, Set

from .data_loader import load_map
from .state import GameState, ZoneState


def load_map_state(map_id: str) -> Dict[str, ZoneState]:
    raw = load_map(map_id)
    zones: Dict[str, ZoneState] = {}
    start = raw["start_zone"]
    for zid, z in raw["zones"].items():
        owner = "self" if zid == start else "neutral"
        zones[zid] = ZoneState(
            zone_id=zid,
            owner=owner,
            neighbors=list(z["neighbors"]),
            zone_tags=set(z.get("zone_tags", [])),
            building_capacity=int(z["building_capacity"]),
            buildings=list(z.get("buildings", [])),
            neutral_pack=z.get("neutral_pack"),
            lure_type=z.get("lure_type"),
            improved=bool(z.get("improved", False)),
        )
    return zones


def self_zones(state: GameState) -> Dict[str, ZoneState]:
    return {k: v for k, v in state.zones.items() if v.owner == "self"}
