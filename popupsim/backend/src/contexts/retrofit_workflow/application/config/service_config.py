"""Service configuration for retrofit workflow context."""

from dataclasses import dataclass

from contexts.retrofit_workflow.application.interfaces.coordination_interfaces import CoordinationService
from contexts.retrofit_workflow.application.interfaces.transport_interfaces import RouteService
from contexts.retrofit_workflow.domain.services.batch_formation_service import BatchFormationService


@dataclass
class ServiceConfig:
    """Configuration for domain services."""

    batch_service: BatchFormationService
    route_service: RouteService
    coordination_service: CoordinationService

    def validate(self) -> None:
        """Validate service configuration."""
        if not self.batch_service:
            raise ValueError('BatchFormationService is required')
        if not self.route_service:
            raise ValueError('RouteService is required')
        if not self.coordination_service:
            raise ValueError('CoordinationService is required')
