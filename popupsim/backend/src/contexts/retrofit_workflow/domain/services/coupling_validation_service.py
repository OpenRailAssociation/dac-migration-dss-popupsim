"""Coupling validation service for railway coupler compatibility analysis.

This module provides domain services for validating coupler compatibility between
wagons and locomotives in the DAC migration simulation system.
"""

from contexts.retrofit_workflow.domain.entities.locomotive import Locomotive
from contexts.retrofit_workflow.domain.entities.wagon import Wagon


class CouplingValidationService:
    """Domain service for validating coupler compatibility in railway operations.

    This service provides pure domain logic for determining whether railway vehicles
    can be coupled together based on their coupler types and compatibility rules.
    It operates without external dependencies and maintains business rule integrity.

    Notes
    -----
    This is a stateless domain service that enforces coupling business rules
    without any SimPy or infrastructure dependencies.

    Examples
    --------
    >>> service = CouplingValidationService()
    >>> can_couple = service.can_couple_wagons(wagon1, wagon2)
    >>> can_form, error = service.can_form_rake([wagon1, wagon2, wagon3])
    """

    def can_couple_wagons(self, wagon1: Wagon, wagon2: Wagon) -> bool:
        """Validate if two wagons can be coupled together.

        Checks compatibility between wagon1's rear coupler (coupler_b) and
        wagon2's front coupler (coupler_a) according to DAC migration rules.

        Parameters
        ----------
        wagon1 : Wagon
            First wagon in the coupling sequence
        wagon2 : Wagon
            Second wagon to be coupled to the first

        Returns
        -------
        bool
            True if wagons can be coupled, False otherwise

        Notes
        -----
        The coupling direction is fixed: wagon1.coupler_b connects to wagon2.coupler_a.
        This maintains consistent rake formation order.

        Examples
        --------
        >>> service = CouplingValidationService()
        >>> result = service.can_couple_wagons(wagon_with_dac, wagon_with_screw)
        >>> print(f'Can couple: {result}')
        """
        return wagon1.coupler_b.can_couple_to(wagon2.coupler_a)  # type: ignore[no-any-return]

    def can_form_rake(self, wagons: list[Wagon]) -> tuple[bool, str | None]:
        """Validate if a sequence of wagons can form a valid rake.

        Checks all adjacent wagon pairs in the sequence to ensure they have
        compatible couplers for rake formation.

        Parameters
        ----------
        wagons : list[Wagon]
            Ordered list of wagons to form into a rake

        Returns
        -------
        tuple[bool, str | None]
            A tuple containing:
            - bool: True if rake can be formed, False otherwise
            - str | None: Error message if formation fails, None if successful

        Notes
        -----
        - Empty wagon lists are invalid
        - Single wagons automatically form valid rakes
        - All adjacent pairs must have compatible couplers

        Examples
        --------
        >>> service = CouplingValidationService()
        >>> wagons = [wagon1, wagon2, wagon3]
        >>> can_form, error = service.can_form_rake(wagons)
        >>> if not can_form:
        ...     print(f'Rake formation failed: {error}')
        """
        if not wagons:
            return False, 'No wagons provided'

        if len(wagons) == 1:
            return True, None

        for i in range(len(wagons) - 1):
            wagon1 = wagons[i]
            wagon2 = wagons[i + 1]

            if not self.can_couple_wagons(wagon1, wagon2):
                return False, (
                    f'Incompatible couplers: {wagon1.id}.coupler_b '
                    f'({wagon1.coupler_b.type.value}) cannot couple to '
                    f'{wagon2.id}.coupler_a ({wagon2.coupler_a.type.value})'
                )

        return True, None

    def can_couple_loco_to_first_wagon(
        self,
        loco: Locomotive,
        first_wagon: Wagon,
        use_front: bool = True,
    ) -> bool:
        """Validate if locomotive can couple to the first wagon of a rake.

        Checks compatibility between locomotive coupler and the front coupler
        of the first wagon in a rake.

        Parameters
        ----------
        loco : Locomotive
            Locomotive to couple to the rake
        first_wagon : Wagon
            First wagon in the rake sequence
        use_front : bool, default=True
            Whether to use locomotive's front coupler (True) or back coupler (False)

        Returns
        -------
        bool
            True if locomotive can couple to first wagon, False otherwise

        Notes
        -----
        The locomotive couples to the wagon's coupler_a (front coupler).
        This is the standard configuration for pulling a rake.

        Examples
        --------
        >>> service = CouplingValidationService()
        >>> can_couple = service.can_couple_loco_to_first_wagon(locomotive, first_wagon, use_front=True)
        """
        loco_coupler = loco.coupler_front if use_front else loco.coupler_back
        return loco_coupler.can_couple_to(first_wagon.coupler_a)  # type: ignore[no-any-return]

    def can_couple_loco_to_last_wagon(
        self,
        loco: Locomotive,
        last_wagon: Wagon,
        use_front: bool = True,
    ) -> bool:
        """Validate if locomotive can couple to the last wagon of a rake.

        Checks compatibility between locomotive coupler and the rear coupler
        of the last wagon in a rake.

        Parameters
        ----------
        loco : Locomotive
            Locomotive to couple to the rake
        last_wagon : Wagon
            Last wagon in the rake sequence
        use_front : bool, default=True
            Whether to use locomotive's front coupler (True) or back coupler (False)

        Returns
        -------
        bool
            True if locomotive can couple to last wagon, False otherwise

        Notes
        -----
        The locomotive couples to the wagon's coupler_b (rear coupler).
        This configuration is used for pushing operations or double-heading.

        Examples
        --------
        >>> service = CouplingValidationService()
        >>> can_couple = service.can_couple_loco_to_last_wagon(locomotive, last_wagon, use_front=False)
        """
        loco_coupler = loco.coupler_front if use_front else loco.coupler_back
        return loco_coupler.can_couple_to(last_wagon.coupler_b)  # type: ignore[no-any-return]
