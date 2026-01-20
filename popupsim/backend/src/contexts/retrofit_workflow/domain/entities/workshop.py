"""Workshop Aggregate - DDD Aggregate Root with RetrofitBay entities."""

from dataclasses import dataclass
from dataclasses import field
from enum import Enum
from typing import Any

from contexts.retrofit_workflow.domain.ports.resource_port import ResourcePort


class BayStatus(Enum):
    """Retrofit bay status."""

    IDLE = 'IDLE'
    BUSY = 'BUSY'


@dataclass
class RetrofitBay:
    """Retrofit bay entity (owned by Workshop aggregate).

    A bay can process one wagon at a time.

    Attributes
    ----------
        id: Unique bay identifier
        workshop_id: Parent workshop identifier
    """

    id: str
    workshop_id: str

    # Private state
    _status: BayStatus = field(default=BayStatus.IDLE, init=False)
    _current_wagon_id: str | None = field(default=None, init=False)
    _retrofit_start_time: float | None = field(default=None, init=False)

    @property
    def status(self) -> BayStatus:
        """Get bay status."""
        return self._status

    @property
    def current_wagon_id(self) -> str | None:
        """Get current wagon ID being processed."""
        return self._current_wagon_id

    @property
    def is_available(self) -> bool:
        """Check if bay is available."""
        return self._status == BayStatus.IDLE

    def start_retrofit(self, wagon_id: str, start_time: float) -> None:
        """Start retrofit operation.

        Args:
            wagon_id: Wagon to retrofit
            start_time: Simulation time when retrofit starts

        Raises
        ------
            ValueError: If bay is busy
        """
        if self._status == BayStatus.BUSY:
            raise ValueError(f'Bay {self.id} is busy with wagon {self._current_wagon_id}')

        self._status = BayStatus.BUSY
        self._current_wagon_id = wagon_id
        self._retrofit_start_time = start_time

    def complete_retrofit(self) -> str:
        """Complete retrofit operation.

        Returns
        -------
            Wagon ID that was retrofitted

        Raises
        ------
            ValueError: If bay is idle
        """
        if self._status == BayStatus.IDLE:
            raise ValueError(f'Bay {self.id} is idle, no retrofit to complete')

        wagon_id = self._current_wagon_id

        self._status = BayStatus.IDLE
        self._current_wagon_id = None
        self._retrofit_start_time = None

        return wagon_id  # type: ignore[return-value]

    def __repr__(self) -> str:
        """Return string representation."""
        return f'RetrofitBay(id={self.id}, status={self._status.value}, wagon={self._current_wagon_id})'


