"""Transport configuration objects for reducing parameter counts."""

from collections.abc import Callable
from dataclasses import dataclass

from contexts.retrofit_workflow.domain.events import LocomotiveMovementEvent
from contexts.retrofit_workflow.domain.events import WagonJourneyEvent
from contexts.retrofit_workflow.domain.services.route_service import RouteService
from contexts.retrofit_workflow.domain.services.track_selection_service import TrackSelectionFacade
from contexts.retrofit_workflow.infrastructure.resources.locomotive_resource_manager import LocomotiveResourceManager
import simpy


@dataclass
class TransportConfig:
    """Configuration for transport operations.

    Groups core transport dependencies to reduce parameter counts
    in transport command constructors.
    """

    env: simpy.Environment
    locomotive_manager: LocomotiveResourceManager
    route_service: RouteService
    track_selector: TrackSelectionFacade


@dataclass
class EventPublishers:
    """Event publishing configuration.

    Groups event publishers to reduce parameter counts and
    provide consistent event handling across transport operations.
    """

    loco_event_publisher: Callable[[LocomotiveMovementEvent], None] | None = None
    wagon_event_publisher: Callable[[WagonJourneyEvent], None] | None = None
