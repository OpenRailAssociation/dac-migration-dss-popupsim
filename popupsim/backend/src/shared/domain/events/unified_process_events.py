"""Unified process tracking events for wagons and locomotives."""

from dataclasses import dataclass
from dataclasses import field
from enum import Enum
from typing import Any

from infrastructure.events.base_event import DomainEvent


class ProcessType(Enum):
    """Types of trackable processes."""

    COUPLING = 'coupling'
    DECOUPLING = 'decoupling'
    RETROFITTING = 'retrofitting'
    MOVING = 'moving'
    PARKING = 'parking'
    WAITING = 'waiting'
    LOADING = 'loading'
    UNLOADING = 'unloading'
    MAINTENANCE = 'maintenance'
    INSPECTION = 'inspection'


class ResourceType(Enum):
    """Types of resources that can be tracked."""

    WAGON = 'wagon'
    LOCOMOTIVE = 'locomotive'
    RAKE = 'rake'
    BATCH = 'batch'


@dataclass(frozen=True)
class ProcessStartedEvent(DomainEvent):  # pylint: disable=too-many-instance-attributes
    """Universal process start event for any resource.

    Note: Multiple attributes needed for comprehensive process tracking.
    """

    resource_id: str = ''
    resource_type: ResourceType = ResourceType.WAGON
    process_type: ProcessType = ProcessType.WAITING
    location: str = ''
    start_time: float = 0.0
    estimated_duration: float = 0.0

    # Context data
    batch_id: str | None = None
    rake_id: str | None = None
    locomotive_id: str | None = None
    workshop_id: str | None = None

    # Process-specific data
    additional_data: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ProcessCompletedEvent(DomainEvent):  # pylint: disable=too-many-instance-attributes
    """Universal process completion event for any resource.

    Note: Multiple attributes needed for comprehensive process tracking.
    """

    resource_id: str = ''
    resource_type: ResourceType = ResourceType.WAGON
    process_type: ProcessType = ProcessType.WAITING
    location: str = ''
    start_time: float = 0.0
    end_time: float = 0.0
    actual_duration: float = 0.0

    # Context data
    batch_id: str | None = None
    rake_id: str | None = None
    locomotive_id: str | None = None
    workshop_id: str | None = None

    # Process-specific data
    additional_data: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ProcessProgressEvent(DomainEvent):
    """Process progress update event."""

    resource_id: str = ''
    resource_type: ResourceType = ResourceType.WAGON
    process_type: ProcessType = ProcessType.WAITING
    location: str = ''
    progress_percentage: float = 0.0
    current_time: float = 0.0
    estimated_completion: float = 0.0


# Convenience events for specific processes
@dataclass(frozen=True)
class WagonCouplingStarted(ProcessStartedEvent):
    """Wagon coupling process started."""

    resource_type: ResourceType = field(default=ResourceType.WAGON, init=False)
    process_type: ProcessType = field(default=ProcessType.COUPLING, init=False)


@dataclass(frozen=True)
class WagonCouplingCompleted(ProcessCompletedEvent):
    """Wagon coupling process completed."""

    resource_type: ResourceType = field(default=ResourceType.WAGON, init=False)
    process_type: ProcessType = field(default=ProcessType.COUPLING, init=False)


@dataclass(frozen=True)
class LocomotiveMovingStarted(ProcessStartedEvent):
    """Locomotive moving process started."""

    resource_type: ResourceType = field(default=ResourceType.LOCOMOTIVE, init=False)
    process_type: ProcessType = field(default=ProcessType.MOVING, init=False)


@dataclass(frozen=True)
class LocomotiveMovingCompleted(ProcessCompletedEvent):
    """Locomotive moving process completed."""

    resource_type: ResourceType = field(default=ResourceType.LOCOMOTIVE, init=False)
    process_type: ProcessType = field(default=ProcessType.MOVING, init=False)
