from northgard.actions import Wait
from northgard.horizon_playbook import (
    build_playbook_sections,
    compute_action_intervals,
    format_horizon_playbook_markdown,
)
def test_empty_actions_fills_passive_horizon():
    segs = build_playbook_sections([], 1200.0)
    assert len(segs) >= 1
    assert all(s["kind"] == "passive" for s in segs)
    assert abs(segs[0]["start"] - 0.0) < 1
    assert abs(segs[-1]["end"] - 1200.0) < 1


def test_playbook_markdown_mentions_full_horizon():
    segs = build_playbook_sections([], 1200.0)
    md = format_horizon_playbook_markdown(segs, 1200.0)
    assert "0:00" in md or "20:00" in md or "1200" in md or "20 min" in md.lower()


def test_compute_intervals_wait():
    intervals = compute_action_intervals("standard_hostile", [Wait(10.0)])
    assert len(intervals) == 1
    assert intervals[0]["t_end"] - intervals[0]["t_start"] == 10.0
