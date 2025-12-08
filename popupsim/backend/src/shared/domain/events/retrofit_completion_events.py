"""Events for retrofit completion coordination."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from infrastructure.events.base_event import DomainEvent

if TYPE_CHECKING:
    from shared.domain.entities.wagon import Wagon


@dataclass(frozen=True)
class RakeRetrofitCompletedEvent(DomainEvent):
    """Event published when all wagons in a rake have completed retrofit."""

    rake_id: str = ""
    workshop_id: str = ""
    completed_wagons: list[Wagon] = field(default_factory=list)  # type: ignore[assignment]
    completion_time: float = 0.0


@dataclass(frozen=True)
class WorkshopReadyForPickupEvent(DomainEvent):
    """Event published when workshop has wagons ready for pickup."""

    workshop_id: str = ""
    ready_wagons: list[Wagon] = field(default_factory=list)  # type: ignore[assignment]
    wagon_count: int = 0
