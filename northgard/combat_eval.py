from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import Dict, List

from .data_loader import load_json
from .state import GameState


@dataclass
class CombatScore:
    win: bool
    remaining_friendly_value: float
    destroyed_enemy_value: float
    hero_survival_bonus: float
    time_to_kill: float
    total_score: float


def count_upgraded_archery_ranges(state: GameState) -> int:
    return state.archery_ranges_upgraded


def expected_double_shot_bonus(state: GameState, clustering: float) -> float:
    if "double_shot" not in state.hunter_nodes:
        return 0.0
    hp = load_json("hunter_path")
    sec = hp["double_shot"]["secondary_damage_pct"] / 100.0
    return clustering * sec


def attack_speed_multiplier(state: GameState) -> float:
    n = state.path_complete_purchases
    return 1.0 + 0.05 * n


def effective_tracker_dps(state: GameState, clustering: float) -> float:
    base = 10.0
    attack_mult = 1.0
    if "weaponsmith" in state.lores:
        attack_mult *= 1.20
    attack_mult *= 1.0 + 0.05 * count_upgraded_archery_ranges(state)
    if "double_shot" in state.hunter_nodes:
        attack_mult *= 1.0 + expected_double_shot_bonus(state, clustering)
    return base * attack_mult * attack_speed_multiplier(state)


def effective_tracker_hp(state: GameState) -> float:
    hp = 50.0
    if "wild_hunter" in state.hunter_nodes:
        hp *= 1.05
    return hp


def paired_brundr_attack_mult(state: GameState, same_zone: bool) -> float:
    if not same_zone:
        return 1.0
    if "caring_siblings" not in state.hunter_nodes:
        return 1.0
    if state.units.brundr < 1 or state.units.kaelinn < 1:
        return 1.0
    hp = load_json("hunter_path")
    return 1.0 + hp["caring_siblings"]["brundr_attack_pct_if_with_kaelinn"] / 100.0


def paired_kaelinn_defense_mult(state: GameState, same_zone: bool) -> float:
    if not same_zone:
        return 1.0
    if "sibling_rivalry" not in state.hunter_nodes:
        return 1.0
    if state.units.brundr < 1 or state.units.kaelinn < 1:
        return 1.0
    hp = load_json("hunter_path")
    return 1.0 + hp["sibling_rivalry"]["kaelinn_defense_pct_if_with_brundr"] / 100.0


def winter_attack_mult(state: GameState, context: Dict) -> float:
    """Wiki: -30% attack outside territory, -10% inside, in winter; Wild Hunter removes."""
    if not context.get("winter", False):
        return 1.0
    if "wild_hunter" in state.hunter_nodes:
        return 1.0
    if context.get("outside_territory", False):
        return 0.7
    return 0.9


def _hero_contribution(state: GameState, same_zone: bool) -> float:
    u = load_json("units")
    hero = 0.0
    if state.units.mielikki > 0:
        m = u["mielikki"]
        hero += m["attack"] * 3.0 + m["health"] * 0.2
    if state.units.brundr > 0:
        b = u["brundr"]
        hero += (b["attack"] * 3.0 + b["health"] * 0.2) * paired_brundr_attack_mult(state, same_zone)
    if state.units.kaelinn > 0:
        k = u["kaelinn"]
        hero += (k["attack"] * 3.0 + k["health"] * 0.2) * paired_kaelinn_defense_mult(state, same_zone)
    return hero


def army_effective_value(state: GameState, context: Dict) -> float:
    clustering = float(context.get("clustering", 0.6))
    same_zone = bool(context.get("paired_lynx_same_zone", True))
    dps = effective_tracker_dps(state, clustering) * max(0, state.units.trackers)
    dps *= winter_attack_mult(state, context)
    hero = _hero_contribution(state, same_zone)
    hp_pool = effective_tracker_hp(state) * state.units.trackers + hero * 5.0
    return dps * 2.0 + sqrt(max(0.0, hp_pool))


def simulate_battle(state: GameState, bench: Dict) -> CombatScore:
    ctx = bench.get("context", {})
    friendly = army_effective_value(state, ctx)
    enemy = 0.0
    for u in bench.get("enemy_units", []):
        enemy += u["count"] * (u["attack"] * 2.0 + u["hp"] * 0.15)
    win = friendly > enemy * 0.95
    ttk = enemy / max(1.0, friendly * 0.05)
    surv = friendly * 0.4 if win else friendly * 0.1
    total = surv + (enemy if win else enemy * 0.2) + (50.0 if win else 0.0) - ttk * 0.02
    return CombatScore(
        win=win,
        remaining_friendly_value=surv,
        destroyed_enemy_value=enemy if win else enemy * 0.3,
        hero_survival_bonus=10.0 if state.units.mielikki > 0 else 0.0,
        time_to_kill=ttk,
        total_score=max(0.0, total),
    )
