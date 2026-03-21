from __future__ import annotations

from typing import Set


def sharp_axes_mult(has_lore: bool) -> float:
    return 1.2 if has_lore else 1.0


def weaponsmith_mult(has_lore: bool) -> float:
    return 1.2 if has_lore else 1.0


def colonization_food_mult(lores: Set[str]) -> float:
    """Legacy −30% modifier; simulator uses Fame wiki colonization tables instead."""
    return 0.7 if "colonization" in lores else 1.0


def recruitment_pop_bonus_pct(lores: Set[str]) -> float:
    return 25.0 if "recruitment" in lores else 0.0


def archery_mastery_upgrade_cost_mult(lores: Set[str]) -> float:
    return 0.5 if "archery_mastery" in lores else 1.0


def archery_mastery_first_tracker_free(lores: Set[str]) -> bool:
    return "archery_mastery" in lores


def hearthstone_winter_firewood_mult(lores: Set[str]) -> float:
    return 0.5 if "hearthstone" in lores else 1.0


def hearthstone_winter_food_penalty_mult(lores: Set[str]) -> float:
    return 0.8 if "hearthstone" in lores else 1.0


def shiny_happy_people_offset(lores: Set[str]) -> float:
    return 0.2 if "shiny_happy_people" in lores else 0.0


def feeling_safe_bonus(
    lores: Set[str],
    has_warchief: bool,
    upgraded_military_camps: int,
) -> float:
    if "feeling_safe" not in lores:
        return 0.0
    bonus = 0.0
    if has_warchief:
        bonus += 3.0
    bonus += upgraded_military_camps
    return bonus


LORE_COSTS = {
    "sharp_axes": 50,
    "colonization": 50,
    "recruitment": 50,
    "weaponsmith": 100,
    "archery_mastery": 100,
    "hearthstone": 50,
    "shiny_happy_people": 50,
    "feeling_safe": 100,
    "spoils_of_plenty": 100,
}

LORE_ORDER = [
    "sharp_axes",
    "colonization",
    "recruitment",
    "weaponsmith",
    "archery_mastery",
    "hearthstone",
    "shiny_happy_people",
    "feeling_safe",
    "spoils_of_plenty",
]
