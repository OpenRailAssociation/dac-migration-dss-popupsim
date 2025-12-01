"""PopUp Retrofit Station Service for SimPy-based wagon processing."""

from collections.abc import Generator
from typing import Any
import logging

from analytics.domain.events.simulation_events import WagonRetrofittedEvent
from analytics.domain.value_objects.timestamp import Timestamp
from workshop_operations.domain.entities.wagon import CouplerType
from workshop_operations.domain.entities.wagon import Wagon
from workshop_operations.domain.entities.wagon import WagonStatus
from workshop_operations.infrastructure.simulation.simpy_adapter import SimulationAdapter

from ..popup_context import PopUpRetrofitContext

logger = logging.getLogger(__name__)


class RetrofitStationService:  # pylint: disable=too-few-public-methods
    """Service for processing wagons at PopUp retrofit stations."""

    def __init__(self, sim_adapter: SimulationAdapter, popup_context: PopUpRetrofitContext) -> None:
        """Initialize retrofit station service."""
        self.sim = sim_adapter
        self.popup_context = popup_context

    def process_wagon_at_station(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        wagon: Wagon,
        workshop_resource: Any,
        track_id: str,
        process_time: float,
        workshop_capacity_manager: Any,
        metrics: Any,
    ) -> Generator[Any, Any]:
        """Process single wagon at PopUp retrofit station.

        Handles SimPy resource management and PopUp-specific processing.
        """
        with workshop_resource.request() as station_req:
            yield station_req

            # Station acquired
            current_time = self.sim.current_time()
            wagon.retrofit_start_time = current_time
            workshop_capacity_manager.record_station_occupied(track_id, wagon.id, current_time)
            logger.debug('Wagon %s started PopUp retrofit at station (t=%.1f)', wagon.id, current_time)

            # Use PopUp Retrofit Context for DAC installation
            popup_workshop_id = f'popup_{track_id}'
            try:
                # Process wagon through PopUp workshop
                retrofit_result = self.popup_context.process_wagon_retrofit(popup_workshop_id, wagon)

                # Simulate the actual retrofit time
                yield self.sim.delay(process_time)

                logger.info(
                    'PopUp retrofit result for wagon %s: success=%s, duration=%.1f min',
                    wagon.id,
                    retrofit_result.success,
                    retrofit_result.duration,
                )

            except (ValueError, AttributeError, TypeError) as e:
                logger.error('PopUp retrofit failed for wagon %s: %s', wagon.id, e)
                # Fallback to standard processing
                wagon.status = WagonStatus.RETROFITTING
                yield self.sim.delay(process_time)
                wagon.status = WagonStatus.RETROFITTED
                wagon.retrofit_end_time = self.sim.current_time()
                wagon.needs_retrofit = False
                wagon.coupler_type = CouplerType.DAC

            # Update final state
            current_time = self.sim.current_time()
            wagon.retrofit_end_time = current_time
            workshop_capacity_manager.record_station_released(track_id, current_time)

            # Record domain event
            event = WagonRetrofittedEvent.create(
                timestamp=Timestamp.from_simulation_time(current_time),
                wagon_id=wagon.id,
                workshop_id=track_id,
                processing_duration=process_time,
            )
            metrics.record_event(event)

            logger.info(
                'Wagon %s PopUp retrofit completed at t=%s, coupler changed to DAC', wagon.id, wagon.retrofit_end_time
            )
