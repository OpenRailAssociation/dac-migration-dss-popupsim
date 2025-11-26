"""Workshop-related domain events."""

from dataclasses import dataclass

from .base_event import DomainEvent


@dataclass(frozen=True)
class WorkshopStationOccupiedEvent(DomainEvent):
    """Event when workshop station becomes occupied."""

    workshop_id: str
    station_id: str


@dataclass(frozen=True)
class WorkshopStationIdleEvent(DomainEvent):
    """Event when workshop station becomes idle."""

    workshop_id: str
    station_id: str


@dataclass(frozen=True)
class WorkshopCapacityChangedEvent(DomainEvent):
    """Event when workshop capacity changes."""

    workshop_id: str
    available_capacity: int
