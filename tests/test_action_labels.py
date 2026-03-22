from northgard.action_labels import describe_action
from northgard.actions import Build, Wait


def test_describe_wait():
    assert "Pass time" in describe_action(Wait(15.0))
    assert "15" in describe_action(Wait(15.0))


def test_describe_build():
    s = describe_action(Build("archery_range", "main"))
    assert "archery" in s.lower() or "Archery" in s
    assert "main" in s
