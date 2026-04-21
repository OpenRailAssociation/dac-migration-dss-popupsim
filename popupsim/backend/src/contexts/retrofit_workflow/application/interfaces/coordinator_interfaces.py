"""Coordinator interfaces for SOLID principles compliance."""

from abc import ABC
from abc import abstractmethod
from typing import Any


class CoordinatorInterface(ABC):
    """Common interface for all coordinators."""

    @abstractmethod
    def start_coordination(self) -> None:
        """Start coordination process."""

    @abstractmethod
    def stop_coordination(self) -> None:
        """Stop coordination process."""

    @abstractmethod
    def get_status(self) -> dict[str, Any]:
        """Get coordinator status."""


class TransportCoordinatorInterface(CoordinatorInterface):
    """Interface for transport coordinators."""

    @abstractmethod
    def transport_wagons(self, wagons: list[Any], from_track: str, to_track: str) -> Any:
        """Transport wagons between tracks."""


class WorkshopCoordinatorInterface(CoordinatorInterface):
    """Interface for workshop coordinators."""

    @abstractmethod
    def process_wagons(self, wagons: list[Any], workshop_id: str) -> Any:
        """Process wagons in workshop."""
