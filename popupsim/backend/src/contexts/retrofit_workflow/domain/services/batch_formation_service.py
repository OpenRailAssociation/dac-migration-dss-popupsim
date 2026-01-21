"""Batch formation service for railway wagon processing operations.

This module provides domain services for forming batches of wagons based on
capacity constraints and operational requirements in the DAC migration system.
Batch formation follows specific business rules for different operational phases.
"""

from contexts.retrofit_workflow.domain.aggregates.batch_aggregate import BatchAggregate
from contexts.retrofit_workflow.domain.aggregates.batch_aggregate import DomainError
from contexts.retrofit_workflow.domain.aggregates.rake_aggregate import RakeType
from contexts.retrofit_workflow.domain.entities.wagon import Wagon
from contexts.retrofit_workflow.domain.entities.workshop import Workshop
from contexts.retrofit_workflow.domain.services.rake_formation_service import RakeFormationService
from contexts.retrofit_workflow.domain.value_objects.rake_formation_request import RakeFormationRequest


class BatchFormationService:
    """Domain service for forming wagon batches with integrated rake creation.

    This service implements business rules for batch formation across different
    operational phases of the DAC migration process. It coordinates batch and
    rake creation to ensure every batch is transportable.

    Business Rules
    --------------
    1. Collection → Retrofit: Batch size limited by retrofit track capacity
    2. Retrofit → Workshop: Batch size equals available workshop bays
    3. Workshop → Retrofitted: Batch size matches workshop processing batch
    4. Retrofitted → Parking: Batch size limited by parking track capacity
    5. Every batch must have a valid rake for transport (coupling validation)

    Notes
    -----
    This is a stateless domain service that coordinates batch and rake creation.

    Examples
    --------
    >>> service = BatchFormationService()
    >>> batch = service.form_batch_for_workshop(wagons, workshop)
    >>> aggregate = service.create_batch_aggregate(batch, 'WORKSHOP_01')
    """

    def __init__(self, rake_formation_service: RakeFormationService | None = None) -> None:
        """Initialize batch formation service with dependencies.

        Parameters
        ----------
        rake_formation_service : RakeFormationService | None
            Service for rake formation operations. If None, creates default instance.
        """
        self._rake_formation_service = rake_formation_service or RakeFormationService()

    def form_batch_for_retrofit_track(
        self,
        wagons: list[Wagon],
        retrofit_track_capacity: float,
    ) -> list[Wagon]:
        """Form wagon batch that fits within retrofit track capacity constraints.

        Implements Collection → Retrofit phase batch formation by selecting
        wagons that fit within the available track capacity.

        Parameters
        ----------
        wagons : list[Wagon]
            Available wagons in processing order
        retrofit_track_capacity : float
            Available capacity on retrofit track in meters

        Returns
        -------
        list[Wagon]
            Batch of wagons that fit within capacity constraints

        Notes
        -----
        Wagons are selected in order until capacity is exhausted.
        Partial wagon fitting is not allowed - each wagon must fit completely.

        Examples
        --------
        >>> service = BatchFormationService()
        >>> batch = service.form_batch_for_retrofit_track(wagons, 150.0)
        >>> total_length = sum(w.length for w in batch)
        >>> assert total_length <= 150.0
        """
        batch = []
        total_length = 0.0

        for wagon in wagons:
            if total_length + wagon.length <= retrofit_track_capacity:
                batch.append(wagon)
                total_length += wagon.length
            else:
                break  # Can't fit more

        return batch

    def form_batch_for_workshop(
        self,
        wagons: list[Wagon],
        workshop: Workshop,
    ) -> list[Wagon]:
        """Form wagon batch based on workshop bay availability.

        Implements Retrofit → Workshop phase batch formation where batch size
        equals the number of available workshop bays for parallel processing.

        Parameters
        ----------
        wagons : list[Wagon]
            Available wagons on retrofit track in processing order
        workshop : Workshop
            Target workshop with available bays

        Returns
        -------
        list[Wagon]
            Batch of wagons sized to match available workshop capacity

        Notes
        -----
        All wagons in the batch will be processed simultaneously in parallel bays.
        Batch size is limited by the smaller of available wagons or available bays.

        Examples
        --------
        >>> service = BatchFormationService()
        >>> batch = service.form_batch_for_workshop(wagons, workshop)
        >>> assert len(batch) <= workshop.available_capacity
        >>> assert len(batch) <= len(wagons)
        """
        available_bays = workshop.available_capacity

        # Take up to available_bays wagons
        batch_size = min(available_bays, len(wagons))
        return wagons[:batch_size]

    def form_batch_for_parking_track(
        self,
        wagons: list[Wagon],
        parking_track_capacity: float,
    ) -> list[Wagon]:
        """Form wagon batch that fits within parking track capacity constraints.

        Implements Retrofitted → Parking phase batch formation by selecting
        wagons that fit within the available parking track capacity.

        Parameters
        ----------
        wagons : list[Wagon]
            Available retrofitted wagons in processing order
        parking_track_capacity : float
            Available capacity on parking track in meters

        Returns
        -------
        list[Wagon]
            Batch of wagons that fit within parking capacity constraints

        Notes
        -----
        Similar to retrofit track formation, wagons are selected in order
        until capacity is exhausted. Partial wagon fitting is not allowed.

        Examples
        --------
        >>> service = BatchFormationService()
        >>> batch = service.form_batch_for_parking_track(wagons, 200.0)
        >>> total_length = sum(w.length for w in batch)
        >>> assert total_length <= 200.0
        """
        batch = []
        total_length = 0.0

        for wagon in wagons:
            if total_length + wagon.length <= parking_track_capacity:
                batch.append(wagon)
                total_length += wagon.length
            else:
                break  # Can't fit more

        return batch

    def calculate_batch_size_for_workshop(
        self,
        workshop: Workshop,
        available_wagon_count: int,
    ) -> int:
        """Calculate optimal batch size for workshop processing.

        Determines the maximum number of wagons that can be processed
        simultaneously based on workshop capacity and wagon availability.

        Parameters
        ----------
        workshop : Workshop
            Target workshop for processing
        available_wagon_count : int
            Number of wagons available for processing

        Returns
        -------
        int
            Optimal batch size for workshop processing

        Notes
        -----
        Batch size is constrained by the minimum of available workshop bays
        and available wagons to ensure efficient resource utilization.

        Examples
        --------
        >>> service = BatchFormationService()
        >>> size = service.calculate_batch_size_for_workshop(workshop, 10)
        >>> assert size <= workshop.available_capacity
        >>> assert size <= 10
        """
        return min(workshop.available_capacity, available_wagon_count)  # type: ignore[no-any-return]

    def create_batch_aggregate(
        self,
        wagons: list[Wagon],
        destination: str,
    ) -> BatchAggregate:
        """Create batch aggregate with integrated rake formation.

        Constructs a BatchAggregate with associated rake. Validates coupling
        compatibility and ensures transportability.

        Parameters
        ----------
        wagons : list[Wagon]
            Wagons to include in the batch
        destination : str
            Target destination identifier for the batch

        Returns
        -------
        BatchAggregate
            BatchAggregate with associated rake for transport

        Raises
        ------
        DomainError
            If batch formation fails or rake creation fails due to coupling issues

        Notes
        -----
        This method coordinates both batch and rake creation atomically.
        If rake formation fails, no batch is created, maintaining consistency.

        Examples
        --------
        >>> service = BatchFormationService()
        >>> aggregate = service.create_batch_aggregate(wagons, 'WORKSHOP_01')
        >>> print(f'Created batch: {aggregate.id} with rake: {aggregate.rake_id}')
        """
        if not self.can_form_batch(wagons):
            raise DomainError('Cannot form batch - insufficient wagons')

        batch_id = f'BATCH_{destination}_{len(wagons)}_{id(wagons[0])}'
        rake_id = f'{batch_id}_RAKE'

        # Create rake first to validate coupling compatibility
        rake_request = RakeFormationRequest(
            rake_id=rake_id,
            wagons=wagons,
            rake_type=RakeType.WORKSHOP_RAKE,
            formation_track='BATCH_FORMATION',
            target_track=destination,
            formation_time=0.0,
        )

        rake, error = self._rake_formation_service.form_rake(rake_request)
        if not rake:
            raise DomainError(f'Cannot form batch {batch_id} - rake formation failed: {error}')

        # Create batch with rake reference
        return BatchAggregate(id=batch_id, wagons=wagons, destination=destination, rake_id=rake_id)

    def can_form_batch(
        self,
        wagons: list[Wagon],
        min_size: int = 1,
    ) -> bool:
        """Validate if a batch can be formed from the given wagons.

        Checks if the wagon collection meets minimum requirements for
        batch formation and coupling compatibility.

        Parameters
        ----------
        wagons : list[Wagon]
            Wagons to validate for batch formation
        min_size : int, default=1
            Minimum number of wagons required for a valid batch

        Returns
        -------
        bool
            True if batch can be formed, False otherwise

        Notes
        -----
        Validates both minimum size and coupling compatibility to ensure
        the batch can be transported as a rake.

        Examples
        --------
        >>> service = BatchFormationService()
        >>> can_form = service.can_form_batch(wagons, min_size=2)
        >>> if not can_form:
        ...     print('Insufficient wagons or coupling incompatibility')
        """
        if len(wagons) < min_size:
            return False

        # Check coupling compatibility
        can_couple, _ = self._rake_formation_service.can_form_rake(wagons)
        return can_couple
