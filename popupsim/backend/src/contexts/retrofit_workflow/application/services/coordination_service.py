"""Coordination service for managing global operational state and priorities.

This module provides centralized coordination services for managing operational
priorities and resource conflicts in the DAC migration simulation system.
It ensures proper sequencing of operations and prevents resource contention.
"""

from typing import Any

from contexts.retrofit_workflow.domain.entities.wagon import Wagon


class CoordinationService:
    """Service for coordinating operations and managing global system state.

    This service provides centralized coordination logic to manage operational
    priorities and prevent resource conflicts between different coordinators
    in the DAC migration simulation system.

    Coordination Rules
    ------------------
    - Parking operations have priority over workshop operations
    - Workshop operations are blocked when parking is in progress
    - Retrofitted wagons must be cleared before new workshop operations
    - Collection operations always proceed (highest priority)

    Attributes
    ----------
    _parking_in_progress : bool
        Flag indicating if parking operation is currently active
    _retrofitted_accumulator : list[Wagon]
        Buffer for wagons waiting to be parked
    _workshop_turn_index : int
        Index for round-robin workshop selection

    Notes
    -----
    This service maintains global state to coordinate between different
    operational phases and ensure system-wide consistency.

    Examples
    --------
    >>> service = CoordinationService()
    >>> if service.can_workshop_proceed():
    ...     # Start workshop operation
    ...     service.start_operation('workshop')
    >>> service.add_to_accumulator(completed_wagons)
    """

    def __init__(self) -> None:
        """Initialize the coordination service with default state.

        Sets up initial coordination state with no active operations
        and empty accumulator buffers.
        """
        self._parking_in_progress = False
        self._retrofitted_accumulator: list[Wagon] = []
        self._workshop_turn_index = 0

    def can_workshop_proceed(self) -> bool:
        """Determine if workshop operations can proceed based on system state.

        Checks coordination rules to determine if workshop operations should
        be allowed to start or continue based on current system priorities.

        Returns
        -------
        bool
            True if workshop operations can proceed, False if blocked

        Notes
        -----
        Workshop operations are blocked when:
        - Parking operations are in progress (parking has priority)
        - Retrofitted wagons are waiting in the accumulator

        This ensures that completed wagons are cleared from the system
        before new workshop operations begin.

        Examples
        --------
        >>> service = CoordinationService()
        >>> if service.can_workshop_proceed():
        ...     print('Workshop can start processing')
        ... else:
        ...     print('Workshop blocked - parking in progress or wagons waiting')
        """
        return not self._parking_in_progress and not self._retrofitted_accumulator

    def start_parking(self) -> None:
        """Signal the start of a parking operation.

        Sets the parking-in-progress flag to block workshop operations
        and ensure parking has priority access to system resources.

        Notes
        -----
        This method should be called when parking operations begin
        to prevent resource conflicts with workshop operations.

        Examples
        --------
        >>> service = CoordinationService()
        >>> service.start_parking()
        >>> assert service.is_parking_in_progress()
        >>> assert not service.can_workshop_proceed()
        """
        self._parking_in_progress = True

    def finish_parking(self) -> None:
        """Signal the completion of a parking operation.

        Clears the parking-in-progress flag and empties the retrofitted
        accumulator to allow workshop operations to resume.

        Notes
        -----
        This method should be called when parking operations complete
        to restore normal operational flow.

        Examples
        --------
        >>> service = CoordinationService()
        >>> service.start_parking()
        >>> service.add_to_accumulator(wagons)
        >>> service.finish_parking()
        >>> assert not service.is_parking_in_progress()
        >>> assert service.get_accumulator_size() == 0
        """
        self._parking_in_progress = False
        self._retrofitted_accumulator.clear()

    def add_to_accumulator(self, wagons: list[Wagon]) -> None:
        """Add wagons to the retrofitted accumulator buffer.

        Adds completed wagons to the accumulator, which blocks workshop
        operations until these wagons are processed by parking operations.

        Parameters
        ----------
        wagons : list[Wagon]
            Completed wagons waiting to be parked

        Notes
        -----
        Wagons in the accumulator prevent new workshop operations from
        starting, ensuring that completed work is cleared before new
        processing begins.

        Examples
        --------
        >>> service = CoordinationService()
        >>> completed_wagons = [wagon1, wagon2, wagon3]
        >>> service.add_to_accumulator(completed_wagons)
        >>> assert service.get_accumulator_size() == 3
        >>> assert not service.can_workshop_proceed()
        """
        self._retrofitted_accumulator.extend(wagons)

    def get_accumulator_size(self) -> int:
        """Get the current number of wagons in the retrofitted accumulator.

        Returns
        -------
        int
            Number of wagons currently waiting to be parked

        Notes
        -----
        A non-zero accumulator size indicates that parking operations
        are needed and workshop operations should be blocked.

        Examples
        --------
        >>> service = CoordinationService()
        >>> size = service.get_accumulator_size()
        >>> if size > 0:
        ...     print(f'{size} wagons waiting for parking')
        """
        return len(self._retrofitted_accumulator)

    def is_parking_in_progress(self) -> bool:
        """Check if parking operations are currently active.

        Returns
        -------
        bool
            True if parking operation is currently in progress

        Notes
        -----
        This flag is used to coordinate between parking and workshop
        operations to prevent resource conflicts.

        Examples
        --------
        >>> service = CoordinationService()
        >>> if service.is_parking_in_progress():
        ...     print('Parking active - workshop operations blocked')
        """
        return self._parking_in_progress

    def get_workshop_turn_index(self) -> int:
        """Get the current workshop turn index for round-robin selection.

        Returns
        -------
        int
            Index of the workshop that should process the next batch

        Notes
        -----
        This index is used to implement fair distribution of work
        across multiple workshops in the system.

        Examples
        --------
        >>> service = CoordinationService()
        >>> current_index = service.get_workshop_turn_index()
        >>> next_workshop = workshops[current_index]
        """
        return self._workshop_turn_index

    def set_workshop_turn_index(self, index: int) -> None:
        """Set the workshop turn index for round-robin selection.

        Parameters
        ----------
        index : int
            Index of the workshop that should process the next batch

        Notes
        -----
        This method is used to update the round-robin state after
        workshop selection to ensure fair distribution.

        Examples
        --------
        >>> service = CoordinationService()
        >>> service.set_workshop_turn_index(2)
        >>> assert service.get_workshop_turn_index() == 2
        """
        self._workshop_turn_index = index

    def can_proceed_with_operation(self, operation_type: str) -> bool:
        """Check if a specific operation type can proceed.

        Evaluates coordination rules to determine if the specified
        operation type is allowed to proceed based on current system state.

        Parameters
        ----------
        operation_type : str
            Type of operation to check ('workshop', 'parking', 'collection')

        Returns
        -------
        bool
            True if the operation can proceed, False if blocked

        Notes
        -----
        Operation priority hierarchy:
        1. Collection operations (always proceed)
        2. Parking operations (always proceed when needed)
        3. Workshop operations (blocked by parking or accumulator)

        Examples
        --------
        >>> service = CoordinationService()
        >>> if service.can_proceed_with_operation('workshop'):
        ...     print('Workshop operation allowed')
        >>> if service.can_proceed_with_operation('parking'):
        ...     print('Parking operation allowed')
        """
        if operation_type == 'workshop':
            return self.can_workshop_proceed()
        if operation_type == 'parking':
            return True  # Parking always has priority
        if operation_type == 'collection':
            return True  # Collection always proceeds
        return True

    def start_operation(self, operation_type: str) -> None:
        """Signal the start of a specific operation type.

        Updates coordination state to reflect the beginning of the
        specified operation type.

        Parameters
        ----------
        operation_type : str
            Type of operation starting ('workshop', 'parking', 'collection')

        Notes
        -----
        Currently only parking operations require special coordination
        state management. Other operation types may be added in the future.

        Examples
        --------
        >>> service = CoordinationService()
        >>> service.start_operation('parking')
        >>> assert service.is_parking_in_progress()
        """
        if operation_type == 'parking':
            self.start_parking()

    def complete_operation(self, operation_type: str) -> None:
        """Signal the completion of a specific operation type.

        Updates coordination state to reflect the completion of the
        specified operation type.

        Parameters
        ----------
        operation_type : str
            Type of operation completing ('workshop', 'parking', 'collection')

        Notes
        -----
        Completion of parking operations clears the coordination state
        and allows other operations to resume.

        Examples
        --------
        >>> service = CoordinationService()
        >>> service.start_operation('parking')
        >>> service.complete_operation('parking')
        >>> assert not service.is_parking_in_progress()
        """
        if operation_type == 'parking':
            self.finish_parking()

    def get_status(self) -> dict[str, Any]:
        """Get comprehensive coordination status for monitoring and debugging.

        Provides a complete view of the current coordination state for
        system monitoring, debugging, and operational visibility.

        Returns
        -------
        dict[str, Any]
            Dictionary containing current coordination status information

        Notes
        -----
        Status information includes:
        - Parking operation state
        - Accumulator size and contents
        - Workshop turn index
        - Operation permission flags

        Examples
        --------
        >>> service = CoordinationService()
        >>> status = service.get_status()
        >>> print(f'Parking active: {status["parking_in_progress"]}')
        >>> print(f'Wagons waiting: {status["accumulator_size"]}')
        >>> print(f'Workshop can proceed: {status["can_workshop_proceed"]}')
        """
        return {
            'parking_in_progress': self._parking_in_progress,
            'accumulator_size': len(self._retrofitted_accumulator),
            'workshop_turn_index': self._workshop_turn_index,
            'can_workshop_proceed': self.can_workshop_proceed(),
        }
