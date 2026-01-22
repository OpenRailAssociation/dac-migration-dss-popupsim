"""Event collector for exporting simulation data."""

import json
from pathlib import Path
from typing import TYPE_CHECKING

from contexts.retrofit_workflow.domain.events import LocomotiveMovementEvent
from contexts.retrofit_workflow.domain.events import ResourceStateChangeEvent
from contexts.retrofit_workflow.domain.events import WagonJourneyEvent
from contexts.retrofit_workflow.domain.events.batch_events import BatchArrivedAtDestination
from contexts.retrofit_workflow.domain.events.batch_events import BatchFormed
from contexts.retrofit_workflow.domain.events.batch_events import BatchTransportStarted
import pandas as pd

if TYPE_CHECKING:
    from infrastructure.logging import ProcessLogger


class EventCollector:
    """Collects all simulation events and exports to CSV/JSON."""

    def __init__(self, process_logger: 'ProcessLogger | None' = None) -> None:
        self.process_logger = process_logger
        self.wagon_events: list[WagonJourneyEvent] = []
        self.locomotive_events: list[LocomotiveMovementEvent] = []
        self.resource_events: list[ResourceStateChangeEvent] = []
        self.batch_events: list[BatchFormed | BatchTransportStarted | BatchArrivedAtDestination] = []

    def add_wagon_event(self, event: WagonJourneyEvent) -> None:
        """Add wagon journey event and log to process log."""
        self.wagon_events.append(event)

        if self.process_logger:
            self.process_logger.set_time(event.timestamp)
            self.process_logger.log(f'Wagon {event.wagon_id}: {event.event_type} at {event.location}')

    def add_locomotive_event(self, event: LocomotiveMovementEvent) -> None:
        """Add locomotive movement event and log to process log."""
        self.locomotive_events.append(event)

        if self.process_logger:
            self.process_logger.set_time(event.timestamp)
            from_loc = event.from_location or ''
            to_loc = event.to_location or ''
            movement = f'{from_loc} → {to_loc}' if from_loc or to_loc else event.purpose or ''
            self.process_logger.log(f'Loco {event.locomotive_id}: {event.event_type} {movement}')

    def add_resource_event(self, event: ResourceStateChangeEvent) -> None:
        """Add resource state change event."""
        self.resource_events.append(event)

    def add_batch_event(self, event: BatchFormed | BatchTransportStarted | BatchArrivedAtDestination) -> None:
        """Add batch event and log to process log."""
        self.batch_events.append(event)

        if self.process_logger:
            self.process_logger.set_time(event.timestamp)
            if isinstance(event, BatchFormed):
                self.process_logger.log(
                    f'Batch {event.batch_id}: FORMED with {len(event.wagon_ids)} wagons → {event.destination}'
                )
            elif isinstance(event, BatchTransportStarted):
                self.process_logger.log(
                    f'Batch {event.batch_id}: TRANSPORT_STARTED by {event.locomotive_id} → {event.destination}'
                )
            elif isinstance(event, BatchArrivedAtDestination):
                self.process_logger.log(
                    f'Batch {event.batch_id}: ARRIVED at {event.destination} ({event.wagon_count} wagons)'
                )

    def export_all(self, output_dir: str) -> None:
        """Export all data to output directory."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        self.export_wagon_journey(str(output_path / 'wagon_journey.csv'))
        self.export_rejected_wagons(str(output_path / 'rejected_wagons.csv'))
        self.export_locomotive_movements(str(output_path / 'locomotive_movements.csv'))
        self.export_track_capacity(str(output_path / 'track_capacity.csv'))
        self.export_locomotive_utilization(str(output_path / 'locomotive_utilization.csv'))
        self.export_workshop_utilization(str(output_path / 'workshop_utilization.csv'))
        self.export_summary_metrics(str(output_path / 'summary_metrics.json'))

    def export_wagon_journey(self, filepath: str) -> None:
        """Export complete wagon journey timeline."""
        df = pd.DataFrame(
            [
                {
                    'timestamp': e.timestamp,
                    'wagon_id': e.wagon_id,
                    'train_id': e.train_id or '',
                    'event': e.event_type,
                    'location': e.location,
                    'status': e.status,
                    'rejection_reason': e.rejection_reason or '',
                    'rejection_description': e.rejection_description or '',
                }
                for e in self.wagon_events
            ]
        )
        df.to_csv(filepath, index=False)

    def export_rejected_wagons(self, filepath: str) -> None:
        """Export rejected wagons with reasons."""
        rejected = [e for e in self.wagon_events if e.event_type == 'REJECTED']
        df = pd.DataFrame(
            [
                {
                    'wagon_id': e.wagon_id,
                    'train_id': e.train_id,
                    'rejection_reason': e.rejection_reason,
                    'rejection_description': e.rejection_description,
                    'timestamp': e.timestamp,
                }
                for e in rejected
            ]
        )
        df.to_csv(filepath, index=False)

    def export_locomotive_movements(self, filepath: str) -> None:
        """Export locomotive movement timeline."""
        df = pd.DataFrame(
            [
                {
                    'timestamp': e.timestamp,
                    'locomotive_id': e.locomotive_id,
                    'event': e.event_type,
                    'from_location': e.from_location or '',
                    'to_location': e.to_location or '',
                    'purpose': e.purpose or '',
                }
                for e in self.locomotive_events
            ]
        )
        df.to_csv(filepath, index=False)

    def export_track_capacity(self, filepath: str) -> None:
        """Export track capacity changes over time."""
        track_events = [e for e in self.resource_events if e.resource_type == 'track']
        df = pd.DataFrame(
            [
                {
                    'timestamp': e.timestamp,
                    'track_id': e.resource_id,
                    'change_type': e.change_type,
                    'capacity': e.capacity,
                    'used_before': e.used_before,
                    'used_after': e.used_after,
                    'utilization_before_percent': 0.0,  # Disabled due to None handling
                    'utilization_after_percent': 0.0,  # Disabled due to None handling
                    'change_amount': e.change_amount,
                    'triggered_by': e.triggered_by or '',
                }
                for e in track_events
            ]
        )
        df.to_csv(filepath, index=False)

    def export_locomotive_utilization(self, filepath: str) -> None:
        """Export locomotive utilization changes over time."""
        loco_events = [e for e in self.resource_events if e.resource_type == 'locomotive']
        df = pd.DataFrame(
            [
                {
                    'timestamp': e.timestamp,
                    'change_type': e.change_type,
                    'total_locomotives': e.total_count,
                    'busy_before': e.busy_count_before,
                    'busy_after': e.busy_count_after,
                    'available_before': e.total_count - e.busy_count_before
                    if e.total_count and e.busy_count_before is not None and e.total_count > 0
                    else None,
                    'available_after': e.total_count - e.busy_count_after
                    if e.total_count and e.busy_count_after is not None and e.total_count > 0
                    else None,
                    'utilization_before_percent': 0.0,  # type: ignore[operator]
                    'utilization_after_percent': 0.0,  # type: ignore[operator]
                }
                for e in loco_events
            ]
        )
        df.to_csv(filepath, index=False)

    def export_workshop_utilization(self, filepath: str) -> None:
        """Export workshop bay utilization changes over time."""
        workshop_events = [e for e in self.resource_events if e.resource_type == 'workshop']
        df = pd.DataFrame(
            [
                {
                    'timestamp': e.timestamp,
                    'workshop_id': e.resource_id,
                    'change_type': e.change_type,
                    'total_bays': e.total_bays,
                    'busy_before': e.busy_bays_before,
                    'busy_after': e.busy_bays_after,
                    'available_before': e.total_bays - e.busy_bays_before
                    if e.total_bays and e.busy_bays_before is not None
                    else None,
                    'available_after': e.total_bays - e.busy_bays_after
                    if e.total_bays and e.busy_bays_after is not None
                    else None,
                    'utilization_before_percent': (e.busy_bays_before / e.total_bays * 100)
                    if e.total_bays and e.busy_bays_before is not None
                    else 0,
                    'utilization_after_percent': (e.busy_bays_after / e.total_bays * 100)
                    if e.total_bays and e.busy_bays_after is not None
                    else 0,
                }
                for e in workshop_events
            ]
        )
        df.to_csv(filepath, index=False)

    def export_summary_metrics(self, filepath: str) -> None:
        """Export summary metrics as JSON."""
        arrived = [e for e in self.wagon_events if e.event_type == 'ARRIVED']
        parked = [e for e in self.wagon_events if e.event_type == 'PARKED']
        rejected = [e for e in self.wagon_events if e.event_type == 'REJECTED']

        # Rejection breakdown
        rejection_counts: dict[str, int] = {}
        for e in rejected:
            reason = e.rejection_reason or 'unknown'
            rejection_counts[reason] = rejection_counts.get(reason, 0) + 1

        # Calculate simulation duration
        all_timestamps = [e.timestamp for e in self.wagon_events + self.locomotive_events + self.resource_events]
        sim_duration = max(all_timestamps) if all_timestamps else 0

        metrics = {
            'total_wagons_arrived': len(arrived),
            'total_wagons_parked': len(parked),
            'total_wagons_rejected': len(rejected),
            'rejection_breakdown': rejection_counts,
            'completion_rate': len(parked) / len(arrived) if arrived else 0,
            'throughput_per_hour': (len(parked) / sim_duration * 60) if sim_duration > 0 else 0,
            'simulation_duration_minutes': sim_duration,
            'total_events': {
                'wagon_events': len(self.wagon_events),
                'locomotive_events': len(self.locomotive_events),
                'resource_events': len(self.resource_events),
            },
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, indent=2)
