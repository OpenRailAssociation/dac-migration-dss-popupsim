"""Clean Locomotive entity with enforced business rules."""

from dataclasses import dataclass
from dataclasses import field
from enum import Enum

from contexts.retrofit_workflow.domain.value_objects.coupler import Coupler


class LocomotiveStatus(Enum):
    """Locomotive status enum."""

    PARKING = 'PARKING'
    MOVING = 'MOVING'
    COUPLING = 'COUPLING'
    DECOUPLING = 'DECOUPLING'


@dataclass(order=True)
class Locomotive:  # pylint: disable=too-many-instance-attributes
    """Locomotive entity with enforced business rules.

    Attributes
    ----------
        id: Unique locomotive identifier
        home_track: Home parking track
        max_capacity: Maximum number of wagons
    """

    id: str
    home_track: str
    coupler_front: Coupler  # Front coupler
    coupler_back: Coupler  # Back coupler
    max_capacity: int = 100

    # Private state
    _current_track: str = field(default='', init=False)
    _status: LocomotiveStatus = field(default=LocomotiveStatus.PARKING, init=False)
    _coupled_rake_id: str | None = field(default=None, init=False)  # References Rake!

    def __post_init__(self) -> None:
        """Initialize current track to home track."""
        if not self._current_track:
            self._current_track = self.home_track

    @property
    def current_track(self) -> str:
        """Get current track."""
        return self._current_track

    @property
    def status(self) -> LocomotiveStatus:
        """Get locomotive status."""
        return self._status

    @property
    def coupled_rake_id(self) -> str | None:
        """Get coupled rake ID."""
        return self._coupled_rake_id

    @property
    def is_coupled(self) -> bool:
        """Check if locomotive has coupled rake."""
        return self._coupled_rake_id is not None

    def couple_rake(self, rake_id: str) -> None:
        """Couple rake to locomotive.

        A rake is already coupled (wagons coupled to each other).
        Locomotive couples to the rake as a unit.

        Args:
            rake_id: Rake to couple

        Raises
        ------
            ValueError: If already coupled
        """
        if self._coupled_rake_id:
            raise ValueError(f'Locomotive {self.id} already has coupled rake {self._coupled_rake_id}. Decouple first.')

        self._coupled_rake_id = rake_id

    def decouple_rake(self) -> str:
        """Decouple rake from locomotive.

        Returns
        -------
            Rake ID that was decoupled

        Raises
        ------
            ValueError: If no rake coupled
        """
        if not self._coupled_rake_id:
            raise ValueError(f'Locomotive {self.id} has no coupled rake')

        rake_id = self._coupled_rake_id
        self._coupled_rake_id = None

        return rake_id

    def start_movement(self, _to_track: str) -> None:
        """Start movement to track.

        Parameters
        ----------
        _to_track : str
            Destination track identifier (unused in current implementation)

        Notes
        -----
        Currently only changes status to MOVING. Future implementations
        may use the destination track for route planning.
        """
        self._status = LocomotiveStatus.MOVING

    def arrive_at(self, track: str) -> None:
        """Arrive at track.

        Args:
            track: Track where locomotive arrived
        """
        self._current_track = track
        self._status = LocomotiveStatus.PARKING

    def start_coupling(self) -> None:
        """Start coupling operation."""
        self._status = LocomotiveStatus.COUPLING

    def start_decoupling(self) -> None:
        """Start decoupling operation."""
        self._status = LocomotiveStatus.DECOUPLING

    def finish_operation(self) -> None:
        """Finish coupling/decoupling operation."""
        self._status = LocomotiveStatus.MOVING

    def __repr__(self) -> str:
        """Return string representation."""
        return f'Locomotive(id={self.id}, status={self._status.value}, track={self._current_track})'
