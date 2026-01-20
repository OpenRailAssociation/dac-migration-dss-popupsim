"""Transport interfaces for retrofit workflow context."""

from collections.abc import Generator
from typing import Any
from typing import Protocol

from contexts.retrofit_workflow.domain.entities.locomotive import Locomotive
from contexts.retrofit_workflow.domain.entities.wagon import Wagon


class TransportPort(Protocol):
    """Port interface for transport operations."""

    def allocate_locomotive(self) -> Generator[Any, Any, Locomotive]:
        """Allocate locomotive for transport."""

    def release_locomotive(self, locomotive: Locomotive) -> Generator[Any, Any]:
        """Release locomotive back to pool."""

    def remove_from_track(self, track_id: str, wagons: list[Wagon]) -> Generator[Any, Any]:
        """Remove wagons from track."""

    def add_to_track(self, track_id: str, wagons: list[Wagon]) -> Generator[Any, Any]:
        """Add wagons to track."""


class TransportService(Protocol):
    """Protocol for transport operations."""

    def transport_batch(
        self,
        batch: list[Wagon],
        from_location: str,
        to_location: str,
        purpose: str,
    ) -> Generator[Any, Any]:
        """Transport batch from one location to another."""

    def get_transport_duration(self, from_location: str, to_location: str) -> float:
        """Get transport duration between locations."""


class LocomotiveManager(Protocol):
    """Protocol for locomotive resource management."""

    def allocate(self, purpose: str, priority: int = 0) -> Generator[Any, Any, Locomotive]:
        """Allocate locomotive for specific purpose."""

    def release(self, locomotive: Locomotive) -> Generator[Any, Any]:
        """Release locomotive back to pool."""

    def get_available_count(self) -> int:
        """Get number of available locomotives."""


class RouteService(Protocol):
    """Protocol for route management."""

    def get_duration(self, from_location: str, to_location: str) -> float:
        """Get duration for route between locations."""

    def route_exists(self, from_location: str, to_location: str) -> bool:
        """Check if route exists between locations."""
