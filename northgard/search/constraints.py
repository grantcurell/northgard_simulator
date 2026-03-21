from __future__ import annotations

from northgard.state import GameState, total_population


def within_pop_cap(state: GameState) -> bool:
    return total_population(state.units) <= state.housing_cap + 2
