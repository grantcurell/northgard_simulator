from northgard.combat_eval import supply_attack_defense_multiplier, supply_malus_fraction
from northgard.sim import initial_state


def test_supply_malus_table():
    assert supply_malus_fraction(1, 0) == 0.0
    assert abs(supply_malus_fraction(2, 0) - 0.05) < 1e-9
    assert abs(supply_malus_fraction(3, 0) - 0.15) < 1e-9
    assert abs(supply_malus_fraction(5, 0) - 0.30) < 1e-9


def test_wild_hunter_ignores_supply():
    s = initial_state("standard_hostile")
    s.hunter_nodes.add("wild_hunter")
    ctx = {"supply_distance_tiles": 4, "campaign_year_index": 0}
    assert supply_attack_defense_multiplier(s, ctx) == 1.0
