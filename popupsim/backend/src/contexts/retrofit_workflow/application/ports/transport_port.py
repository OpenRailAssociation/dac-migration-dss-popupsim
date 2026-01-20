"""Transport port for hexagonal architecture."""

from abc import ABC
from abc import abstractmethod
from collections.abc import Generator
from typing import Any

from ...domain.aggregates.batch_aggregate import BatchAggregate
from ...domain.entities.locomotive import Locomotive


class TransportPort(ABC):
    """Port for transport operations."""

    @abstractmethod
    def transport_batch_to_workshop(self, batch: BatchAggregate, workshop_id: str) -> Generator[Any, Any]:
        """Transport batch to workshop."""
        pass

    @abstractmethod
    def transport_batch_from_workshop(self, batch: BatchAggregate, destination: str) -> Generator[Any, Any]:
        """Transport batch from workshop."""
        pass

    @abstractmethod
    def return_locomotive(self, locomotive: Locomotive, origin: str) -> Generator[Any, Any]:
        """Return locomotive to origin."""
        pass


class ResourceAllocationPort(ABC):
    """Port for resource allocation."""

    @abstractmethod
    def allocate_locomotive(self) -> Generator[Any, Any, Locomotive]:
        """Allocate locomotive resource."""
        pass

    @abstractmethod
    def release_locomotive(self, locomotive: Locomotive) -> Generator[Any, Any]:
        """Release locomotive resource."""
        pass

    @abstractmethod
    def allocate_workshop_capacity(self, workshop_id: str, required_capacity: int) -> Generator[Any, Any]:
        """Allocate workshop capacity."""
        pass

    @abstractmethod
    def release_workshop_capacity(self, workshop_id: str, capacity: int) -> Generator[Any, Any]:
        """Release workshop capacity."""
        pass
