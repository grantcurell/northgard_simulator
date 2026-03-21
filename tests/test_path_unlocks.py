from northgard.trophies import can_unlock_next_node


def test_path_unlocks():
    assert can_unlock_next_node(30.0, 0) is True
    assert can_unlock_next_node(29.0, 0) is False
