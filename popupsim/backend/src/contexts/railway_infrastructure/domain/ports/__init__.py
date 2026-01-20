"""Domain ports for railway infrastructure context."""

from abc import ABC
from abc import abstractmethod
from typing import Any

from contexts.railway_infrastructure.domain.entities.track import Track
from contexts.railway_infrastructure.domain.repositories.track_occupancy_repository import TrackOccupancyRepository


class MetricsPort(ABC):
    """Port for metrics collection operations."""

    @abstractmethod
    def collect_track_metrics(self, tracks: dict[str, Track]) -> dict[str, Any]:
        """Collect track-related metrics."""

    @abstractmethod
    def collect_occupancy_metrics(self, repository: TrackOccupancyRepository) -> dict[str, Any]:
        """Collect occupancy-related metrics."""
