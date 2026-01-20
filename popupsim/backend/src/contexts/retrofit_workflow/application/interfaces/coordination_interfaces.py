"""Coordination interfaces for retrofit workflow context.

This module defines protocol interfaces for coordination services used throughout
the DAC migration simulation system. These protocols ensure consistent interfaces
for coordination, resource allocation, and workshop assignment strategies.
"""

from typing import Protocol

from contexts.retrofit_workflow.domain.entities.wagon import Wagon
from contexts.retrofit_workflow.domain.entities.workshop import Workshop


class CoordinationService(Protocol):
    """Protocol interface for coordination service managing global operational state.

    This protocol defines the contract for coordination services that manage
    global state and operational priorities in the DAC migration system.
    Implementations must provide methods for coordinating between different
    operational phases and managing resource conflicts.

    Methods
    -------
    can_workshop_proceed() -> bool
        Check if workshop operations are allowed to proceed
    start_parking() -> None
        Signal the start of parking operations
    finish_parking() -> None
        Signal the completion of parking operations
    add_to_accumulator(wagons: list[Wagon]) -> None
        Add wagons to the retrofitted accumulator buffer
    get_accumulator_size() -> int
        Get the current number of wagons in the accumulator

    Notes
    -----
    This protocol ensures that different coordination service implementations
    provide consistent interfaces for managing operational priorities and
    preventing resource conflicts.

    Examples
    --------
    >>> def process_workshop_batch(coordinator: CoordinationService) -> None:
    ...     if coordinator.can_workshop_proceed():
    ...         # Process workshop operations
    ...         pass
    """

    def can_workshop_proceed(self) -> bool:
        """Check if workshop operations can proceed based on system state.

        Returns
        -------
        bool
            True if workshop operations are allowed, False if blocked

        Notes
        -----
        Workshop operations may be blocked by higher-priority operations
        such as parking or when wagons are waiting in the accumulator.
        """

    def start_parking(self) -> None:
        """Signal that parking operation has started.

        Notes
        -----
        This method should be called when parking operations begin
        to coordinate with other system components and manage priorities.
        """

    def finish_parking(self) -> None:
        """Signal that parking operation has finished.

        Notes
        -----
        This method should be called when parking operations complete
        to allow other operations to resume normal processing.
        """

    def add_to_accumulator(self, wagons: list[Wagon]) -> None:
        """Add wagons to the retrofitted accumulator buffer.

        Parameters
        ----------
        wagons : list[Wagon]
            Wagons to add to the accumulator for parking coordination

        Notes
        -----
        Wagons in the accumulator typically block certain operations
        until they are processed by parking coordinators.
        """

    def get_accumulator_size(self) -> int:
        """Get the current number of wagons in the accumulator.

        Returns
        -------
        int
            Number of wagons currently waiting in the accumulator

        Notes
        -----
        The accumulator size is used to determine if operations
        should be blocked or if parking operations are needed.
        """


class WorkshopAssignmentStrategy(Protocol):  # pylint: disable=too-few-public-methods
    """Protocol interface for workshop assignment strategies.

    This protocol defines the contract for strategies that determine
    which workshop should be selected for processing operations.
    Different strategies can implement various optimization goals
    such as load balancing, efficiency, or fairness.

    Methods
    -------
    select_next_workshop(workshops: list[Workshop], current_index: int) -> int
        Select the next workshop index using the implemented strategy

    Notes
    -----
    Workshop assignment strategies enable flexible resource allocation
    policies that can be configured based on operational requirements.

    Examples
    --------
    >>> def assign_batch_to_workshop(strategy: WorkshopAssignmentStrategy, workshops: list[Workshop]) -> int:
    ...     return strategy.select_next_workshop(workshops, 0)
    """

    def select_next_workshop(self, workshops: list[Workshop], current_index: int) -> int:
        """Select the next workshop index using the implemented strategy.

        Parameters
        ----------
        workshops : list[Workshop]
            List of available workshops to choose from
        current_index : int
            Current workshop index for strategies that maintain state

        Returns
        -------
        int
            Index of the selected workshop in the workshops list

        Notes
        -----
        Different strategies may implement:
        - Round-robin selection for fair distribution
        - Least-busy selection for load balancing
        - Capacity-based selection for efficiency
        - Custom business logic for specific requirements
        """


class ResourceAllocationService(Protocol):  # pylint: disable=too-few-public-methods
    """Protocol interface for resource allocation coordination services.

    This protocol defines the contract for services that manage resource
    allocation and reservation across the DAC migration system. It provides
    methods for checking availability, reserving resources, and managing
    resource lifecycle.

    Methods
    -------
    can_allocate_locomotive(purpose: str, priority: int) -> bool
        Check if locomotive can be allocated for specific purpose
    reserve_locomotive(purpose: str, priority: int) -> str
        Reserve locomotive and return reservation identifier
    release_reservation(reservation_id: str) -> None
        Release a previously made resource reservation

    Notes
    -----
    Resource allocation services enable centralized management of
    shared resources like locomotives, preventing conflicts and
    ensuring optimal resource utilization.

    Examples
    --------
    >>> def transport_batch(allocator: ResourceAllocationService, purpose: str) -> str | None:
    ...     if allocator.can_allocate_locomotive(purpose, priority=1):
    ...         return allocator.reserve_locomotive(purpose, priority=1)
    ...     return None
    """

    def can_allocate_locomotive(self, purpose: str, priority: int) -> bool:
        """Check if locomotive can be allocated for specific purpose.

        Parameters
        ----------
        purpose : str
            Purpose or operation type requiring locomotive allocation
        priority : int
            Priority level for the allocation request

        Returns
        -------
        bool
            True if locomotive can be allocated, False if unavailable

        Notes
        -----
        This method checks resource availability without making
        a reservation, allowing for planning and decision-making.
        """

    def reserve_locomotive(self, purpose: str, priority: int) -> str:
        """Reserve locomotive and return reservation identifier.

        Parameters
        ----------
        purpose : str
            Purpose or operation type requiring locomotive
        priority : int
            Priority level for the reservation

        Returns
        -------
        str
            Unique reservation identifier for tracking and release

        Notes
        -----
        This method makes an actual reservation that should be
        released when the resource is no longer needed.
        """

    def release_reservation(self, reservation_id: str) -> None:
        """Release a previously made resource reservation.

        Parameters
        ----------
        reservation_id : str
            Unique identifier of the reservation to release

        Notes
        -----
        Proper reservation release is critical for resource
        availability and preventing resource leaks in the system.
        """
