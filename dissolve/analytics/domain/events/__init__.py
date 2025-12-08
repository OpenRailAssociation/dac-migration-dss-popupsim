"""Analytics domain events."""

from .base_event import DomainEvent
from .locomotive_events import (
    LocomotiveAssignedEvent,
    LocomotiveIdleEvent,
    LocomotiveStatusChangeEvent,
)
from .resource_events import ResourceAllocatedEvent, ResourceReleasedEvent
from .retrofit_events import RetrofitCompletedEvent, RetrofitStartedEvent
from .simulation_events import (
    BottleneckDetectedEvent,
    WagonArrivedEvent,
    WagonDeliveredEvent,
    WagonMovedEvent,
    WagonRejectedEvent,
    WagonRetrofittedEvent,
    WorkshopUtilizationChangedEvent,
)
from .simulation_lifecycle_events import SimulationEndedEvent, SimulationStartedEvent
from .train_events import TrainArrivedEvent, TrainDepartedEvent
from .workshop_events import (
    WorkshopCapacityChangedEvent,
    WorkshopStationIdleEvent,
    WorkshopStationOccupiedEvent,
)

__all__ = [
    "BottleneckDetectedEvent",
    "DomainEvent",
    "LocomotiveAssignedEvent",
    "LocomotiveIdleEvent",
    "LocomotiveStatusChangeEvent",
    "ResourceAllocatedEvent",
    "ResourceReleasedEvent",
    "RetrofitCompletedEvent",
    "RetrofitStartedEvent",
    "SimulationEndedEvent",
    "SimulationStartedEvent",
    "TrainArrivedEvent",
    "TrainDepartedEvent",
    "WagonArrivedEvent",
    "WagonDeliveredEvent",
    "WagonMovedEvent",
    "WagonRejectedEvent",
    "WagonRetrofittedEvent",
    "WorkshopCapacityChangedEvent",
    "WorkshopStationIdleEvent",
    "WorkshopStationOccupiedEvent",
    "WorkshopUtilizationChangedEvent",
]
