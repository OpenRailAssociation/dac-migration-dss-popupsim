"""Event discovery functions for each context."""

from typing import Any

from contexts.external_trains.domain.events.train_events import TrainDepartedEvent
from shared.domain.events.locomotive_events import LocomotiveMovementCompletedEvent
from shared.domain.events.locomotive_events import LocomotiveMovementStartedEvent
from shared.domain.events.wagon_lifecycle_events import BatchRetrofittedEvent
from shared.domain.events.wagon_lifecycle_events import LocomotiveMovementRequestEvent
from shared.domain.events.wagon_lifecycle_events import TrainArrivedEvent
from shared.domain.events.wagon_lifecycle_events import WagonClassifiedEvent
from shared.domain.events.wagon_lifecycle_events import WagonReadyForParkingEvent
from shared.domain.events.wagon_lifecycle_events import WagonReadyForRetrofitEvent
from shared.domain.events.wagon_lifecycle_events import WagonRetrofitCompletedEvent
from shared.domain.events.wagon_lifecycle_events import WagonRetrofittedEvent
from shared.domain.events.wagon_movement_events import WagonMovedEvent


def discover_shared_events() -> list[type[Any]]:
    """Discover shared domain events."""
    return [
        TrainArrivedEvent,
        WagonClassifiedEvent,
        WagonReadyForRetrofitEvent,
        WagonRetrofittedEvent,
        WagonRetrofitCompletedEvent,
        BatchRetrofittedEvent,
        WagonReadyForParkingEvent,
        LocomotiveMovementRequestEvent,
        WagonMovedEvent,
        LocomotiveMovementStartedEvent,
        LocomotiveMovementCompletedEvent,
    ]


def discover_external_trains_events() -> list[type[Any]]:
    """Discover external trains events."""
    return [TrainDepartedEvent]


def discover_all_events() -> list[type[Any]]:
    """Discover all events from all contexts."""
    all_events = []
    for discoverer in get_all_discoverers():
        all_events.extend(discoverer())
    return all_events


def get_all_discoverers() -> list[Any]:
    """Get all event discovery functions."""
    return [
        discover_shared_events,
        discover_external_trains_events,
    ]
