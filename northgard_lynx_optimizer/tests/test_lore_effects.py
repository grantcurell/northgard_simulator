from northgard.lore import sharp_axes_mult, weaponsmith_mult


def test_lore_mods():
    assert sharp_axes_mult(False) == 1.0
    assert sharp_axes_mult(True) == 1.2
    assert weaponsmith_mult(True) == 1.2
