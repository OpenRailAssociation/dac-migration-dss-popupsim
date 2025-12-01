"""Train arrival coordination."""

from __future__ import annotations

from collections.abc import Generator
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from workshop_operations.application.orchestrator import WorkshopOrchestrator

logger = logging.getLogger(__name__)


class TrainArrivalCoordinator:  # pylint: disable=too-few-public-methods
    """Coordinates train arrivals and wagon classification."""

    def __init__(self, orchestrator: WorkshopOrchestrator) -> None:
        self.orchestrator = orchestrator

    def process_train_arrivals(self) -> Generator:
        """Process train arrivals and classify wagons."""
        scenario = self.orchestrator.scenario
        process_times = scenario.process_times
        if not process_times:
            raise ValueError('Scenario must have process_times configured')
        if not scenario.trains:
            raise ValueError('Scenario must have trains configured')

        logger.info('Starting train arrival generator for scenario %s', scenario.id)

        for train in scenario.trains:
            logger.debug('Waiting for next train arrival at %s', train.arrival_time)
            yield self.orchestrator.sim.delay((train.arrival_time - scenario.start_date).total_seconds() / 60.0)
            logger.info('Train %s arrived at %s', train.train_id, train.arrival_time)

            # Delay from train arrival to first wagon at hump
            yield self.orchestrator.sim.delay(process_times.train_to_hump_delay)

            # Process wagons through hump
            for wagon in train.wagons:
                logger.debug('Processing wagon %s through hump yard', wagon.id)

                # Use Yard Operations Context for wagon classification
                decision = self.orchestrator.yard_operations.hump_yard_service.process_wagon(
                    wagon, self.orchestrator.wagons_queue, self.orchestrator.rejected_wagons_queue
                )

                logger.debug('Wagon %s classification decision: %s', wagon.id, decision.value)
                yield self.orchestrator.sim.delay(process_times.wagon_hump_interval)

            # Signal train processed
            logger.info('Train %s fully processed, signaling pickup', train.train_id)
            self.orchestrator.train_processed_event.succeed()
            self.orchestrator.train_processed_event = self.orchestrator.sim.create_event()
            yield self.orchestrator.sim.delay(0)
