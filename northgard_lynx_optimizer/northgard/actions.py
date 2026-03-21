from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Union


class Action:
    pass


@dataclass(frozen=True)
class Build(Action):
    building_type: str
    zone_id: str


@dataclass(frozen=True)
class Upgrade(Action):
    building_type: str
    zone_id: str


@dataclass(frozen=True)
class Colonize(Action):
    zone_id: str


@dataclass(frozen=True)
class AssignWorker(Action):
    from_job: str
    to_job: str
    zone_id: str


@dataclass(frozen=True)
class RecruitTracker(Action):
    zone_id: str


@dataclass(frozen=True)
class RecruitMielikki(Action):
    zone_id: str


@dataclass(frozen=True)
class SummonBrundr(Action):
    zone_id: str


@dataclass(frozen=True)
class SummonKaelinn(Action):
    zone_id: str


@dataclass(frozen=True)
class SelectLore(Action):
    lore_id: str


@dataclass(frozen=True)
class UnlockHunterNode(Action):
    node_id: str


@dataclass(frozen=True)
class PlaceLure(Action):
    zone_id: str
    lure_type: str


@dataclass(frozen=True)
class ClearNeutral(Action):
    zone_id: str


@dataclass(frozen=True)
class UpgradeTownHall(Action):
    zone_id: str


@dataclass(frozen=True)
class PurchasePathComplete(Action):
    pass


@dataclass(frozen=True)
class Wait(Action):
    seconds: float


ActionType = Union[
    Build,
    Upgrade,
    Colonize,
    AssignWorker,
    RecruitTracker,
    RecruitMielikki,
    SummonBrundr,
    SummonKaelinn,
    SelectLore,
    UnlockHunterNode,
    PlaceLure,
    ClearNeutral,
    UpgradeTownHall,
    PurchasePathComplete,
    Wait,
]
