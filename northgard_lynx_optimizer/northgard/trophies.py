from __future__ import annotations

from typing import List, Set

from .data_loader import load_json


def thresholds() -> List[int]:
    return list(load_json("hunter_path")["unlock_thresholds"])


def can_unlock_next_node(lifetime_trophies: float, unlocked_count: int) -> bool:
    th = thresholds()
    if unlocked_count >= len(th):
        return False
    return lifetime_trophies >= th[unlocked_count]


def next_threshold(unlocked_count: int) -> int:
    th = thresholds()
    if unlocked_count >= len(th):
        return th[-1]
    return th[unlocked_count]
