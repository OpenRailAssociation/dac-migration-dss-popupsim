"""Train arrival coordinator using hexagonal architecture."""

import logging
from collections.abc import Generator
from typing import Any

from MVP.configuration.domain.models.scenario import Scenario
from MVP.external_trains.application.ports.external_train_port import (
    ExternalTrainPort,
)
from MVP.external_trains.infrastructure.adapters.file_adapter import (
    FileAdapter,
)

logger = logging.getLogger(__name__)


class TrainArrivalCoordinator:  # pylint: disable=too-few-public-methods
    """Coordinates external train arrivals using hexagonal architecture.

    Uses ExternalTrainPort to retrieve train schedules from various sources
    (files, APIs, EDI, manual entry) and publishes domain events.

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

    def process_train_arrivals(self, popupsim: Any) -> Generator[Any]:
        """Process external train arrivals and publish events.

        Retrieves train schedule from port, waits for arrivals,
        and publishes ExternalTrainArrivedEvent and WagonsDeliveredEvent.

        Parameters
        ----------
        popupsim : Any
            Workshop orchestrator instance

        Yields
        ------
        Any
            SimPy events during train arrival processing
        """
        # Get arrival schedule from port
        external_trains = self.port.get_arrival_schedule(
            self.scenario.start_date, self.scenario.end_date
        )

        if not external_trains:
            msg = "No trains scheduled in scenario"
            raise ValueError(msg)

        logger.info(
            "Starting external train arrival coordinator for scenario %s",
            self.scenario.id,
        )
        logger.info("Loaded %d external trains from port", len(external_trains))

        for external_train in external_trains:
            # Wait for scheduled arrival time
            delay_minutes = (
                external_train.arrival_time - self.scenario.start_date
            ).total_seconds() / 60.0
            yield popupsim.sim.delay(delay_minutes)

            # Mark train as arrived
            external_train.mark_arrived()
            logger.info(
                "External train %s arrived from %s",
                external_train.train_id,
                external_train.origin_station,
            )

            # Publish ExternalTrainArrivedEvent (future: publish to event bus)
            logger.debug(
                "ExternalTrainArrivedEvent: train=%s origin=%s operator=%s",
                external_train.train_id,
                external_train.origin_station,
                external_train.operator,
            )

            # Mark wagons delivered
            external_train.mark_wagons_delivered()

            # Publish WagonsDeliveredEvent (future: publish to event bus)
            logger.debug(
                "WagonsDeliveredEvent: train=%s wagons=%d location=yard_entry",
                external_train.train_id,
                len(external_train.wagons),
            )

            yield popupsim.sim.delay(0)
