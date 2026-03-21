from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(order=True)
class ScheduledEvent:
    t: float
    kind: str
    payload: Any
