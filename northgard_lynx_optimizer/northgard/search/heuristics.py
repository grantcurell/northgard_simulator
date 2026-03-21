from __future__ import annotations

from northgard import gpu_ops
from northgard.state import GameState


def eco_value(state: GameState) -> float:
    return (
        state.resources.food * 0.01
        + state.resources.wood * 0.012
        + state.resources.krowns * 0.015
    )


def expansion_value(state: GameState) -> float:
    return float(state.colonized_zones) * 25.0


def lore_progress_value(state: GameState) -> float:
    return float(len(state.lores)) * 18.0 + state.resources.lore * 0.08


def trophy_progress_value(state: GameState) -> float:
    return state.lifetime_trophies * 0.12 + state.resources.trophies * 0.1


def military_shell_value(state: GameState) -> float:
    return (
        state.units.trackers * 14.0
        + state.units.mielikki * 40.0
        + state.units.brundr * 35.0
        + state.units.kaelinn * 32.0
        + state.warband_cap * 2.0
    )


def risk_penalty(state: GameState) -> float:
    if state.resources.krowns < 0 or state.resources.food < -50:
        return 80.0
    return 0.0


def combined_heuristic(state: GameState) -> float:
    return (
        eco_value(state)
        + expansion_value(state)
        + lore_progress_value(state)
        + trophy_progress_value(state)
        + military_shell_value(state)
        - risk_penalty(state)
    )


def combined_heuristic_batch(states: list[GameState]) -> list[float]:
    if not states:
        return []
    feats = gpu_ops.encode_states(states)
    scores = gpu_ops.batched_heuristic_scores(feats)
    return gpu_ops.scores_to_float_list(scores)
