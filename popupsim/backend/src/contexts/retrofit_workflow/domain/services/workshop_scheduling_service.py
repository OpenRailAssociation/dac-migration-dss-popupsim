"""Workshop Scheduling Service - Pure domain service for workshop operations.

This module provides a domain service for scheduling workshop operations
without any simulation infrastructure dependencies.
"""

from dataclasses import dataclass
from datetime import timedelta

from contexts.retrofit_workflow.domain.entities.wagon import Wagon
from contexts.retrofit_workflow.domain.entities.workshop import Workshop


@dataclass
class SchedulingResult:
    """Result of workshop scheduling operation."""

    workshop_id: str
    batch_size: int
    estimated_processing_time: timedelta
    success: bool
    error_message: str | None = None


class WorkshopSchedulingService:
    """Pure domain service for simple workshop scheduling.

    Handles basic workshop operations without optimization complexity:
    - Batch scheduling based on bay availability
    - Processing time calculations
    - Simple capacity validation

    This service contains only business logic needed for current simulation.
    """

    def __init__(self, base_processing_time_minutes: float = 120.0) -> None:
        """Initialize with base processing time.

        Parameters
        ----------
        base_processing_time_minutes : float, default=120.0
            Base time in minutes to retrofit one wagon
        """
        self._base_processing_time = base_processing_time_minutes

    def schedule_batch(self, wagons: list[Wagon], workshop: Workshop) -> SchedulingResult:
        """Schedule wagons for workshop processing.

        Parameters
        ----------
        wagons : list[Wagon]
            Wagons to schedule for processing
        workshop : Workshop
            Target workshop for processing

        Returns
        -------
        SchedulingResult
            Scheduling result with timing and success information
        """
        if not wagons:
            return SchedulingResult(
                workshop_id=workshop.id,
                batch_size=0,
                estimated_processing_time=timedelta(0),
                success=False,
                error_message='Cannot schedule empty wagon list',
            )

        batch_size = len(wagons)

        # Check if workshop can accept the batch
        if not workshop.can_accept_batch(batch_size):
            return SchedulingResult(
                workshop_id=workshop.id,
                batch_size=batch_size,
                estimated_processing_time=timedelta(0),
                success=False,
                error_message=f'Workshop {workshop.id} has insufficient capacity. '
                f'Required: {batch_size}, Available: {workshop.available_capacity}',
            )

        # Calculate processing time (parallel processing in bays)
        processing_time = timedelta(minutes=self._base_processing_time)

        return SchedulingResult(
            workshop_id=workshop.id,
            batch_size=batch_size,
            estimated_processing_time=processing_time,
            success=True,
            error_message=None,
        )

    def calculate_processing_time(self, batch_size: int) -> timedelta:
        """Calculate processing time for a batch.

        Parameters
        ----------
        batch_size : int
            Number of wagons in batch (not used - parallel processing)

        Returns
        -------
        timedelta
            Processing time (same for all batch sizes due to parallel processing)
        """
        if batch_size <= 0:
            return timedelta(0)

        # Parallel processing - all wagons processed simultaneously
        return timedelta(minutes=self._base_processing_time)

    def can_workshop_handle_batch(self, batch_size: int, workshop: Workshop) -> bool:
        """Check if workshop can handle the batch.

        Parameters
        ----------
        batch_size : int
            Number of wagons in batch
        workshop : Workshop
            Workshop to check

        Returns
        -------
        bool
            True if workshop has sufficient capacity
        """
        return workshop.can_accept_batch(batch_size)
