"""Segregated interfaces for workshop operations following ISP."""

from abc import ABC
from abc import abstractmethod
from collections.abc import Generator
from typing import Any

from contexts.retrofit_workflow.domain.entities.wagon import Wagon
from contexts.retrofit_workflow.domain.entities.workshop import Workshop
from contexts.retrofit_workflow.domain.value_objects.batch_context import BatchContext


class BatchProcessor(ABC):  # pylint: disable=too-few-public-methods
    """Interface for batch processing operations."""

    @abstractmethod
    def process_batch(self, batch_context: BatchContext, workshop: Workshop) -> Generator[Any, Any]:
        """Process a batch of wagons in workshop."""


class WorkshopResourceAllocator(ABC):
    """Interface for workshop resource allocation."""

    @abstractmethod
    def allocate_bays(self, workshop_id: str, wagon_count: int) -> Generator[Any, Any, list[Any]]:
        """Allocate workshop bays for wagons."""

    @abstractmethod
    def release_bays(self, workshop_id: str, bay_requests: list[Any]) -> None:
        """Release workshop bays."""


class TransportOrchestrator(ABC):
    """Interface for transport orchestration."""

    @abstractmethod
    def transport_to_workshop(self, batch_context: BatchContext) -> Generator[Any, Any]:
        """Transport batch to workshop."""

    @abstractmethod
    def transport_from_workshop(self, batch_context: BatchContext) -> Generator[Any, Any]:
        """Transport batch from workshop."""


class WorkshopScheduler(ABC):
    """Interface for workshop scheduling operations."""

    @abstractmethod
    def select_next_workshop(self, workshops: list[Workshop], current_index: int) -> int:
        """Select next workshop for processing."""

    @abstractmethod
    def can_process_batch(self, workshop: Workshop, wagons: list[Wagon]) -> bool:
        """Check if workshop can process batch."""
