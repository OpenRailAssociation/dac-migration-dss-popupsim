"""Train schedule aggregate for External Trains Context."""

from dataclasses import dataclass
from dataclasses import field

from contexts.external_trains.domain.entities.external_train import ExternalTrain
from contexts.external_trains.domain.entities.external_train import TrainStatus
from contexts.external_trains.domain.events.train_events import TrainArrivedEvent
from contexts.external_trains.domain.events.train_events import TrainDepartedEvent
from contexts.external_trains.domain.value_objects.train_id import TrainId


@dataclass
class TrainSchedule:
    """Aggregate managing external train schedules."""

    trains: dict[str, ExternalTrain] = field(default_factory=dict)

    def add_train(self, train: ExternalTrain) -> None:
        """Add train to schedule."""
        self.trains[train.id.id] = train

    def get_train(self, train_id: TrainId) -> ExternalTrain | None:
        """Get train by ID."""
        return self.trains.get(train_id.id)

    def get_scheduled_trains(self) -> list[ExternalTrain]:
        """Get all scheduled trains."""
        return [train for train in self.trains.values() if train.status == TrainStatus.SCHEDULED]

    def process_arrival(self, train_id: TrainId, arrival_time: float) -> TrainArrivedEvent:
        """Process train arrival and return event."""
        train = self.get_train(train_id)
        if not train:
            msg = f'Train {train_id.id} not found'
            raise ValueError(msg)

        metrics = train.arrive(arrival_time)

        return TrainArrivedEvent(train_id=train_id, wagons=train.wagons, arrival_metrics=metrics)

    def process_departure(self, train_id: TrainId, departure_time: float) -> TrainDepartedEvent:
        """Process train departure and return event."""
        train = self.get_train(train_id)
        if not train:
            msg = f'Train {train_id.id} not found'
            raise ValueError(msg)

        train.depart()

        return TrainDepartedEvent(train_id=train_id, departure_time=departure_time)
