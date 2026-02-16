"""Transport Planning Service - Pure domain service for transport operations.

This module provides a domain service for planning transport operations
without any simulation infrastructure dependencies.
"""

from dataclasses import dataclass
from datetime import timedelta

from contexts.configuration.application.dtos.route_input_dto import RouteType
from contexts.retrofit_workflow.domain.aggregates.rake_aggregate import Rake
from contexts.retrofit_workflow.domain.services.route_service import RouteService
from shared.infrastructure.simpy_time_converters import sim_ticks_to_timedelta


@dataclass
class TransportPlan:
    """Simple transport plan for rake movement between tracks."""

    rake_id: str
    from_track: str
    to_track: str
    route_type: RouteType
    transport_time: timedelta


@dataclass
class TransportPlanResult:
    """Result of transport planning operation."""

    plan: TransportPlan | None
    success: bool
    error_message: str | None


class TransportPlanningService:
    """Pure domain service for simple transport planning.

    Provides basic transport planning without optimization complexity:
    - Route lookup and validation
    - Transport time calculations
    - Simple feasibility checks

    This service contains only business logic needed for current simulation.
    """

    def __init__(self, route_service: RouteService) -> None:
        """Initialize with route service for transport calculations.

        Parameters
        ----------
        route_service : RouteService
            Service for route duration and type lookups
        """
        self._route_service = route_service

    def plan_transport(self, rake: Rake, from_track: str, to_track: str) -> TransportPlanResult:
        """Create simple transport plan with route and timing.

        Parameters
        ----------
        rake : Rake
            Rake to be transported
        from_track : str
            Source track identifier
        to_track : str
            Destination track identifier

        Returns
        -------
        TransportPlanResult
            Result containing transport plan or error information
        """
        if not rake:
            return TransportPlanResult(plan=None, success=False, error_message='Cannot plan transport for null rake')

        if from_track == to_track:
            return TransportPlanResult(
                plan=None, success=False, error_message=f'Source and destination tracks are the same: {from_track}'
            )

        # Get route information from existing RouteService
        route_type = self._route_service.get_route_type(from_track, to_track)
        transport_ticks = self._route_service.get_duration(from_track, to_track)
        transport_time = sim_ticks_to_timedelta(transport_ticks)

        # Create simple transport plan
        plan = TransportPlan(
            rake_id=rake.id,
            from_track=from_track,
            to_track=to_track,
            route_type=route_type,
            transport_time=transport_time,
        )

        return TransportPlanResult(plan=plan, success=True, error_message=None)

    def calculate_transport_time(self, from_track: str, to_track: str) -> timedelta:
        """Calculate transport time between tracks.

        Parameters
        ----------
        from_track : str
            Source track identifier
        to_track : str
            Destination track identifier

        Returns
        -------
        timedelta
            Base transport time between tracks
        """
        # Get base transport time from route
        base_transport_ticks = self._route_service.get_duration(from_track, to_track)
        return sim_ticks_to_timedelta(base_transport_ticks)

    def get_route_type(self, from_track: str, to_track: str) -> RouteType:
        """Get route type for transport between tracks.

        Parameters
        ----------
        from_track : str
            Source track identifier
        to_track : str
            Destination track identifier

        Returns
        -------
        RouteType
            Route type (MAINLINE or SHUNTING)
        """
        return self._route_service.get_route_type(from_track, to_track)
