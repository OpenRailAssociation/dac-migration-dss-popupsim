"""Domain port for scenario loading (Hexagonal Architecture)."""

from abc import ABC
from abc import abstractmethod
from pathlib import Path

from configuration.application.dtos.scenario_input_dto import ScenarioInputDTO


class ScenarioPort(ABC):
    """Port for loading scenario DTOs from different sources."""

    @abstractmethod
    def load_scenario_dto(self, source: Path) -> ScenarioInputDTO:
        """Load scenario DTO from source."""

    @abstractmethod
    def supports(self, source: Path) -> bool:
        """Check if adapter supports this source."""
