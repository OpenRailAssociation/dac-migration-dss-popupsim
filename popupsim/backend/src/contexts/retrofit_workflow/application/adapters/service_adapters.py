"""Service implementations that implement domain interfaces."""

from typing import Any

from contexts.retrofit_workflow.domain.aggregates.rake_aggregate import Rake
from contexts.retrofit_workflow.domain.entities.wagon import Wagon
from contexts.retrofit_workflow.domain.entities.workshop import Workshop
from contexts.retrofit_workflow.domain.ports.service_interfaces import RakeFormationPort
from contexts.retrofit_workflow.domain.ports.service_interfaces import TransportPlanningPort
from contexts.retrofit_workflow.domain.ports.service_interfaces import WorkshopSchedulingPort
from contexts.retrofit_workflow.domain.services.rake_lifecycle_manager import RakeFormationContext
from contexts.retrofit_workflow.domain.services.rake_lifecycle_manager import RakeLifecycleManager
from contexts.retrofit_workflow.domain.services.transport_planning_service import TransportPlanningService
from contexts.retrofit_workflow.domain.services.workshop_scheduling_service import WorkshopSchedulingService
from contexts.retrofit_workflow.domain.value_objects.rake_formation_request import RakeFormationRequest


class RakeFormationAdapter(RakeFormationPort):
    """Adapter for rake formation service."""

    def __init__(self, rake_lifecycle_manager: RakeLifecycleManager) -> None:
        self._rake_lifecycle = rake_lifecycle_manager

    def form_rake(self, request: RakeFormationRequest) -> Any:
        """Form rake from request."""
        context = RakeFormationContext(
            formation_track=request.formation_track,
            target_track=request.target_track,
            rake_type=request.rake_type,
            formation_time=0.0,
        )
        return self._rake_lifecycle.form_rake(request.wagons, context)

    def dissolve_rake(self, rake: Rake) -> list[str]:
        """Dissolve rake and return wagon IDs."""
        return rake.wagon_ids.copy()


class TransportPlanningAdapter(TransportPlanningPort):
    """Adapter for transport planning service."""

    def __init__(self, transport_planning_service: TransportPlanningService) -> None:
        self._transport_planning = transport_planning_service

    def plan_transport(self, rake: Rake, from_track: str, to_track: str) -> Any:
        """Plan transport operation."""
        return {
            'rake': rake,
            'from_track': from_track,
            'to_track': to_track,
            'duration': self.calculate_transport_time(from_track, to_track),
        }

    def calculate_transport_time(self, from_track: str, to_track: str) -> Any:
        """Calculate transport time."""
        return self._transport_planning.calculate_transport_time(from_track, to_track)


class WorkshopSchedulingAdapter(WorkshopSchedulingPort):
    """Adapter for workshop scheduling service."""

    def __init__(self, workshop_scheduling_service: WorkshopSchedulingService) -> None:
        self._workshop_scheduling = workshop_scheduling_service

    def schedule_batch(self, wagons: list[Wagon], workshop: Workshop) -> Any:
        """Schedule batch for workshop processing."""
        return self._workshop_scheduling.schedule_batch(wagons, workshop)

    def calculate_processing_time(self, wagon_count: int) -> Any:
        """Calculate processing time."""
        return self._workshop_scheduling.calculate_processing_time(wagon_count)
