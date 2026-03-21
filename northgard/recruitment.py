from __future__ import annotations


def tracker_unit_cost(nth_tracker: int) -> int:
    return 25 + 5 * (nth_tracker - 1)


def tracker_total_cost(n: int) -> int:
    return sum(tracker_unit_cost(i) for i in range(1, n + 1))


def cap_for_ranges(ranges: int, upgraded: int) -> int:
    return ranges * 2 + upgraded
