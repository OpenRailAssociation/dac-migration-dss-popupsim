"""Domain events for wagon lifecycle orchestration."""

from dataclasses import dataclass
from dataclasses import field
from typing import Any

from infrastructure.events.base_event import DomainEvent
from shared.domain.entities.wagon import Wagon


@dataclass(frozen=True)
class TrainArrivedEvent(DomainEvent):
    """Train has arrived with wagons."""

    train_id: str = ''
    wagons: list[Wagon] = field(default_factory=list)
    arrival_track: str = ''
    event_timestamp: float = 0.0


@dataclass(frozen=True)
class WagonClassifiedEvent(DomainEvent):
    """Wagon has been classified in yard."""

    wagon: Any = None
    classification_track: str = ''


@dataclass(frozen=True)
class WagonsClassifiedEvent(DomainEvent):
    """Train wagons have been classified through hump yard."""

    train_id: str = ''
    accepted_wagons: list[Any] = field(default_factory=list)
    rejected_wagons: list[Any] = field(default_factory=list)


@dataclass(frozen=True)
class WagonsReadyForPickupEvent(DomainEvent):
    """Wagons are ready for pickup from collection track."""

    track_id: str = ''
    wagon_count: int = 0
    event_timestamp: float = 0.0


@dataclass(frozen=True)
class TrainDepartedEvent(DomainEvent):
    """Train has departed after wagon classification."""

    train_id: str = ''
    departure_time: float = 0.0
    wagon_count: int = 0


@dataclass(frozen=True)
class WagonReadyForRetrofitEvent(DomainEvent):
    """Wagon is ready for retrofit processing."""

    wagon: Any = None
    workshop_id: str = ''
    event_timestamp: float = 0.0


@dataclass(frozen=True)
class WagonRetrofittedEvent(DomainEvent):
    """Wagon has completed retrofit."""

    wagon: Any = None
    workshop_id: str = ''
    batch_id: str | None = None
    event_timestamp: float = 0.0


@dataclass(frozen=True)
class WagonRetrofitCompletedEvent(DomainEvent):
    """Wagon retrofit completed - for single source of truth updates."""

    wagon_id: str = ''
    completion_time: float = 0.0
    workshop_id: str = ''
    event_timestamp: float = 0.0


@dataclass(frozen=True)
class BatchRetrofittedEvent(DomainEvent):
    """All wagons in a batch have completed retrofit."""

    batch_id: str = ''
    wagons: list[Any] = field(default_factory=list)
    workshop_id: str = ''
    event_timestamp: float = 0.0


@dataclass(frozen=True)
class WagonReadyForParkingEvent(DomainEvent):
    """Wagon is ready to be moved to parking."""

    wagon: Any = None
    source_track: str = ''


@dataclass(frozen=True)
class LocomotiveMovementRequestEvent(DomainEvent):
    """Request locomotive movement for wagon transport."""

    wagons: list[Any] = field(default_factory=list)
    from_track: str = ''
    to_track: str = ''
    operation_type: str = ''  # 'pickup', 'delivery', 'parking'
