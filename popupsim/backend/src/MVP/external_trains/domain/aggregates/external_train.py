"""External train aggregate root."""

from dataclasses import dataclass
from datetime import datetime

from MVP.external_trains.domain.value_objects.external_train_status import (
    ExternalTrainStatus,
)
from MVP.workshop_operations.domain.entities.wagon import Wagon


@dataclass
class ExternalTrain:
    """External train arriving from railway network.

    Parameters
    ----------
    train_id : str
        Unique identifier for the train
    arrival_time : datetime
        Scheduled arrival time
    origin_station : str
        Station where train originated
    destination_station : str
        Final destination station
    wagons : list[Wagon]
        List of wagons on the train
    operator : str
        Railway operator (DB, ÖBB, SBB, etc.)
    status : ExternalTrainStatus
        Current status of the train
    """

    train_id: str
    arrival_time: datetime
    origin_station: str
    destination_station: str
    wagons: list[Wagon]
    operator: str
    status: ExternalTrainStatus = ExternalTrainStatus.SCHEDULED

    def mark_arrived(self) -> None:
        """Mark train as arrived at facility."""
        self.status = ExternalTrainStatus.ARRIVED

    def mark_wagons_delivered(self) -> None:
        """Mark wagons as delivered to yard."""
        self.status = ExternalTrainStatus.WAGONS_DELIVERED

    def mark_departed(self) -> None:
        """Mark train as departed from facility."""
        self.status = ExternalTrainStatus.DEPARTED
