"""Primary port for external train data sources."""

from abc import ABC, abstractmethod
from datetime import datetime

from external_trains.domain.aggregates.external_train import ExternalTrain


class ExternalTrainPort(ABC):  # pylint: disable=too-few-public-methods
    """Primary port interface for external train data sources.

    This port defines the contract for retrieving external train information
    from various sources (files, APIs, EDI, manual entry).
    """

    @abstractmethod
    def get_arrival_schedule(self, start_date: datetime, end_date: datetime) -> list[ExternalTrain]:
        """Get scheduled train arrivals for date range.

        Parameters
        ----------
        start_date : datetime
            Start of date range
        end_date : datetime
            End of date range

        Returns
        -------
        list[ExternalTrain]
            List of scheduled external train arrivals
        """
