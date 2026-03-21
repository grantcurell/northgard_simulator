from northgard.recruitment import tracker_total_cost, tracker_unit_cost


def test_tracker_costs():
    assert tracker_unit_cost(1) == 25
    assert tracker_unit_cost(10) == 70
    assert tracker_total_cost(8) == 340
    assert tracker_total_cost(10) == 475
