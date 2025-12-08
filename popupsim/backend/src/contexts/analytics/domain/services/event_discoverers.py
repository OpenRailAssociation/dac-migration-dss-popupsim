"""Event discovery functions for each context."""

from typing import Any


def discover_shared_events() -> list[type[Any]]:
    """Discover shared domain events."""
    from shared.domain.events.wagon_lifecycle_events import (
        BatchRetrofittedEvent,
        LocomotiveMovementRequestEvent,
        TrainArrivedEvent,
        WagonClassifiedEvent,
        WagonReadyForParkingEvent,
        WagonReadyForRetrofitEvent,
        WagonRetrofitCompletedEvent,
        WagonRetrofittedEvent,
    )

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
    from contexts.yard_operations.domain.events.yard_events import (
        WagonDistributedEvent,
        WagonParkedEvent,
    )

    return [WagonDistributedEvent, WagonParkedEvent]


def discover_shunting_events() -> list[type[Any]]:
    """Discover shunting operations events."""
    from contexts.shunting_operations.domain.events.shunting_events import (
        LocomotiveAllocatedEvent,
        LocomotiveReleasedEvent,
        ShuntingOperationCompletedEvent,
    )
    from shared.domain.events.locomotive_events import (
        LocomotiveMovementCompletedEvent,
        LocomotiveMovementStartedEvent,
    )

    return [
        LocomotiveAllocatedEvent,
        LocomotiveReleasedEvent,
        ShuntingOperationCompletedEvent,
        LocomotiveMovementStartedEvent,
        LocomotiveMovementCompletedEvent,
    ]


def discover_popup_events() -> list[type[Any]]:
    """Discover popup retrofit events."""
    from contexts.popup_retrofit.domain.events.retrofit_events import (
        RetrofitCompletedEvent,
        RetrofitStartedEvent,
    )

    return [RetrofitStartedEvent, RetrofitCompletedEvent]


def discover_external_trains_events() -> list[type[Any]]:
    """Discover external trains events."""
    from contexts.external_trains.domain.events.train_events import (
        TrainDepartedEvent,
    )

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
