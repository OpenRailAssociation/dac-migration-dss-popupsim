"""Journey timeline events - pure state changes separate from process tracking."""

from dataclasses import dataclass
from enum import Enum

from infrastructure.events.base_event import DomainEvent


class WagonState(Enum):
    """Wagon states in the system."""

    ARRIVED = 'arrived'
    CLASSIFIED = 'classified'
    QUEUED = 'queued'
    ASSIGNED = 'assigned'
    IN_WORKSHOP = 'in_workshop'
    RETROFITTED = 'retrofitted'
    PARKED = 'parked'
    REJECTED = 'rejected'
    DEPARTED = 'departed'


class LocomotiveState(Enum):
    """Locomotive states in the system."""

    IDLE = 'idle'
    ASSIGNED = 'assigned'
    MOVING = 'moving'
    COUPLING = 'coupling'
    DECOUPLING = 'decoupling'
    MAINTENANCE = 'maintenance'


@dataclass(frozen=True)
class WagonStateChangedEvent(DomainEvent):  # pylint: disable=too-many-instance-attributes
    """Wagon state change event - pure state tracking.

    Note: Multiple attributes needed for comprehensive state tracking.
    """

    wagon_id: str = ''
    previous_state: WagonState | None = None
    new_state: WagonState = WagonState.ARRIVED
    location: str = ''
    timestamp: float = 0.0

    # Context for state change
    train_id: str | None = None
    batch_id: str | None = None
    workshop_id: str | None = None
    rejection_reason: str | None = None


@dataclass(frozen=True)
class LocomotiveStateChangedEvent(DomainEvent):
    """Locomotive state change event - pure state tracking."""

    locomotive_id: str = ''
    previous_state: LocomotiveState | None = None
    new_state: LocomotiveState = LocomotiveState.IDLE
    location: str = ''
    timestamp: float = 0.0

    # Context for state change
    assigned_task: str | None = None
    wagon_count: int = 0


@dataclass(frozen=True)
class WagonLocationChangedEvent(DomainEvent):
    """Wagon location change event - track movement."""

    wagon_id: str = ''
    previous_location: str | None = None
    new_location: str = ''
    timestamp: float = 0.0
    movement_type: str = 'shunting'  # 'shunting', 'classification', 'transport'


@dataclass(frozen=True)
class LocomotiveLocationChangedEvent(DomainEvent):
    """Locomotive location change event - track movement."""

    locomotive_id: str = ''
    previous_location: str | None = None
    new_location: str = ''
    timestamp: float = 0.0
    operation_type: str = 'movement'  # 'movement', 'positioning', 'return'


# Journey milestone events
@dataclass(frozen=True)
class WagonJourneyStartedEvent(DomainEvent):
    """Wagon journey started in the system."""

    wagon_id: str = ''
    train_id: str = ''
    arrival_time: float = 0.0
    arrival_track: str = ''


@dataclass(frozen=True)
class WagonJourneyCompletedEvent(DomainEvent):
    """Wagon journey completed (parked or departed)."""

    wagon_id: str = ''
    completion_time: float = 0.0
    final_location: str = ''
    final_state: WagonState = WagonState.PARKED
    total_journey_time: float = 0.0


@dataclass(frozen=True)
class LocomotiveTaskStartedEvent(DomainEvent):
    """Locomotive task assignment started."""

    locomotive_id: str = ''
    task_type: str = ''  # 'pickup', 'delivery', 'shunting', 'positioning'
    start_time: float = 0.0
    start_location: str = ''
    wagon_ids: list[str] | None = None

    def __post_init__(self) -> None:
        """Initialize mutable default values."""
        if self.wagon_ids is None:
            object.__setattr__(self, 'wagon_ids', [])


@dataclass(frozen=True)
class LocomotiveTaskCompletedEvent(DomainEvent):
    """Locomotive task completed."""

    locomotive_id: str = ''
    task_type: str = ''
    completion_time: float = 0.0
    completion_location: str = ''
    task_duration: float = 0.0
    wagon_ids: list[str] | None = None

    def __post_init__(self) -> None:
        """Initialize mutable default values."""
        if self.wagon_ids is None:
            object.__setattr__(self, 'wagon_ids', [])
