from northgard.data_loader import load_json
from northgard.economy import update_month_and_winter_flags
from northgard.sim import initial_state


def test_winter_december_through_february():
    s = initial_state("standard_hostile")
    economy = load_json("economy")
    s.t = 9 * economy["seconds_per_month"]
    update_month_and_winter_flags(s, economy)
    assert s.in_winter is True
    assert s.month_index in economy["winter_month_indices"]
