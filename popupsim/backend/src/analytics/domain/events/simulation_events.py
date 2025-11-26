"""Simulation-related domain events."""

from dataclasses import dataclass

from .base_event import DomainEvent


@dataclass(frozen=True)
class WagonDeliveredEvent(DomainEvent):
    """Event when wagon is delivered to workshop."""

    wagon_id: str


@dataclass(frozen=True)
class WagonRetrofittedEvent(DomainEvent):
    """Event when wagon retrofit is completed."""

    wagon_id: str
    workshop_id: str
    processing_duration: float  # minutes


@dataclass(frozen=True)
class WagonRejectedEvent(DomainEvent):
    """Event when wagon is rejected."""

    wagon_id: str
    reason: str


@dataclass(frozen=True)
class WorkshopUtilizationChangedEvent(DomainEvent):
    """Event when workshop utilization changes."""

    workshop_id: str
    utilization_percent: float
    available_stations: int


@dataclass(frozen=True)
class BottleneckDetectedEvent(DomainEvent):
    """Event when bottleneck is detected."""

    location: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    impact_description: str
