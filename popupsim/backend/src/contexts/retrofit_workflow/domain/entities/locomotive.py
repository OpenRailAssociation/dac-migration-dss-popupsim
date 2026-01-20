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
    _coupled_rakes: list[str] = field(default_factory=list, init=False)  # Multiple rakes
    _assembly_complete: bool = field(default=False, init=False)

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
    def coupled_rakes(self) -> list[str]:
        """Get list of coupled rake IDs."""
        return self._coupled_rakes.copy()

    @property
    def is_coupled(self) -> bool:
        """Check if locomotive has any coupled rakes."""
        return len(self._coupled_rakes) > 0

    @property
    def assembly_complete(self) -> bool:
        """Check if train assembly is complete."""
        return self._assembly_complete

    def assemble_rake(self, rake_id: str) -> None:
        """Assemble rake to locomotive.

        Args:
            rake_id: Rake to assemble

        Raises
        ------
            ValueError: If rake already assembled
        """
        if rake_id in self._coupled_rakes:
            raise ValueError(f'Rake {rake_id} already assembled to locomotive {self.id}')

        self._coupled_rakes.append(rake_id)

    def disassemble_rake(self, rake_id: str) -> None:
        """Disassemble rake from locomotive.

        Args:
            rake_id: Rake to disassemble

        Raises
        ------
            ValueError: If rake not assembled
        """
        if rake_id not in self._coupled_rakes:
            raise ValueError(f'Rake {rake_id} not assembled to locomotive {self.id}')

        self._coupled_rakes.remove(rake_id)
        if not self._coupled_rakes:
            self._assembly_complete = False

    def complete_assembly(self) -> None:
        """Mark train assembly as complete after brake test."""
        if not self._coupled_rakes:
            raise ValueError(f'Cannot complete assembly - no rakes coupled to locomotive {self.id}')

        self._assembly_complete = True

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
