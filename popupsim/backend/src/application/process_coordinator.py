"""Process coordinator for cross-context workflows."""

import logging
from collections.abc import Generator
from typing import Any

from application.simulation_infrastructure import SimulationInfrastructure
from configuration.domain.models.scenario import Scenario

logger = logging.getLogger(__name__)


class ProcessCoordinator:
    """Coordinates processes across bounded contexts."""

    def __init__(self, infra: SimulationInfrastructure, scenario: Scenario) -> None:
        self.infra = infra
        self.scenario = scenario

    def start_coordination_processes(self) -> None:
        """Start cross-context coordination processes."""
        logger.info("🚀 Starting process coordination")

        # Start train arrival process (External Trains → Yard)
        self.infra.engine.schedule_process(self._coordinate_train_arrivals())

        # Start workshop processing (Yard → PopUp → Yard)
        self.infra.engine.schedule_process(self._coordinate_workshop_processing())

        logger.info("✅ Process coordination started")

    def _coordinate_train_arrivals(self) -> Generator[Any, Any]:
        """Coordinate train arrivals from external trains to yard."""
        if not self.scenario.trains:
            return

        for train in self.scenario.trains:
            # Schedule train arrival
            arrival_time = (
                float(train.arrival_time.timestamp())
                if hasattr(train.arrival_time, "timestamp")
                else 0.0
            )
            yield self.infra.engine.delay(arrival_time)

            # Put wagons into incoming queue
            for wagon in train.wagons:
                yield self.infra.incoming_wagons.put(wagon)
                logger.debug("📥 Train %s: wagon %s arrived", train.train_id, wagon.id)

    def _coordinate_workshop_processing(self) -> Generator[Any, Any]:
        """Coordinate workshop processing workflow."""
        while True:
            # Simple coordination - move wagons from retrofit queues to retrofitted
            for workshop_id, workshop_queue in self.infra.wagons_for_retrofit.items():
                if len(workshop_queue.items) > 0:
                    wagon = yield workshop_queue.get()

                    # Simulate retrofit time
                    retrofit_time = 30.0  # minutes
                    yield self.infra.engine.delay(retrofit_time)

                    # Move to retrofitted queue
                    yield self.infra.retrofitted_wagons.put(wagon)
                    logger.debug(
                        "🔧 Workshop %s: wagon %s retrofitted", workshop_id, wagon.id
                    )

            yield self.infra.engine.delay(1.0)  # Check every minute
