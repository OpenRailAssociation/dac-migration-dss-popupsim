"""Workshop service configuration objects for parameter reduction."""

from dataclasses import dataclass
from typing import Any

from contexts.retrofit_workflow.domain.services.batch_formation_service import BatchFormationService
from contexts.retrofit_workflow.domain.services.workshop_assignment_strategies import WorkshopAssignmentStrategy
from contexts.retrofit_workflow.infrastructure.resources.workshop_resource_manager import WorkshopResourceManager
import simpy


@dataclass
class WorkshopServiceConfig:
    """Configuration for workshop services.

    Groups workshop service dependencies to reduce parameter counts
    in service constructors.
    """

    env: simpy.Environment
    workshop_resources: WorkshopResourceManager
    assignment_strategy: WorkshopAssignmentStrategy
    batch_service: BatchFormationService
    retrofit_time: float = 10.0


@dataclass
class WorkshopEventPublishers:
    """Event publishing configuration for workshop operations.

    Groups workshop-specific event publishers.
    """

    wagon_event_publisher: Any = None
    loco_event_publisher: Any = None
