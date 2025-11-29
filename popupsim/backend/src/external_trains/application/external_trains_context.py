"""External Trains Context with hexagonal architecture."""

from external_trains.application.ports.external_train_port import ExternalTrainPort
from external_trains.infrastructure.adapters.file_adapter import FileAdapter

from configuration.domain.models.scenario import Scenario

from .train_arrival_coordinator import TrainArrivalCoordinator


class ExternalTrainsContext:  # pylint: disable=too-few-public-methods
    """Main context for external train operations using hexagonal architecture.

    Implements ADR-001 with ports and adapters pattern for flexible
    integration with multiple external train data sources.

    Parameters
    ----------
    scenario : Scenario
        Scenario configuration
    port : ExternalTrainPort | None
        Port for retrieving train data (defaults to FileAdapter)
    """

    def __init__(self, scenario: Scenario, port: ExternalTrainPort | None = None) -> None:
        self.scenario = scenario
        self.port = port if port else FileAdapter(scenario)
        self.train_arrival_coordinator = TrainArrivalCoordinator(scenario, self.port)

    def get_train_arrival_coordinator(self) -> TrainArrivalCoordinator:
        """Get coordinator for external train arrivals.

        Returns
        -------
        TrainArrivalCoordinator
            Coordinator responsible for external train arrival processing
        """
        return self.train_arrival_coordinator
