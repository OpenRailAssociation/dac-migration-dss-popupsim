"""Train Movement Aggregate - locomotive + rake for transport operations."""

from dataclasses import dataclass
from dataclasses import field
from enum import Enum
from typing import Any

from contexts.retrofit_workflow.domain.aggregates.batch_aggregate import BatchAggregate
from contexts.retrofit_workflow.domain.entities.locomotive import Locomotive
from shared.infrastructure.simpy_time_converters import timedelta_to_sim_ticks


class TrainType(Enum):
    """Train type enumeration for different operational modes."""

    MAINLINE = 'MAINLINE'  # Full brake test + inspection required
    SHUNTING = 'SHUNTING'  # Yard shunting - coupling + preparation only


class TrainMovementStatus(Enum):
    """Train movement status enumeration."""

    FORMING = 'FORMING'  # Train being assembled
    READY = 'READY'  # Ready for departure
    IN_TRANSIT = 'IN_TRANSIT'  # Moving between locations
    ARRIVED = 'ARRIVED'  # Arrived at destination
    DISSOLVED = 'DISSOLVED'  # Train dissolved (loco + rake separated)


@dataclass
class TrainMovement:  # pylint: disable=too-many-instance-attributes
    """Aggregate root for locomotive + rake transport operations.

    Represents a complete train (locomotive + rake) for transport between locations.
    Handles both mainline operations (with brake test + inspection) and yard shunting
    (simplified coupling only).

    Attributes
    ----------
        id: Unique train movement identifier
        locomotive: Locomotive pulling the train
        batch: BatchAggregate (rake of wagons)
        train_type: MAINLINE or SHUNTING
        origin: Starting location
        destination: Target location
    """

    id: str
    locomotive: Locomotive
    batch: BatchAggregate
    train_type: TrainType
    origin: str
    destination: str

    # Private state
    _status: TrainMovementStatus = field(default=TrainMovementStatus.FORMING, init=False)
    _brake_test_completed: bool = field(default=False, init=False)
    _inspection_completed: bool = field(default=False, init=False)
    _formation_time: float | None = field(default=None, init=False)
    _departure_time: float | None = field(default=None, init=False)
    _arrival_time: float | None = field(default=None, init=False)

    @property
    def status(self) -> TrainMovementStatus:
        """Get train movement status."""
        return self._status

    @property
    def wagon_count(self) -> int:
        """Get number of wagons in train."""
        return self.batch.wagon_count

    @property
    def total_length(self) -> float:
        """Get total length of train (locomotive + wagons)."""
        loco_length = self.locomotive.length if hasattr(self.locomotive, 'length') else 20.0
        return loco_length + self.batch.total_length

    @property
    def is_mainline(self) -> bool:
        """Check if this is a mainline train."""
        return self.train_type == TrainType.MAINLINE

    @property
    def is_shunting(self) -> bool:
        """Check if this is a shunting movement."""
        return self.train_type == TrainType.SHUNTING

    def complete_brake_test(self, current_time: float) -> None:  # noqa: ARG002
        """Complete brake test (mainline only).

        Args:
            current_time: Current simulation time

        Raises
        ------
            ValueError: If not mainline train or wrong status
        """
        if not self.is_mainline:
            raise ValueError(f'Brake test not required for {self.train_type.value} train {self.id}')

        if self._status != TrainMovementStatus.FORMING:
            raise ValueError(f'Cannot complete brake test for train {self.id} in status {self._status.value}')

        self._brake_test_completed = True

    def complete_inspection(self, current_time: float) -> None:  # noqa: ARG002
        """Complete inspection (mainline only).

        Args:
            current_time: Current simulation time

        Raises
        ------
            ValueError: If not mainline train or wrong status
        """
        if not self.is_mainline:
            raise ValueError(f'Inspection not required for {self.train_type.value} train {self.id}')

        if self._status != TrainMovementStatus.FORMING:
            raise ValueError(f'Cannot complete inspection for train {self.id} in status {self._status.value}')

        self._inspection_completed = True

    def mark_ready_for_departure(self, current_time: float) -> None:
        """Mark train as ready for departure.

        Args:
            current_time: Current simulation time

        Raises
        ------
            ValueError: If train not ready (missing brake test/inspection for mainline)
        """
        if not self.is_ready_for_departure():
            missing = []
            if self.is_mainline:
                if not self._brake_test_completed:
                    missing.append('brake test')
                if not self._inspection_completed:
                    missing.append('inspection')
            raise ValueError(f'Train {self.id} not ready for departure. Missing: {", ".join(missing)}')

        self._status = TrainMovementStatus.READY
        self._formation_time = current_time

    def depart(self, current_time: float) -> None:
        """Mark train as departed.

        Args:
            current_time: Current simulation time

        Raises
        ------
            ValueError: If train not ready
        """
        if self._status != TrainMovementStatus.READY:
            raise ValueError(f'Train {self.id} not ready for departure. Current status: {self._status.value}')

        self._status = TrainMovementStatus.IN_TRANSIT
        self._departure_time = current_time

    def arrive(self, current_time: float) -> None:
        """Mark train as arrived at destination.

        Args:
            current_time: Current simulation time

        Raises
        ------
            ValueError: If train not in transit
        """
        if self._status != TrainMovementStatus.IN_TRANSIT:
            raise ValueError(f'Train {self.id} not in transit. Current status: {self._status.value}')

        self._status = TrainMovementStatus.ARRIVED
        self._arrival_time = current_time

    def dissolve(self) -> tuple[Locomotive, BatchAggregate]:
        """Dissolve train and return locomotive and batch separately.

        Returns
        -------
            Tuple of (locomotive, batch)

        Raises
        ------
            ValueError: If train not arrived
        """
        if self._status != TrainMovementStatus.ARRIVED:
            raise ValueError(f'Cannot dissolve train {self.id} in status {self._status.value}')

        self._status = TrainMovementStatus.DISSOLVED
        return self.locomotive, self.batch

    def is_ready_for_departure(self) -> bool:
        """Check if train is ready to depart.

        Returns
        -------
            True if ready, False otherwise
        """
        if self.is_shunting:
            return True  # Shunting always ready after coupling

        # Mainline requires brake test and inspection
        return self._brake_test_completed and self._inspection_completed

    def get_preparation_time(self, process_times: Any) -> float:
        """Calculate total preparation time based on train type.

        Args:
            process_times: Process times configuration

        Returns
        -------
            Total preparation time in simulation ticks
        """
        if self.is_mainline:
            # Mainline: loco coupling + brake test + inspection
            loco_coupling = timedelta_to_sim_ticks(process_times.loco_coupling_time)
            brake_test = timedelta_to_sim_ticks(process_times.full_brake_test_time)
            inspection = timedelta_to_sim_ticks(process_times.technical_inspection_time)
            return loco_coupling + brake_test + inspection

        # Shunting: loco coupling + preparation (safety checks, communication)
        loco_coupling = timedelta_to_sim_ticks(process_times.loco_coupling_time)
        preparation = timedelta_to_sim_ticks(process_times.shunting_preparation_time)
        return loco_coupling + preparation

    def __post_init__(self) -> None:
        """Validate train movement after creation."""
        if not self.locomotive:
            raise ValueError(f'Train movement {self.id} must have a locomotive')

        if not self.batch:
            raise ValueError(f'Train movement {self.id} must have a batch (rake)')

        if not self.origin:
            raise ValueError(f'Train movement {self.id} must have an origin')

        if not self.destination:
            raise ValueError(f'Train movement {self.id} must have a destination')

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f'TrainMovement(id={self.id}, type={self.train_type.value}, '
            f'status={self._status.value}, loco={self.locomotive.id}, '
            f'wagons={self.wagon_count}, {self.origin}->{self.destination})'
        )
