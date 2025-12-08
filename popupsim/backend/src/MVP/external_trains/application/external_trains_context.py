"""External Trains Context with hexagonal architecture."""

from typing import TYPE_CHECKING, Any

from MVP.configuration.domain.models.scenario import Scenario
from MVP.external_trains.application.ports.external_train_port import (
    ExternalTrainPort,
)
from MVP.external_trains.application.train_arrival_coordinator import (
    TrainArrivalCoordinator,
)
from MVP.external_trains.infrastructure.adapters.file_adapter import (
    FileAdapter,
)

if TYPE_CHECKING:
    from simulation.domain.aggregates.simulation_session import SimulationSession


class ExternalTrainsContext:
    """Main context for external train operations implementing BoundedContextPort.

    Implements ADR-001 with ports and adapters pattern for flexible
    integration with multiple external train data sources.

    Parameters
    ----------
    scenario : Scenario
        Scenario configuration
    port : ExternalTrainPort | None
        Port for retrieving train data (defaults to FileAdapter)
    """

    def __init__(
        self, scenario: Scenario, port: ExternalTrainPort | None = None
    ) -> None:
        self.scenario = scenario
        self.port = port if port else FileAdapter(scenario)
        self.train_arrival_coordinator = TrainArrivalCoordinator(scenario, self.port)
        self.session: SimulationSession | None = None

    def initialize(self, simulation_session: "SimulationSession") -> None:
        """Initialize context with simulation session."""
        self.session = simulation_session

    def start_processes(self) -> None:
        """Start external train simulation processes."""
        # External train operations are passive (triggered by workshop context)

    def get_metrics(self) -> dict[str, Any]:
        """Get external train metrics."""
        return {}

    def cleanup(self) -> None:
        """Cleanup resources."""

    def get_train_arrival_coordinator(self) -> TrainArrivalCoordinator:
        """Get coordinator for external train arrivals.

        Returns
        -------
        TrainArrivalCoordinator
            Coordinator responsible for external train arrival processing
        """
        return self.train_arrival_coordinator
