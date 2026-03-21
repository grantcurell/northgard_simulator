"""GPU-only batch scoring via CuPy. Importing this module requires a working CUDA GPU."""

from __future__ import annotations

from typing import List, Sequence

import numpy as np

from .state import GameState

try:
    import cupy as cp
except ImportError as e:
    raise RuntimeError(
        "northgard: GPU required — CuPy is not installed. "
        "Install a CUDA-matching wheel, e.g. `pip install cupy-cuda12x`."
    ) from e


def _verify_gpu_works() -> None:
    """Fail fast if no device or kernels cannot run (wrong driver, sm mismatch, etc.)."""
    try:
        n = cp.cuda.runtime.getDeviceCount()
    except Exception as e:
        raise RuntimeError(
            "northgard: GPU required — could not query CUDA devices. "
            "Install NVIDIA drivers and a CuPy build matching your CUDA toolkit."
        ) from e
    if n < 1:
        raise RuntimeError(
            "northgard: GPU required — no CUDA devices found (device count is 0)."
        )
    try:
        with cp.cuda.Device(0):
            x = cp.ones(256, dtype=cp.float32)
            y = float(cp.sum(x * x))
            if y < 0:
                raise RuntimeError("unexpected")
    except Exception as e:
        raise RuntimeError(
            "northgard: GPU required — CuPy could not run a test kernel on CUDA device 0. "
            "Check GPU driver, CUDA version, and CuPy wheel compatibility."
        ) from e


_verify_gpu_works()


def require_gpu() -> None:
    """No-op if GPU already verified at import; call from CLI for an explicit check."""
    _verify_gpu_works()


def _features(state: GameState) -> np.ndarray:
    return np.array(
        [
            state.resources.food / 500.0,
            state.resources.wood / 500.0,
            state.resources.krowns / 500.0,
            state.resources.stone / 200.0,
            state.resources.lore / 200.0,
            state.resources.trophies / 200.0,
            float(state.units.villagers + state.units.woodcutters) / 30.0,
            float(state.units.trackers) / 20.0,
            float(state.warband_cap) / 20.0,
            float(len(state.lores)) / 10.0,
            float(len(state.hunter_nodes)) / 6.0,
            float(state.path_complete_purchases) / 10.0,
            float(state.colonized_zones) / 8.0,
            float(state.t) / 1200.0,
            float(state.units.mielikki + state.units.brundr + state.units.kaelinn) / 3.0,
        ],
        dtype=np.float32,
    )


def encode_states(states: Sequence[GameState]) -> np.ndarray:
    """Host-side feature matrix; uploaded in batched_heuristic_scores."""
    rows = [_features(s) for s in states]
    if not rows:
        return np.zeros((0, 15), dtype=np.float32)
    return np.stack(rows, axis=0)


def batched_heuristic_scores(
    feature_matrix: np.ndarray,
    weights: np.ndarray | None = None,
) -> cp.ndarray:
    """Linear heuristic on GPU: h = sum_i w_i x_i + b. Returns CuPy 1d array."""
    if weights is None:
        weights = np.array(
            [0.6, 0.5, 0.7, 0.2, 0.9, 0.8, 1.0, 2.2, 1.1, 1.4, 1.6, 1.0, 0.9, -0.15, 2.0],
            dtype=np.float32,
        )
    bias = cp.float32(0.5)
    gx = cp.asarray(feature_matrix, dtype=cp.float32)
    gw = cp.asarray(weights, dtype=cp.float32)
    return cp.sum(gx * gw, axis=1) + bias


def top_k_indices(scores: cp.ndarray, k: int) -> np.ndarray:
    """Argmax top-k on GPU; returns host indices for Python list indexing."""
    k = min(k, int(scores.shape[0]))
    if k < 1:
        return np.array([], dtype=np.int64)
    idx = cp.argsort(scores)[-k:]
    return cp.asnumpy(idx)


def batch_mean_combat_proxy(
    states: Sequence[GameState],
    tracker_weight: float = 3.0,
    hero_weight: float = 8.0,
) -> cp.ndarray:
    """Combat proxy vector on GPU."""
    n = len(states)
    if n == 0:
        return cp.array([], dtype=cp.float32)
    tr = cp.array([s.units.trackers for s in states], dtype=cp.float32)
    h = cp.array(
        [s.units.mielikki + s.units.brundr + s.units.kaelinn for s in states],
        dtype=cp.float32,
    )
    wm = cp.array([1.2 if "weaponsmith" in s.lores else 1.0 for s in states], dtype=cp.float32)
    pc = cp.array([1.0 + 0.05 * s.path_complete_purchases for s in states], dtype=cp.float32)
    tw = cp.float32(tracker_weight)
    hw = cp.float32(hero_weight)
    return tr * tw * wm * pc + h * hw


def scores_to_float_list(scores: cp.ndarray) -> List[float]:
    """Copy GPU scores to Python floats (e.g. single-state heuristic)."""
    a = cp.asnumpy(scores)
    return [float(a[i]) for i in range(a.shape[0])]
