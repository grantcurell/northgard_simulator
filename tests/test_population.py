from northgard.data_loader import load_json
from northgard.population import (
    villager_spawn_days_happiness_page_candidate,
    villager_spawn_interval_seconds,
    villager_spawn_interval_seconds_happiness_page_candidate,
)


def test_spawn_interval_ordering():
    cal = load_json("economy")["spawn_calibration"]
    low_pop = villager_spawn_interval_seconds(5.0, 4, 0.0, 0.0, cal)
    high_pop = villager_spawn_interval_seconds(5.0, 20, 0.0, 0.0, cal)
    assert high_pop >= low_pop


def test_happiness_page_candidate_example_order_of_magnitude():
    """Wiki claims ~31 days at pop 10, happiness 2 (V1 — not authoritative)."""
    days = villager_spawn_days_happiness_page_candidate(2.0, 10)
    assert 25.0 < days < 38.0
    sec = villager_spawn_interval_seconds_happiness_page_candidate(2.0, 10, 2.0, 0.0, 0.0)
    assert sec > 50.0
