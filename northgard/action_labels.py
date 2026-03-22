"""Plain-language labels for optimizer / sim actions (for reports, not game strings)."""

from __future__ import annotations

from .actions import (
    Action,
    AssignWorker,
    Build,
    ClearNeutral,
    Colonize,
    PlaceLure,
    PurchasePathComplete,
    RecruitMielikki,
    RecruitTracker,
    SelectLore,
    SummonBrundr,
    SummonKaelinn,
    UnlockHunterNode,
    Upgrade,
    UpgradeTownHall,
    Wait,
)


def _zone(z: str) -> str:
    return f"**{z}**"


def describe_action(action: Action) -> str:
    """One-line English explanation for humans reading an optimizer plan."""
    if isinstance(action, Wait):
        return f"Pass time — advance the sim clock by **{action.seconds:g}** seconds (no build/recruit this step)."
    if isinstance(action, Build):
        return f"Build **{action.building_type.replace('_', ' ')}** in zone {_zone(action.zone_id)}."
    if isinstance(action, Upgrade):
        return f"Upgrade **{action.building_type.replace('_', ' ')}** in zone {_zone(action.zone_id)}."
    if isinstance(action, Colonize):
        return f"Colonize zone {_zone(action.zone_id)} — pay food cost and claim the tile."
    if isinstance(action, AssignWorker):
        return (
            f"Reassign workers: **{action.from_job}** → **{action.to_job}** "
            f"in zone {_zone(action.zone_id)}."
        )
    if isinstance(action, RecruitTracker):
        return f"Recruit a **Tracker** (uses warband / Archery Range) in zone {_zone(action.zone_id)}."
    if isinstance(action, RecruitMielikki):
        return f"Recruit **Mielikki** in zone {_zone(action.zone_id)}."
    if isinstance(action, SummonBrundr):
        return f"Summon **Brundr** in zone {_zone(action.zone_id)}."
    if isinstance(action, SummonKaelinn):
        return f"Summon **Kaelinn** in zone {_zone(action.zone_id)}."
    if isinstance(action, SelectLore):
        return f"Spend lore — unlock clan lore **{action.lore_id.replace('_', ' ')}**."
    if isinstance(action, UnlockHunterNode):
        return f"Hunter path — unlock node **{action.node_id.replace('_', ' ')}** (needs trophies / order)."
    if isinstance(action, PlaceLure):
        return f"Place lure (**{action.lure_type}**) in zone {_zone(action.zone_id)}."
    if isinstance(action, ClearNeutral):
        return f"Clear the neutral camp in zone {_zone(action.zone_id)} (fight + trophies)."
    if isinstance(action, UpgradeTownHall):
        return f"Upgrade **Town Hall** in zone {_zone(action.zone_id)}."
    if isinstance(action, PurchasePathComplete):
        return "Path of the Hunter — spend trophies for a **Path completion** purchase (tracker stat tiers)."
    return str(action)
