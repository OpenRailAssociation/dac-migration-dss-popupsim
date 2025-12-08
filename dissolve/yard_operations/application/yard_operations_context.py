"""Yard Operations Context - Main entry point."""

import asyncio
from typing import TYPE_CHECKING, Any

from yard_operations.application.yard_operations_config import YardOperationsConfig
from yard_operations.domain.entities.classification_area import ClassificationArea
from yard_operations.domain.entities.parking_area import ParkingArea
from yard_operations.domain.services.hump_yard_service import HumpYardService
from yard_operations.domain.value_objects.yard_metrics import YardMetrics

if TYPE_CHECKING:
    from simulation.domain.aggregates.simulation_session import SimulationSession


class YardOperationsContext:
    """Main context for yard operations implementing BoundedContextPort.

    Parameters
    ----------
    config : YardOperationsConfig
        Configuration for yard operations
    """

    def __init__(self, config: YardOperationsConfig) -> None:
        self.config = config
        self.session: SimulationSession | None = None

        # Initialize classification area
        self.classification_area = ClassificationArea(
            area_id="main_classification",
            track_capacity=config.track_capacity,
            workshop_capacity=config.workshop_capacity,
        )

        # Initialize parking area
        self.parking_area = ParkingArea(
            parking_tracks=config.parking_tracks, track_capacity=config.track_capacity
        )

        # Initialize hump yard service
        self.hump_yard_service = HumpYardService(
            classification_area=self.classification_area,
            wagon_state=config.wagon_state,
            wagon_selector=config.wagon_selector,
        )

    def initialize(self, simulation_session: "SimulationSession") -> None:
        """Initialize context with simulation session."""
        self.session = simulation_session

    def start_processes(self) -> None:
        """Start yard simulation processes."""
        # Yard operations are passive (no active processes)

    def get_metrics(self) -> dict[str, Any]:
        """Get yard metrics."""
        return self._compute_yard_metrics()

    def cleanup(self) -> None:
        """Cleanup resources."""

    def get_hump_yard_service(self) -> HumpYardService:
        """Get hump yard service for wagon classification.

        Returns
        -------
        HumpYardService
            Service for hump yard operations
        """
        return self.hump_yard_service

    async def get_yard_metrics_async(self) -> dict[str, Any]:
        """Get yard operations metrics asynchronously.

        Returns
        -------
        Dict[str, Any]
            Yard metrics including hump rejection statistics
        """
        # Run metrics computation in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._compute_yard_metrics)

    def get_yard_metrics(self) -> dict[str, Any]:
        """Sync version for backward compatibility."""
        return self._compute_yard_metrics()

    def _compute_yard_metrics(self) -> dict[str, Any]:
        """Compute yard metrics."""
        rejection_stats = self.hump_yard_service.get_rejection_stats()

        yard_metrics = YardMetrics(
            yard_id="main_yard",
            total_wagons_processed=rejection_stats.total_rejections + 100,
            total_wagons_classified=100,
            total_wagons_rejected=rejection_stats.total_rejections,
            total_hump_time=60.0,
            rejection_stats=rejection_stats,
        )

        return {
            "hump_rejection_rate": yard_metrics.hump_rejection_rate,
            "hump_throughput": yard_metrics.hump_throughput_per_hour,
            "rejection_breakdown": yard_metrics.get_rejection_summary(),
            "bottleneck_analysis": yard_metrics.get_bottleneck_analysis(),
        }
