"""Domain interfaces for SOLID principles compliance."""

from abc import ABC
from abc import abstractmethod
from typing import Any

from contexts.retrofit_workflow.domain.aggregates.rake_aggregate import Rake
from contexts.retrofit_workflow.domain.entities.wagon import Wagon
from contexts.retrofit_workflow.domain.entities.workshop import Workshop
from contexts.retrofit_workflow.domain.value_objects.rake_formation_request import RakeFormationRequest


class RakeFormationPort(ABC):
    """Interface for rake formation operations."""

    @abstractmethod
    def form_rake(self, request: RakeFormationRequest) -> Any:
        """Form rake from wagons."""

    @abstractmethod
    def dissolve_rake(self, rake: Rake) -> list[str]:
        """Dissolve rake and return wagon IDs."""


class TransportPlanningPort(ABC):
    """Interface for transport planning operations."""

    @abstractmethod
    def plan_transport(self, rake: Rake, from_track: str, to_track: str) -> Any:
        """Plan transport operation."""

    @abstractmethod
    def calculate_transport_time(self, from_track: str, to_track: str) -> Any:
        """Calculate transport time."""


class WorkshopSchedulingPort(ABC):
    """Interface for workshop scheduling operations."""

    @abstractmethod
    def schedule_batch(self, wagons: list[Wagon], workshop: Workshop) -> Any:
        """Schedule batch for workshop processing."""

    @abstractmethod
    def calculate_processing_time(self, wagon_count: int) -> Any:
        """Calculate processing time."""


class RakeOperationsPort(ABC):
    """Interface for rake operations coordination."""

    @abstractmethod
    def create_formation_operation(self, wagons: list[Wagon], from_track: str, to_track: str) -> Any:
        """Create rake formation operation."""

    @abstractmethod
    def create_transport_operation(self, rake: Rake, from_track: str, to_track: str) -> Any:
        """Create transport operation."""

    @abstractmethod
    def create_dissolution_operation(self, rake: Rake) -> Any:
        """Create dissolution operation."""


class WorkshopOperationsPort(ABC):
    """Interface for workshop operations coordination."""

    @abstractmethod
    def create_processing_operation(self, wagons: list[Wagon], workshop: Workshop) -> Any:
        """Create processing operation."""

    @abstractmethod
    def select_optimal_workshop(self, wagon: Wagon, workshops: dict[str, Workshop]) -> Any:
        """Select optimal workshop."""
