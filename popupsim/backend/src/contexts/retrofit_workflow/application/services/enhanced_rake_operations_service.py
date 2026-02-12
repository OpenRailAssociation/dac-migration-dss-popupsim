"""Enhanced Rake Operations Service with proper timing integration."""

from dataclasses import dataclass

from contexts.retrofit_workflow.domain.aggregates.rake_aggregate import Rake
from contexts.retrofit_workflow.domain.aggregates.rake_aggregate import RakeType
from contexts.retrofit_workflow.domain.entities.wagon import Wagon
from contexts.retrofit_workflow.domain.services.rake_lifecycle_manager import RakeFormationContext
from contexts.retrofit_workflow.domain.services.rake_lifecycle_manager import RakeLifecycleManager
from contexts.retrofit_workflow.domain.services.transport_planning_service import TransportPlanningService
from shared.infrastructure.simpy_time_converters import timedelta_to_sim_ticks


@dataclass
class RakeOperation:
    """Represents a rake operation with timing."""

    operation_type: str
    rake: Rake
    duration: float
    success: bool = True
    error_message: str | None = None


@dataclass
class TransportPlan:
    """Transport plan for rake movement."""

    rake: Rake
    from_track: str
    to_track: str
    route_duration: float
    formation_duration: float
    dissolution_duration: float
    total_duration: float


class EnhancedRakeOperationsService:
    """Enhanced rake operations service with proper timing integration."""

    def __init__(
        self,
        rake_lifecycle_manager: RakeLifecycleManager,
        transport_planning_service: TransportPlanningService,
    ):
        """Initialize service with domain services."""
        self._rake_lifecycle = rake_lifecycle_manager
        self._transport_planning = transport_planning_service

    def create_formation_operation(self, wagons: list[Wagon], from_track: str, to_track: str) -> RakeOperation:
        """Create rake formation operation with timing."""
        try:
            # Determine rake type based on tracks
            rake_type = self._determine_rake_type(to_track)

            # Create formation context

            context = RakeFormationContext(
                formation_track=from_track,
                target_track=to_track,
                rake_type=rake_type,
                formation_time=0.0,  # Will be calculated by service
            )

            # Form rake using domain service
            result = self._rake_lifecycle.form_rake(wagons, context)

            if not result.success:
                return RakeOperation(
                    operation_type='FORMATION',
                    rake=None,  # type: ignore
                    duration=0.0,
                    success=False,
                    error_message=result.error_message,
                )

            # Convert timedelta to float using centralized converter

            formation_duration = timedelta_to_sim_ticks(result.formation_duration)

            return RakeOperation(
                operation_type='FORMATION', rake=result.rake, duration=formation_duration, success=True
            )
        except Exception as e:
            return RakeOperation(
                operation_type='FORMATION',
                rake=None,  # type: ignore
                duration=0.0,
                success=False,
                error_message=str(e),
            )

    def create_transport_operation(self, rake: Rake, from_track: str, to_track: str) -> RakeOperation:
        """Create rake transport operation with timing."""
        try:
            # Plan transport using domain service
            route_duration_timedelta = self._transport_planning.calculate_transport_time(from_track, to_track)

            # Convert timedelta to float using centralized converter
            if hasattr(route_duration_timedelta, 'total_seconds'):
                route_duration = timedelta_to_sim_ticks(route_duration_timedelta)
            else:
                route_duration = float(route_duration_timedelta)  # Already a number

            return RakeOperation(operation_type='TRANSPORT', rake=rake, duration=route_duration, success=True)
        except Exception as e:
            return RakeOperation(
                operation_type='TRANSPORT', rake=rake, duration=0.0, success=False, error_message=str(e)
            )

    def create_dissolution_operation(self, rake: Rake) -> RakeOperation:
        """Create rake dissolution operation with timing."""
        try:
            # Calculate dissolution time using wagons (simplified - would need wagon entities)
            # For now, estimate based on wagon count
            estimated_dissolution_minutes = rake.wagon_count * 1.0  # 1 minute per wagon

            return RakeOperation(
                operation_type='DISSOLUTION', rake=rake, duration=estimated_dissolution_minutes, success=True
            )
        except Exception as e:
            return RakeOperation(
                operation_type='DISSOLUTION', rake=rake, duration=0.0, success=False, error_message=str(e)
            )

    def create_complete_transport_plan(self, wagons: list[Wagon], from_track: str, to_track: str) -> TransportPlan:
        """Create complete transport plan with all timing."""
        # Form rake
        rake_type = self._determine_rake_type(to_track)

        context = RakeFormationContext(
            formation_track=from_track, target_track=to_track, rake_type=rake_type, formation_time=0.0
        )

        result = self._rake_lifecycle.form_rake(wagons, context)
        if not result.success:
            raise ValueError(f'Failed to form rake: {result.error_message}')

        rake = result.rake

        # Calculate all durations
        formation_duration = timedelta_to_sim_ticks(result.formation_duration)
        route_duration_result = self._transport_planning.calculate_transport_time(from_track, to_track)

        # Handle both timedelta and float returns
        if hasattr(route_duration_result, 'total_seconds'):
            route_duration = timedelta_to_sim_ticks(route_duration_result)
        else:
            route_duration = float(route_duration_result)

        dissolution_duration = len(wagons) * 1.0  # Simplified dissolution time

        total_duration = formation_duration + route_duration + dissolution_duration

        return TransportPlan(
            rake=rake,
            from_track=from_track,
            to_track=to_track,
            route_duration=route_duration,
            formation_duration=formation_duration,
            dissolution_duration=dissolution_duration,
            total_duration=total_duration,
        )

    def dissolve_rake(self, rake: Rake) -> list[str]:
        """Dissolve rake and return wagon IDs."""
        # Simplified dissolution - just return the wagon IDs
        return rake.wagon_ids.copy()

    def _determine_rake_type(self, to_track: str) -> RakeType:
        """Determine rake type based on track movement."""
        if 'workshop' in to_track.lower() or 'ws' in to_track.lower():
            return RakeType.WORKSHOP_RAKE
        if 'retrofitted' in to_track.lower():
            return RakeType.RETROFITTED_RAKE
        if 'parking' in to_track.lower():
            return RakeType.PARKING_RAKE
        return RakeType.WORKSHOP_RAKE  # Default
