"""Shunting operations domain events."""

from dataclasses import dataclass
from dataclasses import field
import time
import uuid


@dataclass(frozen=True)
class LocomotiveAllocatedEvent:
    """Event fired when locomotive is allocated."""

    locomotive_id: str
    allocated_to: str
    track: str
    event_timestamp: float
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)


@dataclass(frozen=True)
class LocomotiveReleasedEvent:
    """Event fired when locomotive is released."""

    locomotive_id: str
    released_from: str
    track: str
    event_timestamp: float
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)


@dataclass(frozen=True)
class ShuntingOperationCompletedEvent:  # pylint: disable=too-many-instance-attributes
    """Event fired when shunting operation completes."""

    locomotive_id: str
    operation_type: str
    track: str
    duration: float
    success: bool
    event_timestamp: float
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
