import numpy as np

from northgard.gpu_ops import batched_heuristic_scores, encode_states, scores_to_float_list
from northgard.sim import initial_state


def test_gpu_batch_scores():
    states = [initial_state("standard_hostile") for _ in range(16)]
    feats = encode_states(states)
    assert feats.shape[0] == 16
    scores = batched_heuristic_scores(feats)
    assert scores.shape == (16,)
    host = np.asarray(scores_to_float_list(scores))
    assert np.all(np.isfinite(host))
