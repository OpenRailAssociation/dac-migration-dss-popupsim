"""Domain events for external train operations."""

from dataclasses import dataclass
from datetime import datetime

from analytics.domain.events.simulation_events import DomainEvent
from workshop_operations.domain.entities.wagon import Wagon


@dataclass(frozen=True)
class ExternalTrainArrivedEvent(DomainEvent):
    """Published when external train arrives at facility.

    Parameters
    ----------
    train_id : str
        Unique identifier for the train
    arrival_time : datetime
        Actual arrival time
    origin_station : str
        Station where train originated
    operator : str
        Railway operator
    """

    train_id: str
    arrival_time: datetime
    origin_station: str
    operator: str


@dataclass(frozen=True)
class WagonsDeliveredEvent(DomainEvent):
    """Published when wagons are delivered to yard from external train.

    Parameters
    ----------
    train_id : str
        Unique identifier for the train
    wagons : list[Wagon]
        List of wagons delivered
    delivery_location : str
        Location where wagons were delivered
    """

    train_id: str
    wagons: list[Wagon]
    delivery_location: str
