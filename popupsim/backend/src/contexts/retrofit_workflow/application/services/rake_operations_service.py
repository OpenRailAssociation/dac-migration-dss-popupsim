"""Rake Operations Service - Application service for rake lifecycle orchestration.

This module provides an application service that coordinates domain services
for complete rake operations without SimPy dependencies.
"""

from dataclasses import dataclass
from datetime import timedelta

from contexts.retrofit_workflow.domain.aggregates.rake_aggregate import Rake
from contexts.retrofit_workflow.domain.aggregates.rake_aggregate import RakeType
from contexts.retrofit_workflow.domain.entities.wagon import Wagon
from contexts.retrofit_workflow.domain.services.rake_lifecycle_manager import RakeFormationContext
from contexts.retrofit_workflow.domain.services.rake_lifecycle_manager import RakeLifecycleManager
from contexts.retrofit_workflow.domain.services.transport_planning_service import TransportPlanningService


# pylint: disable=too-many-instance-attributes
@dataclass
class RakeOperation:
    """Complete rake operation with formation, transport, and dissolution.

    Note: 8 attributes needed to capture complete operation lifecycle.
    """

    rake_id: str
    formation_track: str
    target_track: str
    rake_type: RakeType
    formation_time: timedelta
    transport_time: timedelta
    dissolution_time: timedelta
    total_time: timedelta


@dataclass
class RakeOperationResult:
    """Result of rake operation execution."""

    operation: RakeOperation | None
    success: bool
    error_message: str | None
    completed_wagons: list[Wagon]


