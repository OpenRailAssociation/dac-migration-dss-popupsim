"""Backward-compatible facade for EventCollector (delegates to refactored components)."""

import json
from pathlib import Path
from typing import TYPE_CHECKING

from contexts.retrofit_workflow.application.services.event_collection_service import EventCollectionService
from contexts.retrofit_workflow.application.services.metrics_aggregator import MetricsAggregator
from contexts.retrofit_workflow.domain.events import CouplingEvent
from contexts.retrofit_workflow.domain.events import LocomotiveMovementEvent
from contexts.retrofit_workflow.domain.events import ResourceStateChangeEvent
from contexts.retrofit_workflow.domain.events import WagonJourneyEvent
from contexts.retrofit_workflow.domain.events.batch_events import BatchArrivedAtDestination
from contexts.retrofit_workflow.domain.events.batch_events import BatchFormed
from contexts.retrofit_workflow.domain.events.batch_events import BatchTransportStarted
from contexts.retrofit_workflow.infrastructure.exporters.csv_event_exporter import CsvEventExporter
from shared.infrastructure.simpy_time_converters import sim_ticks_to_datetime

if TYPE_CHECKING:
    from infrastructure.logging import ProcessLogger


class EventCollector:  # pylint: disable=too-many-public-methods
    """Facade maintaining backward compatibility (delegates to refactored services).

    Note: Multiple public methods needed for backward compatibility with existing code.
    """

    def __init__(self, process_logger: 'ProcessLogger | None' = None, start_datetime: str | None = None) -> None:
        """Initialize event collector facade."""
        self._collection_service = EventCollectionService(process_logger)
        self._csv_exporter = CsvEventExporter(start_datetime)
        self._metrics = MetricsAggregator()
        self.start_datetime = start_datetime

    @property
    def wagon_events(self) -> list[WagonJourneyEvent]:
        """Get wagon events."""
        return self._collection_service.wagon_events

    @property
    def locomotive_events(self) -> list[LocomotiveMovementEvent]:
        """Get locomotive events."""
        return self._collection_service.locomotive_events

    @property
    def resource_events(self) -> list[ResourceStateChangeEvent]:
        """Get resource events."""
        return self._collection_service.resource_events

    @property
    def batch_events(self) -> list[BatchFormed | BatchTransportStarted | BatchArrivedAtDestination]:
        """Get batch events."""
        return self._collection_service.batch_events

    @property
    def coupling_events(self) -> list[CouplingEvent]:
        """Get coupling events."""
        return self._collection_service.coupling_events

    def add_wagon_event(self, event: WagonJourneyEvent) -> None:
        """Add wagon event."""
        self._collection_service.add_wagon_event(event)

    def add_locomotive_event(self, event: LocomotiveMovementEvent) -> None:
        """Add locomotive event."""
        self._collection_service.add_locomotive_event(event)

    def add_resource_event(self, event: ResourceStateChangeEvent) -> None:
        """Add resource event."""
        self._collection_service.add_resource_event(event)

    def add_batch_event(self, event: BatchFormed | BatchTransportStarted | BatchArrivedAtDestination) -> None:
        """Add batch event."""
        self._collection_service.add_batch_event(event)

    def add_coupling_event(self, event: CouplingEvent) -> None:
        """Add coupling event."""
        self._collection_service.add_coupling_event(event)

    def _sim_time_to_datetime(self, sim_time: float) -> str:
        """Convert simulation time to datetime (delegates to shared converter)."""
        if not self.start_datetime:
            return ''
        return sim_ticks_to_datetime(sim_time, self.start_datetime)

    def export_wagon_journey(self, filepath: str) -> None:
        """Export wagon journey."""
        self._csv_exporter.export_wagon_journey(self.wagon_events, filepath)

    def export_rejected_wagons(self, filepath: str) -> None:
        """Export rejected wagons."""
        self._csv_exporter.export_rejected_wagons(self.wagon_events, filepath)

    def export_locomotive_movements(self, filepath: str) -> None:
        """Export locomotive movements."""
        self._csv_exporter.export_locomotive_movements(self.locomotive_events, filepath)

    def export_track_capacity(self, filepath: str) -> None:
        """Export track capacity."""
        self._csv_exporter.export_track_capacity(self.resource_events, filepath)

    def export_locomotive_utilization(self, filepath: str) -> None:
        """Export locomotive utilization."""
        self._csv_exporter.export_locomotive_utilization(self.resource_events, filepath)

    def export_locomotive_util(self, filepath: str) -> None:
        """Export locomotive util (alias for backward compatibility)."""
        self._csv_exporter.export_locomotive_utilization(self.resource_events, filepath)

    def export_workshop_utilization(self, filepath: str) -> None:
        """Export workshop utilization."""
        self._csv_exporter.export_workshop_utilization(self.resource_events, filepath)

    def export_summary_metrics(self, filepath: str, simulation_end_time: float | None = None) -> None:
        """Export summary metrics.

        Args:
            filepath: Path to export file
            simulation_end_time: Actual simulation end time (if None, uses max event timestamp)
        """
        duration = (
            simulation_end_time
            if simulation_end_time is not None
            else self._metrics.get_sim_duration(self.wagon_events, self.locomotive_events, self.resource_events)
        )

        summary = {
            **self._metrics.get_event_counts(self.wagon_events, self.locomotive_events, self.batch_events),
            **self._metrics.get_wagon_metrics(self.wagon_events),
            **self._metrics.get_workshop_metrics(self.wagon_events, self.resource_events),
            **self._metrics.get_locomotive_metrics(self.locomotive_events, self.resource_events),
            **self._metrics.get_static_metrics(),
            'simulation_duration_minutes': duration,
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)

    def export_events_csv(self, filepath: str) -> None:
        """Export all events CSV."""
        self._csv_exporter.export_events_csv(self.wagon_events, self.locomotive_events, self.batch_events, filepath)

    def export_timeline(self, filepath: str) -> None:
        """Export timeline."""
        self._csv_exporter.export_timeline(self.wagon_events, self.resource_events, filepath)

    def export_workshop_metrics(self, filepath: str) -> None:
        """Export workshop metrics."""
        self._csv_exporter.export_workshop_metrics(self.wagon_events, filepath)

    def export_locomotive_time_breakdown(self, filepath: str) -> None:
        """Export locomotive time breakdown with coupling details."""
        self._csv_exporter.export_locomotive_time_breakdown(self.locomotive_events, self.coupling_events, filepath)

    def export_locomotive_journey(self, filepath: str) -> None:
        """Export detailed locomotive journey."""
        self._csv_exporter.export_locomotive_journey(self.locomotive_events, self.coupling_events, filepath)

    def export_all(self, output_dir: str, simulation_end_time: float | None = None) -> None:
        """Export all data.

        Args:
            output_dir: Directory to export files
            simulation_end_time: Actual simulation end time for duration calculation
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        self.export_wagon_journey(str(output_path / 'wagon_journey.csv'))
        self.export_rejected_wagons(str(output_path / 'rejected_wagons.csv'))
        self.export_locomotive_movements(str(output_path / 'locomotive_movements.csv'))
        self.export_locomotive_journey(str(output_path / 'locomotive_journey.csv'))
        self.export_track_capacity(str(output_path / 'track_capacity.csv'))
        self.export_locomotive_utilization(str(output_path / 'locomotive_utilization.csv'))
        self.export_locomotive_util(str(output_path / 'locomotive_util.csv'))
        self.export_locomotive_time_breakdown(str(output_path / 'locomotive_time_breakdown.csv'))
        self.export_workshop_utilization(str(output_path / 'workshop_utilization.csv'))
        self.export_summary_metrics(str(output_path / 'summary_metrics.json'), simulation_end_time)
        self.export_events_csv(str(output_path / 'events.csv'))
        self.export_timeline(str(output_path / 'timeline.csv'))
        self.export_workshop_metrics(str(output_path / 'workshop_metrics.csv'))
