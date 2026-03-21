from __future__ import annotations

from typing import Dict

from .data_loader import load_json
from .state import GameState


def next_colonize_food_cost(state: GameState, economy: Dict | None = None) -> float:
    """Food cost for the next colonization from Fame wiki tables (territory index)."""
    if economy is None:
        economy = load_json("economy")
    if "colonization" in state.lores:
        table = economy["colonize_food_with_colonization_lore"]
    else:
        table = economy["colonize_food_without_colonization_lore"]
    idx = min(max(0, state.colonized_zones), len(table) - 1)
    return float(table[idx])
