from northgard.recruitment import cap_for_ranges


def test_archery_range_cap():
    assert cap_for_ranges(1, 0) == 2
    assert cap_for_ranges(1, 1) == 3
    assert cap_for_ranges(5, 2) == 12
