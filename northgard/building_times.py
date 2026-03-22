from __future__ import annotations

from typing import Any, Dict


def seconds_per_game_day(economy: Dict[str, Any]) -> float:
    return float(economy["seconds_per_game_day"])


def build_duration_seconds(building_key: str, buildings: Dict[str, Any], economy: Dict[str, Any]) -> float:
    cfg = buildings[building_key]
    if "build_time_days" in cfg:
        return float(cfg["build_time_days"]) * seconds_per_game_day(economy)
    return float(cfg.get("build_time_sec", 0.0))
