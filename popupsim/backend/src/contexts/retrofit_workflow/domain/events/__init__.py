"""Domain events package - consolidated event definitions."""

# Domain events for business logic
from .batch_events import BatchArrivedAtDestination
from .batch_events import BatchFormed
from .batch_events import BatchProcessingCompleted
from .batch_events import BatchTransportStarted
from .batch_events import DomainEvent
from .batch_events import WorkshopRetrofitCompleted
from .observability_events import CouplingEvent
from .observability_events import LocomotiveAssemblyEvent
from .observability_events import LocomotiveMovementEvent
from .observability_events import RejectionReason
from .observability_events import ResourceStateChangeEvent

# Observability events for tracking
from .observability_events import WagonJourneyEvent

__all__ = [
    # Domain events
    'BatchArrivedAtDestination',
    'BatchFormed',
    'BatchProcessingCompleted',
    'BatchTransportStarted',
    # Observability events
    'CouplingEvent',
    'DomainEvent',
    'LocomotiveAssemblyEvent',
    'LocomotiveMovementEvent',
    'RejectionReason',
    'ResourceStateChangeEvent',
    'WagonJourneyEvent',
    'WorkshopRetrofitCompleted',
]
