"""Rake formation service for railway wagon coupling operations.

This module provides domain services for forming and managing rakes (coupled
wagon sequences) in the DAC migration simulation system. It handles rake
validation, formation, and dissolution operations.
"""

from contexts.retrofit_workflow.domain.aggregates.rake_aggregate import Rake
from contexts.retrofit_workflow.domain.entities.wagon import Wagon
from contexts.retrofit_workflow.domain.services.coupling_validation_service import CouplingValidationService
from contexts.retrofit_workflow.domain.value_objects.rake_formation_request import RakeFormationRequest


class RakeFormationService:
    """Domain service for forming and managing railway wagon rakes.

    This service orchestrates rake formation by validating coupler compatibility
    and managing the lifecycle of rake aggregates. It ensures that only
    compatible wagons are coupled together according to DAC migration rules.

    Attributes
    ----------
    coupling_validator : CouplingValidationService
        Service for validating coupler compatibility between wagons

    Notes
    -----
    This is a stateless domain service with no external dependencies.
    All rake formation logic is based on pure business rules.

    Examples
    --------
    >>> service = RakeFormationService()
    >>> rake, error = service.form_rake('RAKE_001', wagons, RakeType.TRANSPORT, 'TRACK_A', 'TRACK_B', 0.0)
    >>> if rake:
    ...     print(f'Formed rake: {rake.id}')
    """

    def __init__(self) -> None:
        """Initialize the rake formation service.

        Creates the coupling validation service dependency for
        validating wagon compatibility during rake formation.
        """
        self.coupling_validator = CouplingValidationService()

    def can_form_rake(self, wagons: list[Wagon]) -> tuple[bool, str | None]:
        """Validate if wagons can form a valid rake.

        Delegates to the coupling validation service to check if all
        adjacent wagons in the sequence have compatible couplers.

        Parameters
        ----------
        wagons : list[Wagon]
            Ordered list of wagons to validate for rake formation

        Returns
        -------
        tuple[bool, str | None]
            A tuple containing:
            - bool: True if rake can be formed, False otherwise
            - str | None: Error message if validation fails, None if successful

        Notes
        -----
        This method validates the entire wagon sequence for coupling
        compatibility but does not create the actual rake object.

        Examples
        --------
        >>> service = RakeFormationService()
        >>> can_form, error = service.can_form_rake([wagon1, wagon2, wagon3])
        >>> if not can_form:
        ...     print(f'Rake formation failed: {error}')
        """
        return self.coupling_validator.can_form_rake(wagons)  # type: ignore[no-any-return]

    def form_rake(self, request: RakeFormationRequest) -> tuple[Rake | None, str | None]:
        """Form a rake from a validated formation request.

        Creates a Rake aggregate from the provided request after validating
        wagon coupling compatibility. Updates wagon entities with rake
        association information.

        Parameters
        ----------
        request : RakeFormationRequest
            Complete rake formation request with all necessary parameters

        Returns
        -------
        tuple[Rake | None, str | None]
            A tuple containing:
            - Rake | None: Created rake object if successful, None if failed
            - str | None: Error message if formation fails, None if successful

        Notes
        -----
        This method performs coupling validation before creating the rake.
        If successful, it updates all wagon entities with the rake ID
        for proper association tracking.

        Examples
        --------
        >>> service = RakeFormationService()
        >>> request = RakeFormationRequest(
        ...     rake_id='RAKE_001',
        ...     wagons=wagons,
        ...     rake_type=RakeType.TRANSPORT,
        ...     formation_track='FORMATION_TRACK',
        ...     target_track='DESTINATION_TRACK',
        ...     formation_time=120.0,
        ... )
        >>> rake, error = service.form_rake(request)
        >>> if rake:
        ...     print(f'Formed rake {rake.id} with {len(rake.wagon_ids)} wagons')
        """
        # Validate coupling compatibility
        can_form, error = self.can_form_rake(request.wagons)
        if not can_form:
            return None, error

        # Create rake
        wagon_ids = [w.id for w in request.wagons]
        total_length = sum(w.length for w in request.wagons)

        rake = Rake(
            id=request.rake_id,
            wagon_ids=wagon_ids,
            rake_type=request.rake_type,
            formation_track=request.formation_track,
            target_track=request.target_track,
            formation_time=request.formation_time,
        )
        rake.set_total_length(total_length)

        # Assign rake_id to wagons
        for wagon in request.wagons:
            wagon.rake_id = request.rake_id

        return rake, None

    def dissolve_rake(self, rake: Rake, wagons: list[Wagon]) -> None:
        """Dissolve a rake and remove associations from wagons.

        Breaks the association between the rake and its constituent wagons
        by clearing the rake_id from all wagon entities. This is typically
        done when wagons are uncoupled or redistributed.

        Parameters
        ----------
        rake : Rake
            Rake aggregate to dissolve
        wagons : list[Wagon]
            Wagon entities that were part of the rake

        Notes
        -----
        This method only removes the rake association from wagons.
        The rake object itself should be handled by the calling context
        for proper lifecycle management.

        Examples
        --------
        >>> service = RakeFormationService()
        >>> service.dissolve_rake(rake, wagons)
        >>> # All wagons now have rake_id = None
        >>> assert all(w.rake_id is None for w in wagons)
        """
        for wagon in wagons:
            if wagon.id in rake.wagon_ids:
                wagon.rake_id = None
