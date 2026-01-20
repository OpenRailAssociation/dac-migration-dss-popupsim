"""Batch context value object for transport operations."""

from dataclasses import dataclass
from typing import Any

from contexts.retrofit_workflow.domain.entities.wagon import Wagon


@dataclass
class BatchContext:
    """Context information for batch processing operations.

    Holds temporary state needed during batch transport and processing
    without polluting the Wagon entity with implementation details.
    """

    wagons: list[Wagon]
    workshop_id: str
    locomotive: Any | None = None
    bay_requests: list[Any] | None = None

    @property
    def batch_length(self) -> float:
        """Calculate total length of wagons in batch."""
        total: float = sum(wagon.length for wagon in self.wagons)
        return total

    @property
    def wagon_count(self) -> int:
        """Get number of wagons in batch."""
        return len(self.wagons)
