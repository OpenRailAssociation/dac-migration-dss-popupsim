"""Wagon collection strategies for different collection algorithms."""

from abc import ABC
from abc import abstractmethod
from typing import Any

from contexts.retrofit_workflow.domain.entities.wagon import Wagon


class WagonCollectionStrategy(ABC):  # pylint: disable=too-few-public-methods
    """Abstract base class for wagon collection strategies.

    Note: Strategy pattern classes intentionally have few methods.
    """

    @abstractmethod
    def should_collect_wagon(self, current_wagons: list[Wagon], next_wagon: Wagon, context: Any) -> bool:
        """Determine if next wagon should be collected.

        Args:
            current_wagons: Wagons already collected
            next_wagon: Next wagon to consider
            context: Additional context (capacity, thresholds, etc.)

        Returns
        -------
            True if wagon should be collected, False otherwise
        """


class CapacityBasedStrategy(WagonCollectionStrategy):  # pylint: disable=too-few-public-methods
    """Collect wagons until capacity limit is reached."""

    def __init__(self, max_capacity: float) -> None:
        """Initialize with maximum capacity.

        Args:
            max_capacity: Maximum total length of wagons to collect
        """
        self.max_capacity = max_capacity

    def should_collect_wagon(self, current_wagons: list[Wagon], next_wagon: Wagon, _context: Any) -> bool:
        """Check if adding next wagon would exceed capacity."""
        current_length = sum(w.length for w in current_wagons)
        return current_length + next_wagon.length <= self.max_capacity


class ThresholdBasedStrategy(WagonCollectionStrategy):  # pylint: disable=too-few-public-methods
    """Collect wagons until threshold is reached."""

    def __init__(self, threshold_length: float) -> None:
        """Initialize with threshold length.

        Args:
            threshold_length: Target length to collect
        """
        self.threshold_length = threshold_length

    def should_collect_wagon(self, current_wagons: list[Wagon], _next_wagon: Wagon, _context: Any) -> bool:
        """Check if current length is below threshold."""
        current_length = sum(w.length for w in current_wagons)
        return current_length < self.threshold_length


class BayCountStrategy(WagonCollectionStrategy):  # pylint: disable=too-few-public-methods
    """Collect wagons until bay count limit is reached."""

    def __init__(self, max_bays: int) -> None:
        """Initialize with maximum bay count.

        Args:
            max_bays: Maximum number of wagons (bays) to collect
        """
        self.max_bays = max_bays

    def should_collect_wagon(self, current_wagons: list[Wagon], _next_wagon: Wagon, _context: Any) -> bool:
        """Check if adding next wagon would exceed bay count."""
        return len(current_wagons) < self.max_bays
