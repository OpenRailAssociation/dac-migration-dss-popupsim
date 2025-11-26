"""Analytics domain events."""

from .base_event import DomainEvent
from .simulation_events import BottleneckDetectedEvent
from .simulation_events import WagonDeliveredEvent
from .simulation_events import WagonRetrofittedEvent
from .simulation_events import WorkshopUtilizationChangedEvent

__all__ = [
    'BottleneckDetectedEvent',
    'DomainEvent',
    'WagonDeliveredEvent',
    'WagonRetrofittedEvent',
    'WorkshopUtilizationChangedEvent',
]
