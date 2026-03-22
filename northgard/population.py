from __future__ import annotations

from typing import Dict, Optional


def villager_spawn_interval_seconds(
    happiness: float,
    population: int,
    recruitment_bonus_pct: float = 0.0,
    townhall_bonus_pct: float = 0.0,
    calibration: Optional[Dict] = None,
) -> float:
    base = calibration["base_interval_sec"]
    happy_term = 1.0 / (1.0 + calibration["happy_coef"] * max(happiness, 0))
    pop_term = 1.0 + calibration["pop_coef"] * max(population - calibration["pop_ref"], 0)
    bonus_term = 1.0 / (1.0 + recruitment_bonus_pct / 100.0 + townhall_bonus_pct / 100.0)
    return base * happy_term * pop_term * bonus_term


def villager_spawn_days_happiness_page_candidate(happiness: float, population: int) -> float:
    """Outdated Fandom formula (V1) — optional calibration candidate only; not confirmed truth."""
    h = max(float(happiness), 0.01)
    pop = max(int(population), 1)
    return 1.4 * (h**-0.4) * pop - 1.2 * h + 23


def villager_spawn_interval_seconds_happiness_page_candidate(
    happiness: float,
    population: int,
    seconds_per_game_day: float,
    recruitment_bonus_pct: float = 0.0,
    townhall_bonus_pct: float = 0.0,
) -> float:
    days = max(1.0, villager_spawn_days_happiness_page_candidate(happiness, population))
    bonus_term = 1.0 / (1.0 + recruitment_bonus_pct / 100.0 + townhall_bonus_pct / 100.0)
    return days * float(seconds_per_game_day) * bonus_term
