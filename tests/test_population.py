from northgard.data_loader import load_json
from northgard.population import villager_spawn_interval_seconds


def test_spawn_interval_ordering():
    cal = load_json("economy")["spawn_calibration"]
    low_pop = villager_spawn_interval_seconds(5.0, 4, 0.0, 0.0, cal)
    high_pop = villager_spawn_interval_seconds(5.0, 20, 0.0, 0.0, cal)
    assert high_pop >= low_pop
