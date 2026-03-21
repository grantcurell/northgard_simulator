from northgard.buildings import house_capacity


def test_house_capacity():
    assert house_capacity(base=6, total_houses=2, upgraded_houses=0) == 16
    assert house_capacity(base=6, total_houses=2, upgraded_houses=1) == 19
