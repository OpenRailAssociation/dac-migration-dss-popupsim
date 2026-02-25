"""Detailed wagon process events for tracking all time-consuming operations."""

from dataclasses import dataclass
from dataclasses import field

from infrastructure.events.base_event import DomainEvent


@dataclass(frozen=True)
class ProcessStartedEvent(DomainEvent):
    """Base event for process start."""

    wagon_id: str = ''
    process_type: str = ''  # 'coupling', 'decoupling', 'retrofitting', 'moving', 'parking'
    location: str = ''  # track_id or workshop_id
    start_time: float = 0.0
    estimated_duration: float = 0.0
    batch_id: str | None = None


@dataclass(frozen=True)
class ProcessCompletedEvent(DomainEvent):
    """Base event for process completion."""

    wagon_id: str = ''
    process_type: str = ''
    location: str = ''
    start_time: float = 0.0
    end_time: float = 0.0
    actual_duration: float = 0.0
    batch_id: str | None = None


@dataclass(frozen=True)
class CouplingStartedEvent(ProcessStartedEvent):
    """Coupling process started."""

    process_type: str = field(default='coupling', init=False)
    rake_id: str = ''
    wagon_count: int = 0


@dataclass(frozen=True)
class CouplingCompletedEvent(ProcessCompletedEvent):
    """Coupling process completed."""

    process_type: str = field(default='coupling', init=False)
    rake_id: str = ''
    wagon_count: int = 0


@dataclass(frozen=True)
class DecouplingStartedEvent(ProcessStartedEvent):
    """Decoupling process started."""

    process_type: str = field(default='decoupling', init=False)
    rake_id: str = ''
    wagon_count: int = 0


@dataclass(frozen=True)
class DecouplingCompletedEvent(ProcessCompletedEvent):
    """Decoupling process completed."""

    process_type: str = field(default='decoupling', init=False)
    rake_id: str = ''
    wagon_count: int = 0


@dataclass(frozen=True)
class RetrofittingStartedEvent(ProcessStartedEvent):
    """Retrofitting process started."""

    process_type: str = field(default='retrofitting', init=False)
    workshop_id: str = ''
    batch_size: int = 1


@dataclass(frozen=True)
class RetrofittingCompletedEvent(ProcessCompletedEvent):
    """Retrofitting process completed."""

    process_type: str = field(default='retrofitting', init=False)
    workshop_id: str = ''
    batch_size: int = 1


@dataclass(frozen=True)
class MovingStartedEvent(ProcessStartedEvent):
    """Moving process started."""

    process_type: str = field(default='moving', init=False)
    from_location: str = ''
    to_location: str = ''
    locomotive_id: str = ''
    wagon_count: int = 1


@dataclass(frozen=True)
class MovingCompletedEvent(ProcessCompletedEvent):
    """Moving process completed."""

    process_type: str = field(default='moving', init=False)
    from_location: str = ''
    to_location: str = ''
    locomotive_id: str = ''
    wagon_count: int = 1


@dataclass(frozen=True)
class ParkingStartedEvent(ProcessStartedEvent):
    """Parking process started."""

    process_type: str = field(default='parking', init=False)
    parking_track: str = ''


@dataclass(frozen=True)
class ParkingCompletedEvent(ProcessCompletedEvent):
    """Parking process completed."""

    process_type: str = field(default='parking', init=False)
    parking_track: str = ''


@dataclass(frozen=True)
class WaitingStartedEvent(ProcessStartedEvent):
    """Waiting process started (queue, resource unavailable)."""

    process_type: str = field(default='waiting', init=False)
    waiting_reason: str = ''  # 'queue', 'resource_unavailable', 'track_occupied'


@dataclass(frozen=True)
class WaitingCompletedEvent(ProcessCompletedEvent):
    """Waiting process completed."""

    process_type: str = field(default='waiting', init=False)
    waiting_reason: str = ''
