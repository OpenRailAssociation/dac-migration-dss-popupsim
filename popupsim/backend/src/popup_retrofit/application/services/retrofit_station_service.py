"""PopUp Retrofit Station Service - Application layer orchestration."""

from collections.abc import Generator
import logging
from typing import Any

from workshop_operations.domain.entities.wagon import Wagon

logger = logging.getLogger(__name__)


class RetrofitStationService:  # pylint: disable=too-few-public-methods
    """Application service for PopUp retrofit operations."""

    def __init__(self, simpy_coordinator: Any) -> None:
        """Initialize with SimPy coordinator."""
        self.simpy_coordinator = simpy_coordinator

    def process_wagon_at_station(
        self,
        wagon: Wagon,
        workshop_resource: Any,
        track_id: str,
        process_time: float,
        workshop_capacity_manager: Any,
        metrics: Any,
    ) -> Generator[Any, Any]:
        """Orchestrate wagon processing using SimPy coordinator."""
        yield from self.simpy_coordinator.process_wagon_simpy(
            wagon, workshop_resource, track_id, process_time, workshop_capacity_manager, metrics
        )
