"""Dual-stream event system: separate state changes from location tracking."""

from dataclasses import dataclass
from enum import StrEnum


class ResourceState(StrEnum):
    """Resource states (what is happening)."""

    # Wagon states
    ARRIVED = 'arrived'
    WAITING = 'waiting'
    QUEUED = 'queued'
    IN_WORKSHOP = 'in_workshop'
    RETROFITTED = 'retrofitted'
    PARKED = 'parked'
    REJECTED = 'rejected'
    # Locomotive states
    IDLE = 'idle'
    ASSIGNED = 'assigned'
    MOVING = 'moving'


class ProcessState(StrEnum):
    """Process states (activities in progress)."""

    COUPLING_STARTED = 'coupling_started'
    COUPLING_COMPLETED = 'coupling_completed'
    DECOUPLING_STARTED = 'decoupling_started'
    DECOUPLING_COMPLETED = 'decoupling_completed'
    RAKE_COUPLING_STARTED = 'rake_coupling_started'
    RAKE_COUPLING_COMPLETED = 'rake_coupling_completed'
    RAKE_DECOUPLING_STARTED = 'rake_decoupling_started'
    RAKE_DECOUPLING_COMPLETED = 'rake_decoupling_completed'


@dataclass(frozen=True)
class StateChangeEvent:
    """State change event (WHAT is happening to the resource)."""

    timestamp: float
    resource_id: str
    resource_type: str  # 'wagon' or 'locomotive'
    state: ResourceState
    train_id: str | None = None
    batch_id: str | None = None
    rejection_reason: str | None = None


@dataclass(frozen=True)
class LocationChangeEvent:
    """Location change event (WHERE the resource is)."""

    timestamp: float
    resource_id: str
    resource_type: str  # 'wagon' or 'locomotive'
    location: str
    previous_location: str | None = None
    route_path: list[str] | None = None  # Full route path for MOVING state visualization


@dataclass(frozen=True)
class ProcessEvent:  # pylint: disable=too-many-instance-attributes
    """Process event (activities/operations in progress).

    Note: Multiple attributes needed for comprehensive process tracking.
    """

    timestamp: float
    resource_id: str
    resource_type: str
    process_state: ProcessState
    location: str
    coupler_type: str | None = None  # SCREW or DAC for coupling/decoupling
    batch_id: str | None = None
    rake_id: str | None = None
    locomotive_id: str | None = None
