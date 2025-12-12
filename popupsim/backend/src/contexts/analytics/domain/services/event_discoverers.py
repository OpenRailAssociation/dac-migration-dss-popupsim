"""Event discovery functions for each context."""

from typing import Any

from contexts.external_trains.domain.events.train_events import TrainDepartedEvent
from contexts.popup_retrofit.domain.events.retrofit_events import RetrofitCompletedEvent
from contexts.popup_retrofit.domain.events.retrofit_events import RetrofitStartedEvent
from contexts.shunting_operations.domain.events.shunting_events import LocomotiveAllocatedEvent
from contexts.shunting_operations.domain.events.shunting_events import LocomotiveReleasedEvent
from contexts.shunting_operations.domain.events.shunting_events import ShuntingOperationCompletedEvent
from contexts.yard_operations.domain.events.yard_events import WagonDistributedEvent
from contexts.yard_operations.domain.events.yard_events import WagonParkedEvent
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
    ]


def discover_yard_events() -> list[type[Any]]:
    """Discover yard operations events."""
    return [WagonDistributedEvent, WagonParkedEvent]


def discover_shunting_events() -> list[type[Any]]:
    """Discover shunting operations events."""
    return [
        LocomotiveAllocatedEvent,
        LocomotiveReleasedEvent,
        ShuntingOperationCompletedEvent,
        LocomotiveMovementStartedEvent,
        LocomotiveMovementCompletedEvent,
    ]


def discover_popup_events() -> list[type[Any]]:
    """Discover popup retrofit events."""
    return [RetrofitStartedEvent, RetrofitCompletedEvent]


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
        discover_yard_events,
        discover_shunting_events,
        discover_popup_events,
        discover_external_trains_events,
    ]
