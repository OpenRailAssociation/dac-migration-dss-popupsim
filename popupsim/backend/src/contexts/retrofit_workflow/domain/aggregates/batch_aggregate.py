"""Batch aggregate root for consistent batch operations."""

from dataclasses import dataclass
from dataclasses import field
from enum import Enum
from typing import Any

from contexts.retrofit_workflow.domain.entities.locomotive import Locomotive
from contexts.retrofit_workflow.domain.entities.wagon import Wagon
from shared.infrastructure.simpy_time_converters import timedelta_to_sim_ticks


class BatchStatus(Enum):
    """Batch status enumeration."""

    FORMED = 'FORMED'
    IN_TRANSPORT = 'IN_TRANSPORT'
    AT_WORKSHOP = 'AT_WORKSHOP'
    PROCESSING = 'PROCESSING'
    COMPLETED = 'COMPLETED'


class DomainError(Exception):
    """Domain-specific error."""


@dataclass
class BatchAggregate:
    """Aggregate root for batch operations ensuring consistency.

    Contains rake_id reference to ensure every batch has a transportable rake.
    Rake creation is handled by BatchFormationService following DDD principles.
    """

    id: str
    wagons: list[Wagon]
    destination: str
    rake_id: str  # Reference to associated rake
    _status: BatchStatus = field(default=BatchStatus.FORMED, init=False)
    _locomotive: Locomotive | None = field(default=None, init=False)
    _events: list[Any] = field(default_factory=list, init=False)

    @property
    def status(self) -> BatchStatus:
        """Get batch status."""
        return self._status

    @property
    def locomotive(self) -> Locomotive | None:
        """Get assigned locomotive."""
        return self._locomotive

    @property
    def wagon_count(self) -> int:
        """Get number of wagons in batch."""
        return len(self.wagons)

    @property
    def total_length(self) -> float:
        """Calculate total length of wagons in batch."""
        total: float = sum(wagon.length for wagon in self.wagons)
        return total

    @property
    def events(self) -> list[Any]:
        """Get domain events."""
        return self._events.copy()

    def start_transport(self, locomotive: Locomotive) -> None:
        """Start batch transport - ensures consistency."""
        if self._status != BatchStatus.FORMED:
            raise DomainError(f'Batch {self.id} not ready for transport. Current status: {self._status}')

        self._locomotive = locomotive
        self._status = BatchStatus.IN_TRANSPORT

        # Add domain event (will be created next)
        self._events.append(
            {
                'type': 'BatchTransportStarted',
                'batch_id': self.id,
                'locomotive_id': locomotive.id,
                'destination': self.destination,
            }
        )

    def arrive_at_destination(self) -> None:
        """Mark batch as arrived at destination."""
        if self._status != BatchStatus.IN_TRANSPORT:
            raise DomainError(f'Batch {self.id} not in transport. Current status: {self._status}')

        self._status = BatchStatus.AT_WORKSHOP

        self._events.append({'type': 'BatchArrivedAtDestination', 'batch_id': self.id, 'destination': self.destination})

    def start_processing(self) -> None:
        """Start batch processing."""
        if self._status != BatchStatus.AT_WORKSHOP:
            raise DomainError(f'Batch {self.id} not at workshop. Current status: {self._status}')

        self._status = BatchStatus.PROCESSING

        # Update all wagons to processing state
        for wagon in self.wagons:
            if wagon.status.value != 'READY_FOR_RETROFIT':
                wagon.prepare_for_retrofit()

    def complete_processing(self) -> None:
        """Complete batch processing."""
        if self._status != BatchStatus.PROCESSING:
            raise DomainError(f'Batch {self.id} not processing. Current status: {self._status}')

        self._status = BatchStatus.COMPLETED

        self._events.append({'type': 'BatchProcessingCompleted', 'batch_id': self.id, 'workshop_id': self.destination})

    def release_locomotive(self) -> Locomotive | None:
        """Release assigned locomotive."""
        locomotive = self._locomotive
        self._locomotive = None
        return locomotive

    def clear_events(self) -> None:
        """Clear domain events after publishing."""
        self._events.clear()

    def can_start_transport(self) -> bool:
        """Check if batch can start transport."""
        return (
            self._status == BatchStatus.FORMED
            and all(wagon.needs_retrofit for wagon in self.wagons)
            and self.rake_id is not None  # Rake must exist for transport
        )

    def get_transport_time(self, base_transport_time: float, process_times: Any) -> float:
        """Calculate total transport time including coupling.

        Args:
            base_transport_time: Base route transport time
            process_times: Process times configuration

        Returns
        -------
            Total transport time including coupling

        """
        if not process_times:
            return base_transport_time

        # Get coupling time based on wagon coupler types
        coupling_time = 0.0
        if self.wagons:
            # Use first wagon's coupler type to determine coupling time
            first_wagon = self.wagons[0]
            if hasattr(first_wagon, 'coupler_a') and hasattr(first_wagon.coupler_a, 'type'):
                coupler_type = first_wagon.coupler_a.type.value
                if coupler_type == 'SCREW':
                    coupling_time = timedelta_to_sim_ticks(process_times.screw_coupling_time)
                elif coupler_type == 'DAC':
                    coupling_time = timedelta_to_sim_ticks(process_times.dac_coupling_time)

        return base_transport_time + coupling_time

    def __post_init__(self) -> None:
        """Validate batch after creation."""
        if not self.wagons:
            raise DomainError('Batch cannot be empty')

        if not self.destination:
            raise DomainError('Batch must have destination')

        if not self.rake_id:
            raise DomainError('Batch must have associated rake for transport')