@dataclass
class Workshop(ResourcePort):
    """Workshop Aggregate Root.

    A workshop owns multiple retrofit bays and manages wagon queue.
    This is the aggregate root that enforces business rules.

    Attributes
    ----------
        id: Unique workshop identifier
        location: Track where workshop is located
        bays: List of retrofit bays (owned entities)
    """

    id: str
    location: str
    bays: list[RetrofitBay] = field(default_factory=list)

    # Waiting queue (wagon ID references)
    _waiting_queue: list[str] = field(default_factory=list, init=False)

    def __post_init__(self) -> None:
        """Validate workshop."""
        if not self.bays:
            raise ValueError(f'Workshop {self.id} must have at least one bay')

    @property
    def capacity(self) -> int:
        """Get total number of bays."""
        return len(self.bays)

    @property
    def available_bays(self) -> list[RetrofitBay]:
        """Get list of available bays."""
        return [bay for bay in self.bays if bay.is_available]

    @property
    def busy_bays(self) -> list[RetrofitBay]:
        """Get list of busy bays."""
        return [bay for bay in self.bays if not bay.is_available]

    @property
    def available_capacity(self) -> int:
        """Get number of available bays."""
        return len(self.available_bays)

    @property
    def queue_length(self) -> int:
        """Get number of wagons in queue."""
        return len(self._waiting_queue)

    @property
    def utilization(self) -> float:
        """Get workshop utilization percentage."""
        if self.capacity == 0:
            return 0.0
        return (len(self.busy_bays) / self.capacity) * 100.0

    def add_to_queue(self, wagon_id: str) -> None:
        """Add wagon to waiting queue.

        Args:
            wagon_id: Wagon to add to queue
        """
        if wagon_id not in self._waiting_queue:
            self._waiting_queue.append(wagon_id)

    def remove_from_queue(self, wagon_id: str) -> None:
        """Remove wagon from waiting queue.

        Args:
            wagon_id: Wagon to remove
        """
        if wagon_id in self._waiting_queue:
            self._waiting_queue.remove(wagon_id)

    def get_next_from_queue(self) -> str | None:
        """Get next wagon from queue (FIFO).

        Returns
        -------
            Wagon ID or None if queue empty
        """
        if self._waiting_queue:
            return self._waiting_queue.pop(0)
        return None

    def assign_to_bay(self, wagon_id: str, start_time: float) -> RetrofitBay:
        """Assign wagon to available bay.

        Args:
            wagon_id: Wagon to assign
            start_time: Simulation time

        Returns
        -------
            Bay where wagon was assigned

        Raises
        ------
            ValueError: If no bays available
        """
        available = self.available_bays
        if not available:
            raise ValueError(f'Workshop {self.id} has no available bays')

        # Assign to first available bay
        bay = available[0]
        bay.start_retrofit(wagon_id, start_time)

        # Remove from queue if present
        self.remove_from_queue(wagon_id)

        return bay

    def complete_retrofit(self, bay_id: str) -> str:
        """Complete retrofit at bay.

        Args:
            bay_id: Bay identifier

        Returns
        -------
            Wagon ID that was retrofitted

        Raises
        ------
            ValueError: If bay not found or idle
        """
        bay = self.get_bay(bay_id)
        if not bay:
            raise ValueError(f'Bay {bay_id} not found in workshop {self.id}')

        return bay.complete_retrofit()

    def get_bay(self, bay_id: str) -> RetrofitBay | None:
        """Get bay by ID.

        Args:
            bay_id: Bay identifier

        Returns
        -------
            Bay or None if not found
        """
        for bay in self.bays:
            if bay.id == bay_id:
                return bay
        return None

    def can_accept_batch(self, batch_size: int) -> bool:
        """Domain logic for batch acceptance.

        Args:
            batch_size: Number of wagons in batch

        Returns
        -------
            True if workshop can accept the batch
        """
        return self.available_capacity >= batch_size

    def schedule_batch(self, batch_id: str, wagon_count: int) -> dict[str, Any]:
        """Create schedule for batch processing.

        Args:
            batch_id: Batch identifier
            wagon_count: Number of wagons in batch

        Returns
        -------
            Workshop schedule information

        Raises
        ------
            ValueError: If insufficient capacity
        """
        if not self.can_accept_batch(wagon_count):
            raise ValueError(
                f'Workshop {self.id} cannot accept batch of {wagon_count} wagons. '
                f'Available capacity: {self.available_capacity}'
            )

        return {
            'workshop_id': self.id,
            'batch_id': batch_id,
            'wagon_count': wagon_count,
            'available_bays': self.available_capacity,
            'estimated_start_time': self._calculate_start_time(),
            'estimated_completion': self._calculate_completion_time(wagon_count),
        }

    def _calculate_start_time(self) -> float:
        """Calculate estimated start time for next batch."""
        # Simple implementation - immediate start if bays available
        return 0.0 if self.available_capacity > 0 else 10.0  # 10 min delay if no bays

    def _calculate_completion_time(self, wagon_count: int) -> float:
        """Calculate estimated completion time for batch.

        Args:
            wagon_count: Number of wagons to process

        Returns
        -------
            Estimated completion time in minutes
        """
        # Assume 10 minutes per wagon retrofit
        return wagon_count * 10.0

    def get_wagon_bay(self, wagon_id: str) -> RetrofitBay | None:
        """Get bay where wagon is being processed.

        Args:
            wagon_id: Wagon identifier

        Returns
        -------
            Bay or None if wagon not found
        """
        for bay in self.bays:
            if bay.current_wagon_id == wagon_id:
                return bay
        return None

    # ResourcePort interface implementation
    def get_available_capacity(self) -> float:
        """Get available capacity (number of free bays)."""
        return float(self.available_capacity)

    def get_queue_length(self) -> int:
        """Get queue length."""
        return self.queue_length

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f'Workshop(id={self.id}, location={self.location}, '
            f'bays={self.capacity}, available={self.available_capacity}, '
            f'queue={self.queue_length})'
        )


def create_workshop(workshop_id: str, location: str, bay_count: int) -> Workshop:
    """Create workshop with bays.

    Parameters
    ----------
    workshop_id : str
        Workshop identifier
    location : str
        Track location
    bay_count : int
        Number of retrofit bays

    Returns
    -------
    Workshop
        Workshop with bays
    """
    bays = [RetrofitBay(id=f'{workshop_id}_bay_{i}', workshop_id=workshop_id) for i in range(bay_count)]

    return Workshop(id=workshop_id, location=location, bays=bays)
