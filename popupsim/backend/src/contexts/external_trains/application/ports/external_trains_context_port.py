"""Port interface for External Trains Context."""

from abc import ABC, abstractmethod
from typing import Any


class ExternalTrainsContextPort(ABC):
    """Port interface for External Trains Context operations."""

    @abstractmethod
    def schedule_train(
        self, train_id: str, arrival_time: float, wagons: list[Any]
    ) -> None:
        """Schedule external train arrival."""

    @abstractmethod
    def process_arrivals(self, current_time: float) -> None:
        """Process scheduled train arrivals."""

    @abstractmethod
    def get_scheduled_count(self) -> int:
        """Get count of scheduled trains."""
