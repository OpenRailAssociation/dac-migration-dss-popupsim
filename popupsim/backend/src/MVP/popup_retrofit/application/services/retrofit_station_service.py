"""PopUp Retrofit Station Service - Application layer orchestration."""

import logging
from collections.abc import Generator
from typing import Any

from MVP.analytics.domain.events.simulation_events import (
    WagonRetrofittedEvent,
)
from MVP.analytics.domain.value_objects.timestamp import Timestamp
from MVP.popup_retrofit.domain.services.retrofit_processor import (
    PopUpRetrofitProcessor,
)
from MVP.popup_retrofit.domain.value_objects.retrofit_request import (
    RetrofitRequest,
)
from MVP.workshop_operations.domain.entities.wagon import (
    WagonStatus,
)
from shared.infrastructure.time_converters import to_ticks

logger = logging.getLogger(__name__)

# Enable detailed logging for debugging
logger.setLevel(logging.DEBUG)


class RetrofitStationService:  # pylint: disable=too-few-public-methods
    """Application service for PopUp retrofit operations."""

    def __init__(self, sim_engine: Any) -> None:
        """Initialize with simulation engine."""
        self.sim_engine = sim_engine

    def process_wagon_at_station(self, request: RetrofitRequest) -> Generator[Any, Any]:
        """Process wagon at retrofit station."""
        current_time = self.sim_engine.current_time()
        logger.info(
            "🔧 RETROFIT: Wagon %s requesting station at track %s (t=%.1f)",
            request.wagon.id,
            request.track_id,
            current_time,
        )

        workshop_request = request.workshop_resource.request()
        yield workshop_request

        acquire_time = self.sim_engine.current_time()
        logger.info(
            "✓ RETROFIT: Wagon %s acquired station at track %s (t=%.1f, waited %.1f min)",
            request.wagon.id,
            request.track_id,
            acquire_time,
            acquire_time - current_time,
        )

        request.workshop_capacity_manager.mark_station_busy(
            request.track_id, request.wagon.id
        )

        try:
            request.wagon.status = WagonStatus.RETROFITTING
            request.wagon.retrofit_start_time = self.sim_engine.current_time()
            logger.info(
                "⚙️  RETROFIT: Wagon %s started retrofitting at track %s (t=%.1f, duration=%.1f ticks)",
                request.wagon.id,
                request.track_id,
                request.wagon.retrofit_start_time,
                to_ticks(request.process_time),
            )

            yield self.sim_engine.delay(request.process_time)

            processor = PopUpRetrofitProcessor()
            processor.install_dac_coupler(request.wagon)
            request.wagon.status = WagonStatus.RETROFITTED
            request.wagon.retrofit_end_time = self.sim_engine.current_time()

            logger.info(
                "✅ RETROFIT: Wagon %s completed retrofitting at track %s (t=%.1f)",
                request.wagon.id,
                request.track_id,
                request.wagon.retrofit_end_time,
            )

            event = WagonRetrofittedEvent.create(
                timestamp=Timestamp.from_ticks(self.sim_engine.current_time()),
                wagon_id=request.wagon.id,
                workshop_id=request.track_id,
                processing_duration=to_ticks(request.process_time),
            )
            request.metrics.record_event(event)
        finally:
            release_time = self.sim_engine.current_time()
            request.workshop_resource.release(workshop_request)
            request.workshop_capacity_manager.mark_station_available(request.track_id)
            logger.info(
                "🔓 RETROFIT: Wagon %s released station at track %s (t=%.1f)",
                request.wagon.id,
                request.track_id,
                release_time,
            )
