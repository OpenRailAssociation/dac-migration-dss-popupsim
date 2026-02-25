"""CSV exporter for dual-stream events."""

from pathlib import Path

import pandas as pd
from shared.domain.events.dual_stream_events import LocationChangeEvent
from shared.domain.events.dual_stream_events import ProcessEvent
from shared.domain.events.dual_stream_events import StateChangeEvent
from shared.infrastructure.simpy_time_converters import sim_ticks_to_datetime


class DualStreamCsvExporter:
    """Export dual-stream events to separate CSV files."""

    def __init__(self, start_datetime: str | None = None) -> None:
        """Initialize exporter."""
        self.start_datetime = start_datetime

    def _to_datetime(self, sim_time: float) -> str:
        """Convert simulation time to datetime."""
        if not self.start_datetime:
            return ''
        return sim_ticks_to_datetime(sim_time, self.start_datetime)

    def export_state_changes(self, events: list[StateChangeEvent], filepath: str | Path) -> None:
        """Export state change events."""
        df = pd.DataFrame(
            [
                {
                    'timestamp': e.timestamp,
                    'datetime': self._to_datetime(e.timestamp),
                    'resource_id': e.resource_id,
                    'resource_type': e.resource_type,
                    'state': e.state.value,
                    'train_id': e.train_id or '',
                    'batch_id': e.batch_id or '',
                    'rejection_reason': e.rejection_reason or '',
                }
                for e in events
            ]
        )
        df.to_csv(filepath, index=False)

    def export_location_changes(self, events: list[LocationChangeEvent], filepath: str | Path) -> None:
        """Export location change events."""
        df = pd.DataFrame(
            [
                {
                    'timestamp': e.timestamp,
                    'datetime': self._to_datetime(e.timestamp),
                    'resource_id': e.resource_id,
                    'resource_type': e.resource_type,
                    'location': e.location,
                    'previous_location': e.previous_location or '',
                    'route_path': '|'.join(e.route_path) if e.route_path else '',
                }
                for e in events
            ]
        )
        df.to_csv(filepath, index=False)

    def export_process_events(self, events: list[ProcessEvent], filepath: str | Path) -> None:
        """Export process events."""
        df = pd.DataFrame(
            [
                {
                    'timestamp': e.timestamp,
                    'datetime': self._to_datetime(e.timestamp),
                    'resource_id': e.resource_id,
                    'resource_type': e.resource_type,
                    'process_state': e.process_state.value,
                    'location': e.location,
                    'coupler_type': e.coupler_type or '',
                    'batch_id': e.batch_id or '',
                    'rake_id': e.rake_id or '',
                    'locomotive_id': e.locomotive_id or '',
                }
                for e in events
            ]
        )
        df.to_csv(filepath, index=False)

    def export_all(
        self,
        state_events: list[StateChangeEvent],
        location_events: list[LocationChangeEvent],
        process_events: list[ProcessEvent],
        output_dir: str | Path,
    ) -> None:
        """Export all event streams."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        self.export_state_changes(state_events, output_path / 'resource_states.csv')
        self.export_location_changes(location_events, output_path / 'resource_locations.csv')
        self.export_process_events(process_events, output_path / 'resource_processes.csv')
