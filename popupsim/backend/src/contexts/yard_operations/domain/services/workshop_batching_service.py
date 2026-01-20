"""Workshop Batching Domain Service.

Pure business logic for workshop wagon batching - no infrastructure dependencies.
"""

from shared.domain.entities.wagon import Wagon


class WagonBatch:
    """Value object representing a batch of wagons for transport."""

    def __init__(self, wagons: list[Wagon], workshop_id: str) -> None:
        self.wagons = wagons
        self.workshop_id = workshop_id
        self.batch_id = f'batch_{workshop_id}_{len(wagons)}'

    def is_ready_for_transport(self) -> bool:
        """Check if batch is ready for transport."""
        return len(self.wagons) > 0

    def get_total_length(self) -> float:
        """Get total length of all wagons in batch."""
        return sum(wagon.length for wagon in self.wagons)


class WorkshopBatchingService:
    """Domain service for workshop batching business logic."""

    def __init__(self) -> None:
        self._pending_batches: dict[str, list[Wagon]] = {}
        self._pending_transport_checks: dict[str, bool] = {}

    def add_completed_wagon(self, wagon: Wagon, workshop_id: str) -> bool:
        """Add completed wagon to pending batch. Returns True if this is the first wagon."""
        # Initialize workshop batch if needed
        if workshop_id not in self._pending_batches:
            self._pending_batches[workshop_id] = []
            self._pending_transport_checks[workshop_id] = False

        # Add wagon to batch
        self._pending_batches[workshop_id].append(wagon)

        # Return True if this is the first wagon (caller should schedule batch creation)
        if not self._pending_transport_checks[workshop_id]:
            self._pending_transport_checks[workshop_id] = True
            return True

        return False

    def create_batch(self, workshop_id: str) -> WagonBatch | None:
        """Create batch from pending wagons and clear."""
        if workshop_id not in self._pending_batches or not self._pending_batches[workshop_id]:
            return None

        # Get all completed wagons for this workshop
        completed_wagons = self._pending_batches[workshop_id][:]
        self._pending_batches[workshop_id] = []
        self._pending_transport_checks[workshop_id] = False

        if completed_wagons:
            return WagonBatch(completed_wagons, workshop_id)

        return None

    def _create_batch_if_ready(self, workshop_id: str) -> WagonBatch | None:
        """Create batch if wagons are ready for transport (deprecated - use create_batch)."""
        return self.create_batch(workshop_id)

    def has_pending_wagons(self, workshop_id: str) -> bool:
        """Check if workshop has pending wagons."""
        return workshop_id in self._pending_batches and len(self._pending_batches[workshop_id]) > 0
