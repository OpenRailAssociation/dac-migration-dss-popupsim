"""Railway capacity domain service for cross-context capacity management."""

from dataclasses import dataclass
from typing import Any
from typing import Protocol


@dataclass
class CapacityInfo:
    """Information about track capacity."""

    track_id: str
    total_capacity: int
    available_capacity: int
    current_usage: int


class RailwayCapacityPort(Protocol):
    """Port for railway capacity management."""

    def get_available_capacity(self, track_id: str) -> int:
        """Get available capacity on a track."""

    def get_total_capacity(self, track_id: str) -> int:
        """Get total capacity of a track."""

    def request_track_capacity(self, track_id: str) -> Any:
        """Request capacity on a track."""


class RailwayCapacityService:
    """Domain service for railway capacity management across contexts."""

    def __init__(self, railway_capacity_port: RailwayCapacityPort) -> None:
        self._railway_port = railway_capacity_port

    def get_capacity_info(self, track_id: str) -> CapacityInfo:
        """Get comprehensive capacity information for a track."""
        total = self._railway_port.get_total_capacity(track_id)
        available = self._railway_port.get_available_capacity(track_id)
        current = total - available

        return CapacityInfo(
            track_id=track_id,
            total_capacity=total,
            available_capacity=available,
            current_usage=current,
        )

    def can_accept_wagons(self, track_id: str, wagon_count: int) -> bool:
        """Check if track can accept specified number of wagons."""
        available = self._railway_port.get_available_capacity(track_id)
        return available >= wagon_count

    def get_maximum_acceptable_count(self, track_id: str) -> int:
        """Get maximum number of wagons that can be accepted on track."""
        return self._railway_port.get_available_capacity(track_id)
