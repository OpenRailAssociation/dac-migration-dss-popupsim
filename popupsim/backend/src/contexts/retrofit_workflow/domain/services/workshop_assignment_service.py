"""Workshop assignment service for optimal workshop resource allocation.

This module provides domain services for assigning wagons to workshops based on
capacity constraints, business rules, and configurable selection strategies.
It ensures efficient workshop utilization in the DAC migration process.
"""

from contexts.retrofit_workflow.domain.entities.wagon import Wagon
from contexts.retrofit_workflow.domain.entities.workshop import Workshop
from contexts.retrofit_workflow.domain.services.resource_selection_service import ResourceSelectionService
from contexts.retrofit_workflow.domain.services.resource_selection_service import SelectionStrategy


class WorkshopAssignmentService:
    """Domain service for intelligent workshop assignment and resource allocation.

    This service implements business logic for assigning wagons to workshops
    based on operational constraints, capacity availability, and optimization
    strategies. It ensures efficient workshop utilization while maintaining
    business rule compliance.

    Attributes
    ----------
    workshops : dict[str, Workshop]
        Dictionary mapping workshop identifiers to workshop objects
    _selector : ResourceSelectionService
        Generic resource selector for consistent allocation strategies

    Business Rules
    --------------
    - Only wagons requiring retrofit can be assigned to workshops
    - Workshops must have available capacity for assignment
    - Assignment strategies optimize for different operational goals

    Notes
    -----
    This is a stateless domain service with no external dependencies.
    All assignment logic is based on pure business rules.

    Examples
    --------
    >>> workshops = {'WS1': workshop1, 'WS2': workshop2}
    >>> service = WorkshopAssignmentService(workshops, SelectionStrategy.LEAST_BUSY)
    >>> workshop_id = service.select_workshop(wagon)
    >>> if workshop_id:
    ...     print(f'Assigned wagon to workshop: {workshop_id}')
    """

    def __init__(
        self,
        workshops: dict[str, Workshop],
        strategy: SelectionStrategy = SelectionStrategy.FIRST_AVAILABLE,
    ) -> None:
        """Initialize the workshop assignment service.

        Parameters
        ----------
        workshops : dict[str, Workshop]
            Dictionary mapping workshop identifiers to workshop objects
        strategy : SelectionStrategy, default=SelectionStrategy.FIRST_AVAILABLE
            Selection strategy for choosing between multiple available workshops

        Notes
        -----
        The service uses a generic resource selector to ensure consistent
        allocation behavior across different resource types in the system.
        """
        self.workshops = workshops
        self._selector: ResourceSelectionService[Workshop] = ResourceSelectionService(workshops, strategy)

    def can_assign(self, wagon: Wagon, workshop_id: str) -> bool:
        """Validate if a wagon can be assigned to a specific workshop.

        Checks business rules and constraints to determine assignment feasibility
        without considering capacity limitations.

        Parameters
        ----------
        wagon : Wagon
            Wagon entity to validate for assignment
        workshop_id : str
            Target workshop identifier

        Returns
        -------
        bool
            True if wagon can be assigned to the workshop, False otherwise

        Notes
        -----
        Business rules validated:
        - Wagon must require retrofit (status-based validation)
        - Workshop must exist in the system
        - Additional business constraints can be added here

        Examples
        --------
        >>> service = WorkshopAssignmentService(workshops)
        >>> can_assign = service.can_assign(wagon, 'WORKSHOP_01')
        >>> if not can_assign:
        ...     print('Wagon cannot be assigned to this workshop')
        """
        if not wagon.needs_retrofit:
            return False

        return workshop_id in self.workshops

    def select_workshop(self, wagon: Wagon) -> str | None:
        """Select the optimal workshop for wagon assignment using configured strategy.

        Applies the configured selection strategy to choose the best available
        workshop from those that can accept the wagon.

        Parameters
        ----------
        wagon : Wagon
            Wagon entity requiring workshop assignment

        Returns
        -------
        str | None
            Workshop identifier of selected workshop, or None if no suitable workshop

        Notes
        -----
        The selection process:
        1. Filters workshops that can accept the wagon (business rules)
        2. Applies the configured selection strategy
        3. Returns the optimal workshop or None if no options available

        Examples
        --------
        >>> service = WorkshopAssignmentService(workshops, SelectionStrategy.LEAST_BUSY)
        >>> workshop_id = service.select_workshop(wagon)
        >>> if workshop_id:
        ...     workshop = workshops[workshop_id]
        ...     print(f'Selected workshop: {workshop_id} (capacity: {workshop.available_capacity})')
        """
        result = self._selector.select(can_use=lambda ws_id, _: self.can_assign(wagon, ws_id))
        return result  # type: ignore[no-any-return]

    def select_workshop_with_capacity(
        self,
        wagon: Wagon,
        min_capacity: int = 1,
    ) -> str | None:
        """Select workshop with specific minimum capacity requirements.

        Finds a workshop that can accept the wagon and has at least the
        specified minimum available capacity for processing.

        Parameters
        ----------
        wagon : Wagon
            Wagon entity requiring workshop assignment
        min_capacity : int, default=1
            Minimum available capacity required in the workshop

        Returns
        -------
        str | None
            Workshop identifier meeting capacity requirements, or None if unavailable

        Notes
        -----
        This method performs a linear search through workshops, checking both
        business rule compliance and capacity constraints. It's useful for
        batch processing scenarios where specific capacity is required.

        Examples
        --------
        >>> service = WorkshopAssignmentService(workshops)
        >>> # Find workshop with capacity for at least 5 wagons
        >>> workshop_id = service.select_workshop_with_capacity(wagon, min_capacity=5)
        >>> if workshop_id:
        ...     print(f'Found workshop with sufficient capacity: {workshop_id}')
        ... else:
        ...     print('No workshops available with required capacity')
        """
        for workshop_id, workshop in self.workshops.items():
            if not self.can_assign(wagon, workshop_id):
                continue

            if workshop.available_capacity >= min_capacity:
                return workshop_id  # type: ignore[no-any-return]

        return None
