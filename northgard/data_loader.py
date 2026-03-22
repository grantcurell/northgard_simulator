from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


def _root() -> Path:
    return Path(__file__).resolve().parent.parent


def load_json(name: str) -> Dict[str, Any]:
    path = _root() / "data" / f"{name}.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_map(map_id: str) -> Dict[str, Any]:
    path = _root() / "data" / "maps" / f"{map_id}.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_benchmarks() -> list:
    path = _root() / "data" / "enemy_benchmarks.json"
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    return list(data.get("benchmarks", []))
