"""Clean Wagon entity with enforced business rules."""

from dataclasses import dataclass
from dataclasses import field
from enum import Enum

from contexts.retrofit_workflow.domain.value_objects.coupler import Coupler
from contexts.retrofit_workflow.domain.value_objects.coupler import CouplerType


class WagonStatus(Enum):
    """Wagon status with clear state transitions."""

    ARRIVED = 'ARRIVED'
    CLASSIFIED = 'CLASSIFIED'
    READY_FOR_RETROFIT = 'READY_FOR_RETROFIT'
    RETROFITTING = 'RETROFITTING'
    RETROFITTED = 'RETROFITTED'
    PARKED = 'PARKED'


@dataclass
class Wagon:  # pylint: disable=too-many-instance-attributes
    """Wagon entity with enforced business rules.

    This is a CLEAN entity that:
    - Enforces state transitions
    - Validates business rules
    - Provides type safety
    - Is testable without SimPy

    Attributes
    ----------
        id: Unique wagon identifier
        length: Wagon length in meters (float)
        coupler_type: Type of coupler (SCREW or DAC)
        train_id: ID of train this wagon arrived with
    """

    id: str
    length: float  # meters
    coupler_a: Coupler  # Side A coupler
    coupler_b: Coupler  # Side B coupler
    train_id: str | None = None

    # Private state - use methods to modify
    _status: WagonStatus = field(default=WagonStatus.ARRIVED, init=False)
    _location: str | None = field(default=None, init=False)

    # Retrofit tracking
    retrofit_start_time: float | None = field(default=None, init=False)
    retrofit_end_time: float | None = field(default=None, init=False)
    workshop_id: str | None = field(default=None, init=False)

    # Rake tracking
    rake_id: str | None = field(default=None, init=False)
    batch_id: str | None = field(default=None, init=False)

    @property
    def status(self) -> WagonStatus:
        """Get wagon status."""
        return self._status

    @property
    def location(self) -> str | None:
        """Get wagon location (track ID)."""
        return self._location

    @property
    def needs_retrofit(self) -> bool:
        """Check if wagon needs retrofit."""
        return self._status in (
            WagonStatus.CLASSIFIED,
            WagonStatus.READY_FOR_RETROFIT,
        )

    @property
    def is_retrofitted(self) -> bool:
        """Check if wagon is retrofitted."""
        return self._status in (WagonStatus.RETROFITTED, WagonStatus.PARKED)

    def move_to(self, track_id: str) -> None:
        """Move wagon to track.

        Args:
            track_id: Target track identifier
        """
        self._location = track_id

    def classify(self) -> None:
        """Classify wagon after arrival.

        Raises
        ------
            ValueError: If wagon not in ARRIVED status
        """
        if self._status != WagonStatus.ARRIVED:
            raise ValueError(f'Cannot classify wagon {self.id} in status {self._status}')
        self._status = WagonStatus.CLASSIFIED

    def prepare_for_retrofit(self) -> None:
        """Prepare wagon for retrofit.

        Raises
        ------
            ValueError: If wagon not in CLASSIFIED status
        """
        if self._status != WagonStatus.CLASSIFIED:
            raise ValueError(f'Cannot prepare wagon {self.id} in status {self._status}')
        self._status = WagonStatus.READY_FOR_RETROFIT

    def start_retrofit(self, workshop_id: str, start_time: float) -> None:
        """Start retrofit operation.

        Args:
            workshop_id: Workshop performing retrofit
            start_time: Simulation time when retrofit starts

        Raises
        ------
            ValueError: If wagon not ready for retrofit
        """
        if self._status != WagonStatus.READY_FOR_RETROFIT:
            raise ValueError(f'Cannot start retrofit for wagon {self.id} in status {self._status}')
        self._status = WagonStatus.RETROFITTING
        self._location = workshop_id
        self.workshop_id = workshop_id
        self.retrofit_start_time = start_time

    def complete_retrofit(self, end_time: float) -> None:
        """Complete retrofit operation.

        Changes coupler types from SCREW to DAC and updates status.

        Args:
            end_time: Simulation time when retrofit completes

        Raises
        ------
            ValueError: If wagon not retrofitting
        """
        if self._status != WagonStatus.RETROFITTING:
            raise ValueError(f'Cannot complete retrofit for wagon {self.id} in status {self._status}')

        # Change couplers from SCREW to DAC
        self.coupler_a = Coupler(CouplerType.DAC, self.coupler_a.side)
        self.coupler_b = Coupler(CouplerType.DAC, self.coupler_b.side)

        self._status = WagonStatus.RETROFITTED
        self.retrofit_end_time = end_time

    def park(self, parking_track: str) -> None:
        """Park wagon after retrofit.

        Args:
            parking_track: Parking track identifier

        Raises
        ------
            ValueError: If wagon not retrofitted
        """
        if self._status != WagonStatus.RETROFITTED:
            raise ValueError(f'Cannot park wagon {self.id} in status {self._status}')
        self._status = WagonStatus.PARKED
        self._location = parking_track

    def __repr__(self) -> str:
        """Return string representation."""
        return f'Wagon(id={self.id}, status={self._status.value}, location={self._location}, length={self.length}m)'
