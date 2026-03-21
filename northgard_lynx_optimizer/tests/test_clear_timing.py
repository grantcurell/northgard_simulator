from northgard.clearing import estimate_clear_result
from northgard.sim import initial_state


def test_clear_returns_keys():
    s = initial_state("standard_hostile")
    r = estimate_clear_result({"attack_power": 20.0}, "wolves_2", s)
    assert "clear_time_sec" in r
    assert "trophies_gained" in r
