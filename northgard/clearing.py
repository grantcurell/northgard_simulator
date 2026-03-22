from __future__ import annotations

from typing import Any, Dict

from .data_loader import load_json
from .state import GameState


_NEUTRAL = {
    "wolves_2": {
        "enemy_units": [{"type": "wolf", "count": 2}],
        "clear_difficulty": 1.0,
        "expected_damage_model": "wolves_2",
    },
    "draugr_3": {
        "enemy_units": [{"type": "draugr", "count": 3}],
        "clear_difficulty": 2.2,
    },
    "bear_1": {
        "enemy_units": [{"type": "bear", "count": 1}],
        "clear_difficulty": 2.8,
    },
}


def _trophies_per_kill(
    neutral_type: str,
    state: GameState,
    trophy_data: Dict[str, Any],
    economy: Dict[str, Any],
) -> float:
    """P4 / N2 — per-kill table when sourced; mystical rows gated on Great Hunt assumption."""
    tmap = trophy_data.get("neutral_pack_type_map", {})
    wiki_key = tmap.get(neutral_type, neutral_type)
    base = trophy_data.get("base_kills", {})
    gh = trophy_data.get("great_hunt_only_kills", {})
    assume_gh = bool(economy.get("assume_great_hunt_for_mystical_kill_trophies", False))
    if wiki_key in base:
        return float(base[wiki_key])
    if wiki_key in gh:
        if assume_gh:
            return float(gh[wiki_key])
        ph = trophy_data.get("draugr_without_great_hunt", {})
        return float(ph.get("simulator_placeholder_trophies_per_kill", 0.0))
    return 0.0


def _expected_trophies_from_pack(pack: Dict[str, Any], state: GameState) -> float:
    trophy_data = load_json("trophy_income_per_kill")
    economy = load_json("economy")
    total = 0.0
    for u in pack.get("enemy_units", []):
        ntype = u["type"]
        count = int(u["count"])
        total += count * _trophies_per_kill(ntype, state, trophy_data, economy)
    return total


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
    trophies = _expected_trophies_from_pack(pack, state)
    success_prob = min(1.0, atk * t_mult / (diff * 10.0))
    return {
        "clear_time_sec": clear_time_sec,
        "hp_losses": hp_loss,
        "deaths": deaths,
        "trophies_gained": trophies,
        "success_prob": success_prob,
    }
