"""External train entity for External Trains Context."""

from dataclasses import dataclass
from enum import Enum
from typing import Any

from contexts.external_trains.domain.value_objects.arrival_metrics import ArrivalMetrics
from contexts.external_trains.domain.value_objects.train_id import TrainId


class TrainStatus(Enum):
    """Status of external train."""

    SCHEDULED = 'scheduled'
    ARRIVING = 'arriving'
    ARRIVED = 'arrived'
    DEPARTED = 'departed'


@dataclass
class ExternalTrain:
    """External train entity with arrival scheduling."""

    id: TrainId
    scheduled_arrival: float
    wagons: list[Any]  # Wagon entities from MVP
    status: TrainStatus = TrainStatus.SCHEDULED
    actual_arrival: float | None = None

    def arrive(self, arrival_time: float) -> ArrivalMetrics:
        """Mark train as arrived and return metrics."""
        self.status = TrainStatus.ARRIVED
        self.actual_arrival = arrival_time

        return ArrivalMetrics(
            scheduled_time=self.scheduled_arrival,
            actual_time=arrival_time,
            wagon_count=len(self.wagons),
        )

    def depart(self) -> None:
        """Mark train as departed."""
        self.status = TrainStatus.DEPARTED