class RakeOperationsService:
    """Application service for coordinating rake operations.

    Orchestrates domain services to provide complete rake lifecycle operations:
    - Formation with timing
    - Transport planning
    - Dissolution with timing
    - End-to-end operation coordination

    This service coordinates domain services without SimPy dependencies.
    """

    def __init__(
        self,
        rake_lifecycle_manager: RakeLifecycleManager,
        transport_planning_service: TransportPlanningService,
    ) -> None:
        """Initialize with domain services.

        Parameters
        ----------
        rake_lifecycle_manager : RakeLifecycleManager
            Domain service for rake formation/dissolution
        transport_planning_service : TransportPlanningService
            Domain service for transport planning
        """
        self._rake_lifecycle = rake_lifecycle_manager
        self._transport_planning = transport_planning_service

    def create_formation_operation(
        self,
        wagons: list[Wagon],
        context: RakeFormationContext,
    ) -> RakeOperationResult:
        """Create rake formation operation with timing.

        Parameters
        ----------
        wagons : list[Wagon]
            Wagons to form into rake
        context : RakeFormationContext
            Formation context with track, type, and timing info

        Returns
        -------
        RakeOperationResult
            Result containing operation details or error
        """
        if not wagons:
            return RakeOperationResult(
                operation=None,
                success=False,
                error_message='Cannot create formation operation with no wagons',
                completed_wagons=[],
            )

        # Form rake using domain service
        formation_result = self._rake_lifecycle.form_rake(wagons, context)

        if not formation_result.success:
            return RakeOperationResult(
                operation=None,
                success=False,
                error_message=formation_result.error_message,
                completed_wagons=[],
            )

        # Create operation with formation timing only
        operation = RakeOperation(
            rake_id=formation_result.rake.id if formation_result.rake else 'unknown',
            formation_track=context.formation_track,
            target_track=context.target_track,
            rake_type=context.rake_type,
            formation_time=formation_result.formation_duration,
            transport_time=timedelta(0),
            dissolution_time=timedelta(0),
            total_time=formation_result.formation_duration,
        )

        return RakeOperationResult(
            operation=operation,
            success=True,
            error_message=None,
            completed_wagons=wagons,
        )

    def create_transport_operation(
        self,
        rake: Rake,
        wagons: list[Wagon],
        from_track: str,
        to_track: str,
    ) -> RakeOperationResult:
        """Create rake transport operation with timing.

        Parameters
        ----------
        rake : Rake
            Rake to transport
        wagons : list[Wagon]
            Wagons in the rake
        from_track : str
            Source track
        to_track : str
            Destination track

        Returns
        -------
        RakeOperationResult
            Result containing operation details or error
        """
        # Plan transport using domain service
        transport_result = self._transport_planning.plan_transport(rake, from_track, to_track)

        if not transport_result.success:
            return RakeOperationResult(
                operation=None,
                success=False,
                error_message=transport_result.error_message,
                completed_wagons=[],
            )

        # Create operation with transport timing only
        operation = RakeOperation(
            rake_id=rake.id,
            formation_track=from_track,
            target_track=to_track,
            rake_type=rake.rake_type,
            formation_time=timedelta(0),
            transport_time=transport_result.plan.transport_time,
            dissolution_time=timedelta(0),
            total_time=transport_result.plan.transport_time,
        )

        return RakeOperationResult(
            operation=operation,
            success=True,
            error_message=None,
            completed_wagons=wagons,
        )

    def create_dissolution_operation(
        self,
        rake: Rake,
        wagons: list[Wagon],
    ) -> RakeOperationResult:
        """Create rake dissolution operation with timing.

        Parameters
        ----------
        rake : Rake
            Rake to dissolve
        wagons : list[Wagon]
            Wagons in the rake

        Returns
        -------
        RakeOperationResult
            Result containing operation details or error
        """
        # Dissolve rake using domain service
        dissolution_result = self._rake_lifecycle.dissolve_rake(rake, wagons)

        if not dissolution_result.success:
            return RakeOperationResult(
                operation=None,
                success=False,
                error_message='Rake dissolution failed',
                completed_wagons=[],
            )

        # Create operation with dissolution timing only
        operation = RakeOperation(
            rake_id=rake.id,
            formation_track='',
            target_track='',
            rake_type=rake.rake_type,
            formation_time=timedelta(0),
            transport_time=timedelta(0),
            dissolution_time=dissolution_result.dissolution_duration,
            total_time=dissolution_result.dissolution_duration,
        )

        return RakeOperationResult(
            operation=operation,
            success=True,
            error_message=None,
            completed_wagons=dissolution_result.wagons,
        )

    def create_complete_operation(
        self,
        wagons: list[Wagon],
        formation_track: str,
        target_track: str,
        rake_type: RakeType,
    ) -> RakeOperationResult:
        """Create complete rake operation (formation + transport + dissolution).

        Parameters
        ----------
        wagons : list[Wagon]
            Wagons for the complete operation
        formation_track : str
            Track where rake is formed
        target_track : str
            Destination track
        rake_type : RakeType
            Type of rake
        formation_time : float
            Simulation time when operation starts

        Returns
        -------
        RakeOperationResult
            Result containing complete operation timing
        """
        if not wagons:
            return RakeOperationResult(
                operation=None,
                success=False,
                error_message='Cannot create complete operation with no wagons',
                completed_wagons=[],
            )

        # Calculate all timing components
        formation_duration = self._rake_lifecycle.calculate_formation_time(wagons)
        transport_duration = self._transport_planning.calculate_transport_time(formation_track, target_track)
        dissolution_duration = self._rake_lifecycle.calculate_dissolution_time(wagons)

        total_duration = formation_duration + transport_duration + dissolution_duration

        # Create complete operation
        operation = RakeOperation(
            rake_id=f'RAKE_{formation_track}_{target_track}_{len(wagons)}',
            formation_track=formation_track,
            target_track=target_track,
            rake_type=rake_type,
            formation_time=formation_duration,
            transport_time=transport_duration,
            dissolution_time=dissolution_duration,
            total_time=total_duration,
        )

        return RakeOperationResult(
            operation=operation,
            success=True,
            error_message=None,
            completed_wagons=wagons,
        )
