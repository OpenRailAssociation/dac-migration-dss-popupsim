"""Workshop assignment strategies following Strategy pattern."""

from abc import ABC
from abc import abstractmethod

from contexts.retrofit_workflow.domain.entities.workshop import Workshop


class WorkshopAssignmentStrategy(ABC):  # pylint: disable=too-few-public-methods
    """Abstract strategy for workshop assignment."""

    @abstractmethod
    def select_next_workshop(self, workshops: list[Workshop], current_index: int) -> int:
        """Select next workshop index.

        Args:
            workshops: Available workshops
            current_index: Current workshop index

        Returns
        -------
            Next workshop index to use
        """


class RoundRobinAssignmentStrategy(WorkshopAssignmentStrategy):  # pylint: disable=too-few-public-methods
    """Round-robin workshop assignment strategy."""

    def select_next_workshop(self, workshops: list[Workshop], current_index: int) -> int:
        """Select next workshop using round-robin."""
        return (current_index + 1) % len(workshops)


class LoadBalancedAssignmentStrategy(WorkshopAssignmentStrategy):  # pylint: disable=too-few-public-methods
    """Load-balanced workshop assignment strategy."""

    def select_next_workshop(self, workshops: list[Workshop], _current_index: int) -> int:
        """Select workshop with lowest utilization.

        Parameters
        ----------
        workshops : list[Workshop]
            Available workshops to choose from
        _current_index : int
            Current index (unused in load-balanced strategy)

        Returns
        -------
        int
            Index of workshop with lowest utilization
        """
        if not workshops:
            return 0

        # Find workshop with lowest utilization
        min_utilization = float('inf')
        best_index = 0

        for i, workshop in enumerate(workshops):
            if workshop.utilization < min_utilization:
                min_utilization = workshop.utilization
                best_index = i

        return best_index


class FirstAvailableAssignmentStrategy(WorkshopAssignmentStrategy):  # pylint: disable=too-few-public-methods
    """First available workshop assignment strategy."""

    def select_next_workshop(self, workshops: list[Workshop], current_index: int) -> int:
        """Select first workshop with available capacity."""
        for i, workshop in enumerate(workshops):
            if workshop.available_capacity > 0:
                return i

        # If none available, use round-robin as fallback
        return (current_index + 1) % len(workshops)
