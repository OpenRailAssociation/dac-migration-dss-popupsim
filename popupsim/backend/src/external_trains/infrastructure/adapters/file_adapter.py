"""File adapter for external train data from scenario files."""

from datetime import datetime

from external_trains.application.ports.external_train_port import ExternalTrainPort
from external_trains.domain.aggregates.external_train import ExternalTrain
from external_trains.domain.value_objects.external_train_status import ExternalTrainStatus

from configuration.domain.models.scenario import Scenario


class FileAdapter(ExternalTrainPort):  # pylint: disable=too-few-public-methods
    """Adapter for loading external train data from JSON/CSV scenario files.

    This adapter implements the ExternalTrainPort interface by reading
    train schedules from the existing scenario configuration files.

    Parameters
    ----------
    scenario : Scenario
        Scenario configuration containing train schedules
    """

    def __init__(self, scenario: Scenario) -> None:
        self.scenario = scenario

    def get_arrival_schedule(self, start_date: datetime, end_date: datetime) -> list[ExternalTrain]:
        """Get scheduled train arrivals from scenario files.

        Parameters
        ----------
        start_date : datetime
            Start of date range
        end_date : datetime
            End of date range

        Returns
        -------
        list[ExternalTrain]
            List of external trains scheduled to arrive in date range
        """
        if not self.scenario.trains:
            return []

        external_trains: list[ExternalTrain] = []

        for train in self.scenario.trains:
            # Filter trains within date range
            if start_date <= train.arrival_time <= end_date:
                external_train = ExternalTrain(
                    train_id=train.train_id,
                    arrival_time=train.arrival_time,
                    origin_station=train.origin if hasattr(train, 'origin') else 'Unknown',
                    destination_station=train.destination if hasattr(train, 'destination') else 'Unknown',
                    wagons=train.wagons,
                    operator='Unknown',  # Not in current scenario format
                    status=ExternalTrainStatus.SCHEDULED,
                )
                external_trains.append(external_train)

        return external_trains
