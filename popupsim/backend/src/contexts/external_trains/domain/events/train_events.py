"""Domain events for External Trains Context."""

from dataclasses import dataclass
from dataclasses import field
from typing import Any

from contexts.external_trains.domain.value_objects.arrival_metrics import ArrivalMetrics
from contexts.external_trains.domain.value_objects.train_id import TrainId


@dataclass(frozen=True)
class TrainArrivedEvent:
    """Event published when external train arrives."""

    train_id: TrainId
    wagons: list[Any]  # Wagon entities from MVP
    arrival_metrics: ArrivalMetrics
    event_id: str = field(default_factory=lambda: str(__import__('uuid').uuid4()))
    timestamp: float = field(default_factory=__import__('time').time)

    @property
    def event_type(self) -> str:
        return 'train_arrived'


@dataclass(frozen=True)
class TrainDepartedEvent:
    """Event published when external train departs."""

    train_id: TrainId
    departure_time: float
    event_id: str = field(default_factory=lambda: str(__import__('uuid').uuid4()))
    timestamp: float = field(default_factory=__import__('time').time)

    @property
    def event_type(self) -> str:
        return 'train_departed'
