from __future__ import annotations

from typing import Any, Dict

from .data_loader import load_json
from .state import GameState


_NEUTRAL = {
    "wolves_2": {
        "enemy_units": [{"type": "wolf", "count": 2}],
        "clear_difficulty": 1.0,
        "expected_trophies": 2,
        "expected_damage_model": "wolves_2",
    },
    "draugr_3": {
        "enemy_units": [{"type": "draugr", "count": 3}],
        "clear_difficulty": 2.2,
        "expected_trophies": 3,
    },
    "bear_1": {
        "enemy_units": [{"type": "bear", "count": 1}],
        "clear_difficulty": 2.8,
        "expected_trophies": 4,
    },
}


def estimate_clear_result(
    friendly_force: dict,
    neutral_pack: str,
    state: GameState,
) -> dict:
    pack = _NEUTRAL.get(neutral_pack, _NEUTRAL["wolves_2"])
    diff = pack["clear_difficulty"]
    atk = friendly_force.get("attack_power", 10.0)
    t_mult = 1.15 if "weaponsmith" in state.lores else 1.0
    if "caring_siblings" in state.hunter_nodes and friendly_force.get("brundr_with_kaelinn"):
        t_mult *= 1.3
    clear_time_sec = max(8.0, diff * 40.0 / max(1.0, atk * t_mult))
    hp_loss = diff * 5.0
    deaths = 0 if atk * t_mult > diff * 8 else 1
    trophies = pack.get("expected_trophies", 2)
    success_prob = min(1.0, atk * t_mult / (diff * 10.0))
    return {
        "clear_time_sec": clear_time_sec,
        "hp_losses": hp_loss,
        "deaths": deaths,
        "trophies_gained": trophies,
        "success_prob": success_prob,
    }
