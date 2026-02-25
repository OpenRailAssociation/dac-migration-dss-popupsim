"""Process tracking events for wagon and locomotive operations."""

from dataclasses import dataclass
from dataclasses import field
from enum import Enum
from typing import Any

from infrastructure.events.base_event import DomainEvent


class ProcessType(Enum):
    """Process operation types."""

    COUPLING = 'coupling'
    DECOUPLING = 'decoupling'
    RETROFITTING = 'retrofitting'
    MOVING = 'moving'
    PARKING = 'parking'
    WAITING = 'waiting'
    MAINTENANCE = 'maintenance'


class ResourceType(Enum):
    """Resource types."""

    WAGON = 'wagon'
    LOCOMOTIVE = 'locomotive'


@dataclass(frozen=True)
class ProcessStartedEvent(DomainEvent):  # pylint: disable=too-many-instance-attributes
    """Process operation started.

    Note: Multiple attributes needed for comprehensive process tracking.
    """

    resource_id: str = ''
    resource_type: ResourceType = ResourceType.WAGON
    process_type: ProcessType = ProcessType.WAITING
    location: str = ''
    start_time: float = 0.0
    estimated_duration: float = 0.0
    batch_id: str | None = None
    additional_data: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ProcessCompletedEvent(DomainEvent):  # pylint: disable=too-many-instance-attributes
    """Process operation completed.

    Note: Multiple attributes needed for comprehensive process tracking.
    """

    resource_id: str = ''
    resource_type: ResourceType = ResourceType.WAGON
    process_type: ProcessType = ProcessType.WAITING
    location: str = ''
    start_time: float = 0.0
    end_time: float = 0.0
    actual_duration: float = 0.0
    batch_id: str | None = None
    additional_data: dict[str, Any] = field(default_factory=dict)
