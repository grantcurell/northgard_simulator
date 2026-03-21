from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List, Optional

from northgard import gpu_ops
from northgard.economy import advance_to
from northgard.scoring import score_final_state
from northgard.sim import apply_action, legal_actions
from northgard.state import GameState
from northgard.search.heuristics import combined_heuristic_batch


@dataclass
class BeamResult:
    final_state: GameState
    actions: List
    heuristic_score: float
    combat_score: float


def _clone_apply(state: GameState, action) -> GameState:
    s = state.clone()
    apply_action(s, action)
    return s


def _maybe_update_best(
    st: GameState,
    seq: List,
    benchmarks: list,
    score_fn: Optional[Callable[[GameState], float]],
    best_combat: float,
    best_result: Optional[BeamResult],
) -> tuple[float, Optional[BeamResult]]:
    cs = score_fn(st) if score_fn else score_final_state(st, benchmarks)
    if cs > best_combat:
        h = combined_heuristic_batch([st])[0]
        return cs, BeamResult(
            final_state=st.clone(),
            actions=list(seq),
            heuristic_score=h,
            combat_score=cs,
        )
    return best_combat, best_result


def beam_search(
    initial: GameState,
    benchmarks: list,
    beam_width: int = 32,
    horizon_sec: float = 1200.0,
    max_rounds: int = 150,
    max_expansions: int = 12000,
    expand_per_state: int = 28,
    score_fn: Optional[Callable[[GameState], float]] = None,
) -> BeamResult:
    beam: List[tuple[GameState, List]] = [(initial.clone(), [])]
    best_combat = -1e18
    best_result: Optional[BeamResult] = None
    expansions = 0

    for _ in range(max_rounds):
        if expansions >= max_expansions:
            break
        batch_states: List[GameState] = []
        batch_seqs: List[List] = []

        for st, seq in beam:
            if st.t >= horizon_sec - 1e-6:
                best_combat, best_result = _maybe_update_best(
                    st, seq, benchmarks, score_fn, best_combat, best_result
                )
                continue

            acts = legal_actions(st)
            if not acts:
                adv = st.clone()
                advance_to(adv, horizon_sec)
                best_combat, best_result = _maybe_update_best(
                    adv, seq, benchmarks, score_fn, best_combat, best_result
                )
                continue

            for a in acts[:expand_per_state]:
                if expansions >= max_expansions:
                    break
                ns = _clone_apply(st, a)
                batch_states.append(ns)
                batch_seqs.append(seq + [a])
                expansions += 1

        if not batch_states:
            break

        feats = gpu_ops.encode_states(batch_states)
        h_scores = gpu_ops.batched_heuristic_scores(feats)
        proxy = gpu_ops.batch_mean_combat_proxy(batch_states)
        combined = h_scores + 0.35 * proxy
        idx = gpu_ops.top_k_indices(combined, beam_width)
        beam = [(batch_states[i], batch_seqs[i]) for i in idx]

        if not beam:
            break

    for st, seq in beam:
        adv = st.clone()
        advance_to(adv, horizon_sec)
        best_combat, best_result = _maybe_update_best(
            adv, seq, benchmarks, score_fn, best_combat, best_result
        )

    if best_result is None:
        st = initial.clone()
        advance_to(st, horizon_sec)
        _, best_result = _maybe_update_best(
            st, [], benchmarks, score_fn, -1e18, None
        )
        assert best_result is not None
    return best_result
