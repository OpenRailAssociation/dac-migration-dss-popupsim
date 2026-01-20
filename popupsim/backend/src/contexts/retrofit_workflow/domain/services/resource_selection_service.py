"""Generic resource selection service with configurable selection strategies.

This module provides a reusable service for selecting resources (workshops, tracks,
etc.) using various selection strategies. It implements common resource allocation
patterns used throughout the DAC migration simulation system.
"""

from collections.abc import Callable
from enum import Enum
from typing import TypeVar

from contexts.retrofit_workflow.domain.ports.resource_port import ResourcePort


class SelectionStrategy(Enum):
    """Enumeration of available resource selection strategies.

    Each strategy implements a different approach to resource allocation
    based on operational requirements and optimization goals.
    """

    ROUND_ROBIN = 'ROUND_ROBIN'
    FIRST_AVAILABLE = 'FIRST_AVAILABLE'
    LEAST_BUSY = 'LEAST_BUSY'
    SHORTEST_QUEUE = 'SHORTEST_QUEUE'
    BEST_FIT = 'BEST_FIT'  # Fill tracks completely before moving to next


TResource = TypeVar('TResource', bound=ResourcePort)  # pylint: disable=invalid-name


class ResourceSelectionService[TResource: ResourcePort]:  # pylint: disable=invalid-name,too-few-public-methods
    """Generic service for selecting resources using configurable strategies.

    This service provides a interface for resource selection across
    different resource types (workshops, tracks, etc.) using various allocation
    strategies to optimize system performance.

    Parameters
    ----------
    TResource : TypeVar
        Generic type parameter bounded by the Resource protocol

    Attributes
    ----------
    resources : dict[str, TResource]
        Dictionary mapping resource IDs to resource objects
    strategy : SelectionStrategy
        Currently configured selection strategy

    Notes
    -----
    This is a stateless service except for round-robin counter state.
    All selection logic is based on pure business rules.

    Examples
    --------
    >>> workshops = {'WS1': workshop1, 'WS2': workshop2}
    >>> service = ResourceSelectionService(workshops, SelectionStrategy.LEAST_BUSY)
    >>> selected_id = service.select(lambda id, ws: ws.available_capacity > 5)
    """

    def __init__(
        self,
        resources: dict[str, TResource],
        strategy: SelectionStrategy = SelectionStrategy.FIRST_AVAILABLE,
    ) -> None:
        """Initialize the resource selection service.

        Parameters
        ----------
        resources : dict[str, TResource]
            Dictionary mapping resource identifiers to resource objects
        strategy : SelectionStrategy, default=SelectionStrategy.FIRST_AVAILABLE
            Selection strategy to use for resource allocation

        Notes
        -----
        The round-robin counter is initialized to 0 and maintained across
        multiple selection calls for fair distribution.
        """
        self.resources = resources
        self.strategy = strategy
        self._round_robin_counter = 0

    def select(
        self,
        can_use: Callable[[str, TResource], bool] | None = None,
    ) -> str | None:
        """Select a resource using the configured strategy.

        Applies the configured selection strategy to choose the most appropriate
        resource from the available pool, optionally filtered by a custom predicate.

        Parameters
        ----------
        can_use : Callable[[str, TResource], bool] | None, optional
            Optional predicate function to filter usable resources.
            Receives resource_id and resource object, returns True if usable.

        Returns
        -------
        str | None
            Resource identifier of selected resource, or None if no suitable resource

        Notes
        -----
        The selection process first filters resources using the can_use predicate
        (if provided), then applies the configured strategy to the remaining candidates.

        Examples
        --------
        >>> # Select any available resource
        >>> resource_id = service.select()
        >>> # Select resource with specific capacity requirement
        >>> resource_id = service.select(lambda id, resource: resource.available_capacity >= 10)
        """
        if self.strategy == SelectionStrategy.ROUND_ROBIN:
            return self._select_round_robin(can_use)
        if self.strategy == SelectionStrategy.FIRST_AVAILABLE:
            return self._select_first_available(can_use)
        if self.strategy == SelectionStrategy.LEAST_BUSY:
            return self._select_least_busy(can_use)
        if self.strategy == SelectionStrategy.SHORTEST_QUEUE:
            return self._select_shortest_queue(can_use)
        if self.strategy == SelectionStrategy.BEST_FIT:
            return self._select_best_fit(can_use)

        return None

    def _can_use_resource(
        self,
        resource_id: str,
        resource: TResource,
        can_use: Callable[[str, TResource], bool] | None,
    ) -> bool:
        """Check if a resource can be used based on the provided predicate.

        Parameters
        ----------
        resource_id : str
            Resource identifier
        resource : TResource
            Resource object to check
        can_use : Callable[[str, TResource], bool] | None
            Predicate function, or None to allow all resources

        Returns
        -------
        bool
            True if resource can be used, False otherwise
        """
        if can_use is None:
            return True
        return can_use(resource_id, resource)

    def _select_round_robin(
        self,
        can_use: Callable[[str, TResource], bool] | None,
    ) -> str | None:
        """Select resource using round-robin strategy for fair distribution.

        Distributes load evenly across all available resources by cycling
        through them in order, maintaining state between calls.

        Parameters
        ----------
        can_use : Callable[[str, TResource], bool] | None
            Optional predicate to filter usable resources

        Returns
        -------
        str | None
            Selected resource ID or None if no usable resources
        """
        resource_ids = list(self.resources.keys())
        if not resource_ids:
            return None

        for i in range(len(resource_ids)):
            index = (self._round_robin_counter + i) % len(resource_ids)
            resource_id = resource_ids[index]
            resource = self.resources[resource_id]

            if self._can_use_resource(resource_id, resource, can_use):
                self._round_robin_counter = index + 1
                return resource_id

        return None

    def _select_first_available(
        self,
        can_use: Callable[[str, TResource], bool] | None,
    ) -> str | None:
        """Select first resource with available capacity.

        Simple strategy that picks the first resource in iteration order
        that has available capacity and meets the usage criteria.

        Parameters
        ----------
        can_use : Callable[[str, TResource], bool] | None
            Optional predicate to filter usable resources

        Returns
        -------
        str | None
            Selected resource ID or None if no available resources
        """
        for resource_id, resource in self.resources.items():
            if not self._can_use_resource(resource_id, resource, can_use):
                continue

            capacity = resource.get_available_capacity()
            if capacity > 0:
                return resource_id

        return None

    def _select_least_busy(
        self,
        can_use: Callable[[str, TResource], bool] | None,
    ) -> str | None:
        """Select resource with the most available capacity.

        Load balancing strategy that distributes work to the resource
        with the highest available capacity, optimizing for utilization.

        Parameters
        ----------
        can_use : Callable[[str, TResource], bool] | None
            Optional predicate to filter usable resources

        Returns
        -------
        str | None
            Selected resource ID or None if no usable resources
        """
        best_resource = None
        max_available: float = -1.0

        for resource_id, resource in self.resources.items():
            if not self._can_use_resource(resource_id, resource, can_use):
                continue

            capacity = resource.get_available_capacity()
            if capacity > max_available:
                max_available = capacity
                best_resource = resource_id

        return best_resource

    def _select_shortest_queue(
        self,
        can_use: Callable[[str, TResource], bool] | None,
    ) -> str | None:
        """Select resource with the shortest waiting queue.

        Queue optimization strategy that minimizes waiting times by
        directing work to resources with the smallest queues.

        Parameters
        ----------
        can_use : Callable[[str, TResource], bool] | None
            Optional predicate to filter usable resources

        Returns
        -------
        str | None
            Selected resource ID or None if no usable resources
        """
        best_resource = None
        min_queue: float = float('inf')

        for resource_id, resource in self.resources.items():
            if not self._can_use_resource(resource_id, resource, can_use):
                continue

            queue_len = resource.get_queue_length()
            if queue_len < min_queue:
                min_queue = float(queue_len)
                best_resource = resource_id

        return best_resource

    def _select_best_fit(
        self,
        can_use: Callable[[str, TResource], bool] | None,
    ) -> str | None:
        """Select resource with least available capacity (best fit strategy).

        Space optimization strategy that prefers resources with just enough
        capacity over those with excess capacity, maximizing space utilization.

        Parameters
        ----------
        can_use : Callable[[str, TResource], bool] | None
            Optional predicate to filter usable resources

        Returns
        -------
        str | None
            Selected resource ID or None if no usable resources

        Notes
        -----
        This strategy fills resources completely before moving to the next,
        which is optimal for space-constrained scenarios like track allocation.

        Examples
        --------
        For a 300m batch, this strategy would prefer a 320m track over a 500m track,
        leaving the larger track available for bigger batches.
        """
        best_resource = None
        min_available = float('inf')

        for resource_id, resource in self.resources.items():
            if not self._can_use_resource(resource_id, resource, can_use):
                continue

            # Must have capacity
            capacity = resource.get_available_capacity()
            if capacity <= 0:
                continue

            # Pick track with LEAST available capacity (closest fit)
            if capacity < min_available:
                min_available = capacity
                best_resource = resource_id

        return best_resource
