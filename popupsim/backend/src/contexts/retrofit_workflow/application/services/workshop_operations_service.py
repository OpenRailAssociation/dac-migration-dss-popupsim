"""Workshop Operations Service - Application service for workshop operations orchestration.

This module provides an application service that coordinates domain services
for complete workshop operations without SimPy dependencies.
"""

from dataclasses import dataclass
from datetime import timedelta

from contexts.retrofit_workflow.domain.aggregates.batch_aggregate import BatchAggregate
from contexts.retrofit_workflow.domain.entities.wagon import Wagon
from contexts.retrofit_workflow.domain.entities.workshop import Workshop
from contexts.retrofit_workflow.domain.services.batch_formation_service import BatchFormationService
from contexts.retrofit_workflow.domain.services.workshop_assignment_service import WorkshopAssignmentService
from contexts.retrofit_workflow.domain.services.workshop_scheduling_service import WorkshopSchedulingService


@dataclass
class WorkshopOperation:
    """Complete workshop operation with assignment, scheduling, and processing."""

    workshop_id: str
    batch_id: str
    wagon_count: int
    processing_time: timedelta
    total_time: timedelta


@dataclass
class WorkshopOperationResult:
    """Result of workshop operation execution."""

    operation: WorkshopOperation | None
    success: bool
    error_message: str | None
    processed_wagons: list[Wagon]
    batch_aggregate: BatchAggregate | None = None


class WorkshopOperationsService:
    """Application service for coordinating workshop operations.

    Orchestrates domain services to provide complete workshop operations:
    - Workshop assignment and selection
    - Batch formation and scheduling
    - Processing time calculations
    - End-to-end operation coordination

    This service coordinates domain services without SimPy dependencies.
    """

    def __init__(
        self,
        workshop_assignment: WorkshopAssignmentService,
        workshop_scheduling: WorkshopSchedulingService,
        batch_formation: BatchFormationService,
    ) -> None:
        """Initialize with domain services.

        Parameters
        ----------
        workshop_assignment : WorkshopAssignmentService
            Domain service for workshop assignment
        workshop_scheduling : WorkshopSchedulingService
            Domain service for workshop scheduling
        batch_formation : BatchFormationService
            Domain service for batch formation
        """
        self._workshop_assignment = workshop_assignment
        self._workshop_scheduling = workshop_scheduling
        self._batch_formation = batch_formation

    def create_processing_operation(
        self,
        wagons: list[Wagon],
        target_workshop: Workshop,
    ) -> WorkshopOperationResult:
        """Create workshop processing operation with batch formation.

        Parameters
        ----------
        wagons : list[Wagon]
            Wagons to process in workshop
        target_workshop : Workshop
            Workshop for processing

        Returns
        -------
        WorkshopOperationResult
            Result containing operation details or error
        """
        if not wagons:
            return WorkshopOperationResult(
                operation=None,
                success=False,
                error_message='Cannot create processing operation with no wagons',
                processed_wagons=[],
            )

        # Form batch for workshop
        batch_wagons = self._batch_formation.form_batch_for_workshop(wagons, target_workshop)

        if not batch_wagons:
            return WorkshopOperationResult(
                operation=None,
                success=False,
                error_message=f'No wagons can be processed in workshop {target_workshop.id}',
                processed_wagons=[],
            )

        # Schedule batch processing
        scheduling_result = self._workshop_scheduling.schedule_batch(batch_wagons, target_workshop)

        if not scheduling_result.success:
            return WorkshopOperationResult(
                operation=None,
                success=False,
                error_message=scheduling_result.error_message,
                processed_wagons=[],
            )

        # Create batch aggregate
        try:
            batch_aggregate = self._batch_formation.create_batch_aggregate(batch_wagons, target_workshop.id)
        except Exception as e:
            return WorkshopOperationResult(
                operation=None,
                success=False,
                error_message=f'Failed to create batch aggregate: {e!s}',
                processed_wagons=[],
            )

        # Create operation
        operation = WorkshopOperation(
            workshop_id=target_workshop.id,
            batch_id=batch_aggregate.id,
            wagon_count=len(batch_wagons),
            processing_time=scheduling_result.estimated_processing_time,
            total_time=scheduling_result.estimated_processing_time,
        )

        return WorkshopOperationResult(
            operation=operation,
            success=True,
            error_message=None,
            processed_wagons=batch_wagons,
            batch_aggregate=batch_aggregate,
        )

    def select_optimal_workshop(
        self,
        wagon: Wagon,
        workshops: dict[str, Workshop],
    ) -> WorkshopOperationResult:
        """Select optimal workshop for wagon processing.

        Parameters
        ----------
        wagon : Wagon
            Wagon requiring workshop assignment
        workshops : dict[str, Workshop]
            Available workshops

        Returns
        -------
        WorkshopOperationResult
            Result containing selected workshop or error
        """
        # Update assignment service with current workshops
        self._workshop_assignment.workshops = workshops

        # Select workshop
        workshop_id = self._workshop_assignment.select_workshop(wagon)

        if not workshop_id:
            return WorkshopOperationResult(
                operation=None,
                success=False,
                error_message='No suitable workshop available for wagon',
                processed_wagons=[],
            )

        # Create minimal operation for selection
        operation = WorkshopOperation(
            workshop_id=workshop_id,
            batch_id='',
            wagon_count=1,
            processing_time=self._workshop_scheduling.calculate_processing_time(1),
            total_time=self._workshop_scheduling.calculate_processing_time(1),
        )

        return WorkshopOperationResult(
            operation=operation,
            success=True,
            error_message=None,
            processed_wagons=[wagon],
        )

    def calculate_batch_capacity(
        self,
        workshop: Workshop,
        available_wagons: int,
    ) -> WorkshopOperationResult:
        """Calculate optimal batch size for workshop.

        Parameters
        ----------
        workshop : Workshop
            Target workshop
        available_wagons : int
            Number of available wagons

        Returns
        -------
        WorkshopOperationResult
            Result containing batch capacity calculation
        """
        batch_size = self._batch_formation.calculate_batch_size_for_workshop(workshop, available_wagons)

        processing_time = self._workshop_scheduling.calculate_processing_time(batch_size)

        operation = WorkshopOperation(
            workshop_id=workshop.id,
            batch_id='',
            wagon_count=batch_size,
            processing_time=processing_time,
            total_time=processing_time,
        )

        return WorkshopOperationResult(
            operation=operation,
            success=True,
            error_message=None,
            processed_wagons=[],
        )

    def validate_workshop_assignment(
        self,
        wagon: Wagon,
        workshop_id: str,
    ) -> WorkshopOperationResult:
        """Validate if wagon can be assigned to workshop.

        Parameters
        ----------
        wagon : Wagon
            Wagon to validate
        workshop_id : str
            Target workshop ID

        Returns
        -------
        WorkshopOperationResult
            Result indicating validation success or failure
        """
        can_assign = self._workshop_assignment.can_assign(wagon, workshop_id)

        if not can_assign:
            return WorkshopOperationResult(
                operation=None,
                success=False,
                error_message=f'Wagon {wagon.id} cannot be assigned to workshop {workshop_id}',
                processed_wagons=[],
            )

        return WorkshopOperationResult(
            operation=None,
            success=True,
            error_message=None,
            processed_wagons=[wagon],
        )
