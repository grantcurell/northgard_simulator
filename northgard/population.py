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
