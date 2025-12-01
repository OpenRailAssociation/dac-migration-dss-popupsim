"""SimPy coordinator for PopUp retrofit operations."""

from collections.abc import Generator
import logging
from typing import Any

from analytics.domain.events.simulation_events import WagonRetrofittedEvent
from analytics.domain.value_objects.timestamp import Timestamp
from workshop_operations.domain.entities.wagon import Wagon
from workshop_operations.infrastructure.simulation.simpy_adapter import SimulationAdapter

from ..domain.services.retrofit_processor import PopUpRetrofitProcessor

logger = logging.getLogger(__name__)


class PopUpSimPyCoordinator:
    """Coordinates SimPy processes for PopUp operations."""

    def __init__(self, sim_adapter: SimulationAdapter) -> None:
        self.sim = sim_adapter
        self.processor = PopUpRetrofitProcessor()

    def process_wagon_simpy(
        self,
        wagon: Wagon,
        workshop_resource: Any,
        track_id: str,
        process_time: float,
        workshop_capacity_manager: Any,
        metrics: Any,
    ) -> Generator[Any, Any]:
        """SimPy process for wagon retrofit with resource management."""
        with workshop_resource.request() as station_req:
            yield station_req

            # Station acquired
            current_time = self.sim.current_time()
            wagon.retrofit_start_time = current_time
            workshop_capacity_manager.record_station_occupied(track_id, wagon.id, current_time)

            # Pure domain logic
            retrofit_result = self.processor.install_dac_coupler(wagon, f'popup_{track_id}')

            # SimPy timing
            yield self.sim.delay(process_time)

            # Update final state
            current_time = self.sim.current_time()
            wagon.retrofit_end_time = current_time
            workshop_capacity_manager.record_station_released(track_id, current_time)

            # Record event
            event = WagonRetrofittedEvent.create(
                timestamp=Timestamp.from_simulation_time(current_time),
                wagon_id=wagon.id,
                workshop_id=track_id,
                processing_duration=process_time,
            )
            metrics.record_event(event)

            logger.info('Wagon %s PopUp retrofit completed: %s', wagon.id, retrofit_result.reason)
