from __future__ import annotations

from typing import Dict, List

from .combat_eval import CombatScore, simulate_battle
from .state import GameState


def score_final_state(state: GameState, benchmarks: List[dict]) -> float:
    scores: List[float] = []
    for bench in benchmarks:
        result = simulate_battle(state, bench)
        scores.append(result.total_score)
    return sum(scores) / max(1, len(scores))


def benchmark_scores(state: GameState, benchmarks: List[dict]) -> List[CombatScore]:
    return [simulate_battle(state, b) for b in benchmarks]
