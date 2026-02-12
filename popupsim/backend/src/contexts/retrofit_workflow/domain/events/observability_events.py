"""Event definitions for observability tracking."""

from dataclasses import dataclass


@dataclass
class WagonJourneyEvent:  # pylint: disable=too-many-instance-attributes
    """Tracks wagon state changes throughout the simulation."""

    timestamp: float
    wagon_id: str
    event_type: str  # ARRIVED, REJECTED, ON_RETROFIT_TRACK, AT_WORKSHOP, RETROFIT_STARTED, RETROFIT_COMPLETED, PARKED
    location: str
    status: str
    train_id: str | None = None
    rejection_reason: str | None = None
    rejection_description: str | None = None


@dataclass
class LocomotiveMovementEvent:
    """Tracks locomotive movements and allocations."""

    timestamp: float
    locomotive_id: str
    event_type: str  # ALLOCATED, MOVING, ARRIVED, RELEASED
    from_location: str | None = None
    to_location: str | None = None
    purpose: str | None = None
    current_location: str | None = None


@dataclass
class ResourceStateChangeEvent:  # pylint: disable=too-many-instance-attributes
    """Tracks resource utilization changes when they happen."""

    timestamp: float
    resource_type: str  # "track", "locomotive", "workshop"
    resource_id: str
    change_type: (
        str  # "capacity_reserved", "capacity_released", "allocated", "released", "bay_occupied", "bay_released"
    )

    # For tracks
    capacity: float | None = None
    used_before: float | None = None
    used_after: float | None = None
    change_amount: float | None = None
    utilization_before_percent: float | None = None
    utilization_after_percent: float | None = None

    # For locomotives
    total_count: int | None = None
    busy_count_before: int | None = None
    busy_count_after: int | None = None

    # For workshops
    total_bays: int | None = None
    busy_bays_before: int | None = None
    busy_bays_after: int | None = None

    # Context
    triggered_by: str | None = None


@dataclass
class LocomotiveAssemblyEvent:  # pylint: disable=too-many-instance-attributes
    """Tracks locomotive assembly operations."""

    timestamp: float
    locomotive_id: str
    event_type: str  # RAKE_COUPLED, RAKE_DECOUPLED, BRAKE_TEST_STARTED, BRAKE_TEST_COMPLETED, ASSEMBLY_COMPLETED
    rake_id: str | None = None
    coupler_type: str | None = None
    total_rakes: int | None = None
    duration: float | None = None
    location: str | None = None


class RejectionReason:  # pylint: disable=too-few-public-methods
    """Standard rejection reasons with human-readable descriptions."""

    ALREADY_HAS_DAC = ('already_has_dac', 'Wagon already equipped with DAC coupler')

    NOT_ELIGIBLE = ('not_eligible', 'Wagon type not eligible for DAC retrofit')

    TRACK_FULL = ('collection_track_full', 'Collection track at capacity, no space available')

    NO_COUPLER_COMPATIBILITY = ('incompatible_coupler', 'Coupler type incompatible with retrofit process')
