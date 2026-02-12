"""Event collector for exporting simulation data."""

from datetime import datetime
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
from shared.infrastructure.simpy_time_converters import sim_ticks_to_timedelta

if TYPE_CHECKING:
    from infrastructure.logging import ProcessLogger


class EventCollector:
    """Collects all simulation events and exports to CSV/JSON."""

    def __init__(self, process_logger: 'ProcessLogger | None' = None, start_datetime: str | None = None) -> None:
        self.process_logger = process_logger
        self.start_datetime = start_datetime
        self.wagon_events: list[WagonJourneyEvent] = []
        self.locomotive_events: list[LocomotiveMovementEvent] = []
        self.resource_events: list[ResourceStateChangeEvent] = []
        self.batch_events: list[BatchFormed | BatchTransportStarted | BatchArrivedAtDestination] = []

    def _sim_time_to_datetime(self, sim_time: float) -> str:
        """Convert simulation time (ticks) to datetime string.

        Args:
            sim_time: Simulation time in ticks (minutes by default)

        Returns
        -------
            ISO format datetime string
        """
        if not self.start_datetime:
            return ''

        # Handle both datetime objects and strings
        if isinstance(self.start_datetime, datetime):
            start_dt = self.start_datetime
        else:
            start_dt = datetime.fromisoformat(self.start_datetime.replace('Z', '+00:00'))

        duration = sim_ticks_to_timedelta(sim_time)
        event_dt = start_dt + duration
        return event_dt.isoformat()

    def add_wagon_event(self, event: WagonJourneyEvent) -> None:
        """Add wagon journey event and log to process log."""
        print(f'EventCollector: Adding wagon event {event.event_type} for {event.wagon_id} at t={event.timestamp}')
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

        if self.process_logger:
            self.process_logger.set_time(event.timestamp)
            msg: str = ''
            if event.resource_type == 'locomotive':
                msg = (
                    f'Locomotive {event.resource_id}: {event.change_type}.'
                    f'Busy {event.busy_count_before} → {event.busy_count_after}'
                )
            elif event.resource_type == 'track':
                msg = (
                    f'Track {event.resource_id}: {event.change_type}. {event.capacity} '
                    'used : {event.used_before} → {event.used_after} = {event.change_amount}'
                )
            elif event.resource_type == 'workshop':
                msg = (
                    f'Workshop {event.resource_id}: {event.change_type}. {event.total_bays} '
                    'busy bays: {event.busy_bays_before} → {event.busy_bays_after}'
                )
            self.process_logger.log(msg)

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
        self.export_locomotive_summary(str(output_path / 'locomotive_util.csv'))
        self.export_workshop_utilization(str(output_path / 'workshop_utilization.csv'))
        self.export_summary_metrics(str(output_path / 'summary_metrics.json'))
        # Additional exports for dashboard compatibility
        self.export_events_csv(str(output_path / 'events.csv'))
        self.export_timeline(str(output_path / 'timeline.csv'))
        self.export_workshop_metrics(str(output_path / 'workshop_metrics.csv'))
        # Note: wagon_locations.csv removed - use wagon_journey.csv instead (track_id column)

    def export_wagon_journey(self, filepath: str) -> None:
        """Export complete wagon journey timeline with track locations."""
        df = pd.DataFrame(
            [
                {
                    'timestamp': e.timestamp,
                    'datetime': self._sim_time_to_datetime(e.timestamp),
                    'wagon_id': e.wagon_id,
                    'train_id': e.train_id or '',
                    'event': e.event_type,
                    'track_id': e.location,  # Renamed from 'location' for clarity
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

        def map_rejection_type(reason: str) -> str:
            """Map rejection reason to simplified type."""
            if not reason:
                return 'UNKNOWN'
            reason_upper = reason.upper()
            if 'LOADED' in reason_upper:
                return 'WAGON_LOADED'
            if 'NO_RETROFIT_NEEDED' in reason_upper or 'NO RETROFIT' in reason_upper:
                return 'NO_RETROFIT_NEEDED'
            if 'CAPACITY' in reason_upper or 'FULL' in reason_upper:
                return 'TRACK_FULL'
            return 'TRACK_FULL'  # Default for capacity issues

        df = pd.DataFrame(
            [
                {
                    'timestamp': e.timestamp,
                    'datetime': self._sim_time_to_datetime(e.timestamp),
                    'wagon_id': e.wagon_id,
                    'train_id': e.train_id,
                    'rejection_type': map_rejection_type(e.rejection_reason),
                    'detailed_reason': e.rejection_description or e.rejection_reason or '',
                    'track_id': e.location if e.location != 'REJECTED' else '',
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
                    'datetime': self._sim_time_to_datetime(e.timestamp),
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
                    'datetime': self._sim_time_to_datetime(e.timestamp),
                    'track_id': e.resource_id,
                    'change_type': e.change_type,
                    'capacity': e.capacity,
                    'used_before': e.used_before,
                    'used_after': e.used_after,
                    'utilization_before_percent': e.utilization_before_percent
                    if hasattr(e, 'utilization_before_percent')
                    else 0.0,
                    'utilization_after_percent': e.utilization_after_percent
                    if hasattr(e, 'utilization_after_percent')
                    else 0.0,
                    'change_amount': e.change_amount,
                    'triggered_by': e.triggered_by or '',
                }
                for e in track_events
            ]
        )
        df.to_csv(filepath, index=False)

    def export_locomotive_summary(self, filepath: str) -> None:
        """Export per-locomotive summary statistics for dashboard."""
        loco_times: dict[str, dict[str, float]] = {}
        loco_state: dict[str, tuple[float, str]] = {}

        for event in sorted(self.locomotive_events, key=lambda e: e.timestamp):
            loco_id = event.locomotive_id

            if loco_id not in loco_times:
                loco_times[loco_id] = {'moving': 0.0, 'parking': 0.0, 'coupling': 0.0, 'decoupling': 0.0, 'idle': 0.0}
                loco_state[loco_id] = (0.0, 'parking')

            last_time, last_state = loco_state[loco_id]
            if last_time > 0:
                loco_times[loco_id][last_state] += event.timestamp - last_time

            # Map event types directly to states
            event_type = event.event_type.lower()
            if event_type in loco_times[loco_id]:
                new_state = event_type
            elif event_type == 'allocated':
                new_state = 'coupling'  # Backward compatibility
            else:
                new_state = 'parking'  # Default fallback

            loco_state[loco_id] = (event.timestamp, new_state)

        # Final state to simulation end
        if self.locomotive_events:
            sim_end = max(e.timestamp for e in self.locomotive_events)
            for loco_id, (last_time, last_state) in loco_state.items():
                if last_time < sim_end:
                    loco_times[loco_id][last_state] += sim_end - last_time

        output_data = []
        for loco_id, times in sorted(loco_times.items()):
            total = sum(times.values())
            if total > 0:
                output_data.append(
                    {
                        'locomotive_id': loco_id,
                        'moving_percent': times['moving'] / total * 100,
                        'parking_percent': times['parking'] / total * 100,
                        'coupling_percent': times['coupling'] / total * 100,
                        'decoupling_percent': times['decoupling'] / total * 100,
                        'idle_percent': times['idle'] / total * 100,
                    }
                )

        pd.DataFrame(output_data).to_csv(filepath, index=False)

    def export_locomotive_utilization(self, filepath: str) -> None:
        """Export locomotive utilization changes over time."""
        loco_events = [e for e in self.resource_events if e.resource_type == 'locomotive']

        if not loco_events:
            # Create empty file with headers
            df = pd.DataFrame(
                columns=[
                    'timestamp',
                    'datetime',
                    'change_type',
                    'total_locomotives',
                    'busy_before',
                    'busy_after',
                    'available_before',
                    'available_after',
                    'utilization_before_percent',
                    'utilization_after_percent',
                ]
            )
        else:
            df = pd.DataFrame(
                [
                    {
                        'timestamp': e.timestamp,
                        'datetime': self._sim_time_to_datetime(e.timestamp),
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
                        'utilization_before_percent': (e.busy_count_before / e.total_count * 100)
                        if e.total_count and e.busy_count_before is not None and e.total_count > 0
                        else 0.0,
                        'utilization_after_percent': (e.busy_count_after / e.total_count * 100)
                        if e.total_count and e.busy_count_after is not None and e.total_count > 0
                        else 0.0,
                    }
                    for e in loco_events
                ]
            )
        df.to_csv(filepath, index=False)

    def export_workshop_utilization(self, filepath: str) -> None:
        """Export workshop bay utilization changes over time.

        Note: If no workshop resource events are collected, this will be empty.
        Workshop utilization can still be calculated from wagon events in workshop_metrics.csv.
        """
        workshop_events = [e for e in self.resource_events if e.resource_type == 'workshop']

        if not workshop_events:
            # Create empty file with headers
            df = pd.DataFrame(
                columns=[
                    'timestamp',
                    'datetime',
                    'workshop_id',
                    'change_type',
                    'total_bays',
                    'busy_before',
                    'busy_after',
                    'available_before',
                    'available_after',
                    'utilization_before_percent',
                    'utilization_after_percent',
                ]
            )
        else:
            df = pd.DataFrame(
                [
                    {
                        'timestamp': e.timestamp,
                        'datetime': self._sim_time_to_datetime(e.timestamp),
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
                        if e.total_bays and e.busy_bays_before is not None and e.total_bays > 0
                        else 0.0,
                        'utilization_after_percent': (e.busy_bays_after / e.total_bays * 100)
                        if e.total_bays and e.busy_bays_after is not None and e.total_bays > 0
                        else 0.0,
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
        retrofitted = [e for e in self.wagon_events if e.event_type == 'RETROFIT_COMPLETED']
        distributed = [e for e in self.wagon_events if e.event_type == 'DISTRIBUTED']

        # Count event types
        event_type_counts: dict[str, int] = {}
        for e in self.wagon_events + self.locomotive_events + self.batch_events:
            event_name = e.__class__.__name__
            event_type_counts[event_name] = event_type_counts.get(event_name, 0) + 1

        # Rejection breakdown
        rejection_counts: dict[str, int] = {}
        for e in rejected:
            reason = e.rejection_reason or 'unknown'
            rejection_counts[reason] = rejection_counts.get(reason, 0) + 1

        # Calculate simulation duration
        all_timestamps = [e.timestamp for e in self.wagon_events + self.locomotive_events + self.resource_events]
        sim_duration = max(all_timestamps) if all_timestamps else 0

        # Count total wagons in simulation (arrived + accepted into system)
        total_in_simulation = len(arrived)
        completed_wagons = len(parked)

        # Workshop statistics
        workshop_stats: dict[str, dict[str, int]] = {}
        for e in self.wagon_events:
            if e.event_type == 'RETROFIT_STARTED' and e.location:
                ws_id = e.location
                if ws_id not in workshop_stats:
                    workshop_stats[ws_id] = {'wagons_processed': 0, 'retrofits_started': 0}
                workshop_stats[ws_id]['retrofits_started'] += 1
            elif e.event_type == 'RETROFIT_COMPLETED' and e.location:
                ws_id = e.location
                if ws_id not in workshop_stats:
                    workshop_stats[ws_id] = {'wagons_processed': 0, 'retrofits_started': 0}
                workshop_stats[ws_id]['wagons_processed'] += 1

        # Locomotive statistics
        loco_allocated = len([e for e in self.locomotive_events if e.event_type == 'ALLOCATED'])
        loco_released = len([e for e in self.locomotive_events if e.event_type == 'RELEASED'])
        loco_movements = len([e for e in self.locomotive_events if e.event_type == 'MOVING'])

        # Calculate locomotive utilization from resource events
        loco_util_pct = 0.0
        loco_resource_events = [e for e in self.resource_events if e.resource_type == 'locomotive']
        if loco_resource_events:
            last_event = max(loco_resource_events, key=lambda e: e.timestamp)
            if hasattr(last_event, 'busy_count_after') and hasattr(last_event, 'total_count'):
                if last_event.total_count and last_event.total_count > 0:
                    loco_util_pct = (last_event.busy_count_after / last_event.total_count) * 100

        # Workshop utilization (average across all workshops)
        total_workshop_util = 0.0
        if workshop_stats:
            for ws_id in workshop_stats:
                ws_events = [
                    e for e in self.resource_events if e.resource_type == 'workshop' and e.resource_id == ws_id
                ]
                if ws_events:
                    # Calculate time-weighted utilization
                    total_time = 0.0
                    busy_time = 0.0
                    prev_time = 0.0
                    prev_busy = 0
                    prev_total = 0

                    for e in sorted(ws_events, key=lambda x: x.timestamp):
                        if prev_time > 0 and prev_total > 0:
                            duration = e.timestamp - prev_time
                            total_time += duration
                            busy_time += duration * (prev_busy / prev_total)

                        prev_time = e.timestamp
                        prev_busy = e.busy_bays_after if hasattr(e, 'busy_bays_after') else 0
                        prev_total = e.total_bays if hasattr(e, 'total_bays') else 0

                    # Add final period to simulation end
                    if prev_time > 0 and sim_duration > prev_time and prev_total > 0:
                        duration = sim_duration - prev_time
                        total_time += duration
                        busy_time += duration * (prev_busy / prev_total)

                    if total_time > 0:
                        total_workshop_util += (busy_time / total_time) * 100

            total_workshop_util /= len(workshop_stats)

        metrics = {
            'total_events': len(self.wagon_events) + len(self.locomotive_events) + len(self.batch_events),
            'event_counts': event_type_counts,
            'trains_arrived': len(set(e.train_id for e in arrived if e.train_id)),
            'wagons_arrived': total_in_simulation,
            'wagons_classified': 0,  # Not implemented in current workflow
            'wagons_distributed': len(distributed),
            'wagons_parked': completed_wagons,
            'retrofits_completed': len(retrofitted),
            'wagons_rejected': len(rejected),
            'completion_rate': completed_wagons / total_in_simulation if total_in_simulation > 0 else 0,
            'throughput_rate_per_hour': (completed_wagons / sim_duration * 60) if sim_duration > 0 else 0,
            'workshop_statistics': {
                'total_workshops': len(workshop_stats),
                'workshops': workshop_stats,
                'total_wagons_processed': sum(ws['wagons_processed'] for ws in workshop_stats.values()),
            },
            'locomotive_statistics': {
                'utilization_percent': loco_util_pct,
                'allocations': loco_allocated,
                'releases': loco_released,
                'movements': loco_movements,
                'total_operations': loco_allocated + loco_released + loco_movements,
            },
            'shunting_statistics': {
                'total_operations': 0,
                'successful_operations': 0,
                'success_rate': 0.0,
            },
            'yard_statistics': {
                'wagons_classified': 0,
                'wagons_distributed': len(distributed),
                'wagons_parked': completed_wagons,
            },
            'capacity_statistics': {
                'total_wagon_movements': total_in_simulation,
                'active_operations': len(self.wagon_events) + len(self.locomotive_events) + len(self.batch_events),
                'events_per_hour': (len(self.wagon_events) + len(self.locomotive_events) + len(self.batch_events))
                / (sim_duration / 60)
                if sim_duration > 0
                else 0,
            },
            'current_state': {},
            'simulation_duration_minutes': sim_duration,
            'workshop_utilization': total_workshop_util,
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, indent=2)

    def export_events_csv(self, filepath: str) -> None:
        """Export all events in chronological order (legacy format compatibility)."""
        # Combine all events with unified format
        all_events = []

        # Add wagon events
        for e in self.wagon_events:
            all_events.append(
                {
                    'timestamp': e.timestamp,
                    'datetime': self._sim_time_to_datetime(e.timestamp),
                    'event_type': f'Wagon{e.event_type}Event',
                    'resource_type': 'wagon',
                    'resource_id': e.wagon_id,
                    'details': json.dumps(
                        {
                            'location': e.location,
                            'status': e.status,
                            'train_id': e.train_id or '',
                            'rejection_reason': e.rejection_reason or '',
                            'rejection_description': e.rejection_description or '',
                        }
                    ),
                }
            )

        # Add locomotive events
        for e in self.locomotive_events:
            all_events.append(
                {
                    'timestamp': e.timestamp,
                    'datetime': self._sim_time_to_datetime(e.timestamp),
                    'event_type': f'Locomotive{e.event_type}Event',
                    'resource_type': 'locomotive',
                    'resource_id': e.locomotive_id,
                    'details': json.dumps(
                        {
                            'from_location': e.from_location or '',
                            'to_location': e.to_location or '',
                            'purpose': e.purpose or '',
                        }
                    ),
                }
            )

        # Add batch events
        for e in self.batch_events:
            event_type = e.__class__.__name__
            details_dict = {
                'destination': e.destination,
                'wagon_count': e.wagon_count if hasattr(e, 'wagon_count') else len(e.wagon_ids),
                'locomotive_id': e.locomotive_id if hasattr(e, 'locomotive_id') else '',
            }
            # Add wagon_ids if available (BatchFormed event)
            if hasattr(e, 'wagon_ids'):
                details_dict['wagon_ids'] = ','.join(e.wagon_ids)

            all_events.append(
                {
                    'timestamp': e.timestamp,
                    'datetime': self._sim_time_to_datetime(e.timestamp),
                    'event_type': event_type,
                    'resource_type': 'batch',
                    'resource_id': e.batch_id,
                    'details': json.dumps(details_dict),
                }
            )

        # Sort by timestamp
        all_events.sort(key=lambda x: x['timestamp'])

        df = pd.DataFrame(all_events)
        df.to_csv(filepath, index=False)

    def export_wagon_locations(self, filepath: str) -> None:
        """Export current wagon locations (final state)."""
        # Build final state from events
        wagon_states: dict[str, dict[str, str]] = {}

        for e in self.wagon_events:
            wagon_id = e.wagon_id
            if wagon_id not in wagon_states:
                wagon_states[wagon_id] = {
                    'wagon_id': wagon_id,
                    'train_id': e.train_id or '',
                    'current_track': e.location,
                    'status': e.status,
                }
            else:
                # Update with latest state
                wagon_states[wagon_id]['current_track'] = e.location
                wagon_states[wagon_id]['status'] = e.status
                if e.train_id:
                    wagon_states[wagon_id]['train_id'] = e.train_id

        df = pd.DataFrame(list(wagon_states.values()))
        if not df.empty:
            df = df.sort_values('wagon_id')
        df.to_csv(filepath, index=False)

    def export_timeline(self, filepath: str) -> None:
        """Export bottleneck analysis timeline with dynamic track discovery."""
        all_timestamps = [e.timestamp for e in self.wagon_events + self.locomotive_events + self.resource_events]
        if not all_timestamps:
            pd.DataFrame(columns=['timestamp', 'datetime']).to_csv(filepath, index=False)
            return

        # Discover all unique tracks from wagon events (excluding parking and rejected)
        all_tracks = set()
        for e in self.wagon_events:
            if e.location and e.location not in ['REJECTED'] and not e.location.startswith('parking'):
                all_tracks.add(e.location)

        # Discover all workshops from resource events
        all_workshops = set()
        for e in self.resource_events:
            if e.resource_type == 'workshop':
                all_workshops.add(e.resource_id)

        max_time = max(all_timestamps)
        timeline_data = []
        interval = 60.0  # Sample every hour
        current_time = 0.0

        while current_time <= max_time:
            # Track wagon locations by replaying events up to current_time
            wagon_locations: dict[str, str] = {}
            for e in sorted(self.wagon_events, key=lambda x: x.timestamp):
                if e.timestamp > current_time:
                    break
                if e.event_type in [
                    'ARRIVED',
                    'ON_RETROFIT_TRACK',
                    'RETROFIT_STARTED',
                    'RETROFIT_COMPLETED',
                    'PARKED',
                    'REJECTED',
                ]:
                    wagon_locations[e.wagon_id] = e.location

            # Count wagons per track
            track_counts: dict[str, int] = dict.fromkeys(all_tracks, 0)
            for _, location in wagon_locations.items():
                if location in all_tracks:
                    track_counts[location] += 1

            # Count busy workshop bays per workshop
            workshop_bays: dict[str, int] = dict.fromkeys(all_workshops, 0)
            for e in sorted(
                [e for e in self.resource_events if e.resource_type == 'workshop'], key=lambda x: x.timestamp
            ):
                if e.timestamp > current_time:
                    break
                if e.resource_id in workshop_bays:
                    workshop_bays[e.resource_id] = e.busy_bays_after if hasattr(e, 'busy_bays_after') else 0

            # Count busy locomotives
            loco_busy = 0
            for e in sorted(
                [e for e in self.resource_events if e.resource_type == 'locomotive'], key=lambda x: x.timestamp
            ):
                if e.timestamp > current_time:
                    break
                loco_busy = e.busy_count_after if hasattr(e, 'busy_count_after') else 0

            # Build row with dynamic columns
            row = {
                'timestamp': current_time,
                'datetime': self._sim_time_to_datetime(current_time),
            }
            # Add track columns (sorted for consistency)
            for track in sorted(all_tracks):
                row[f'track_{track}'] = track_counts[track]
            # Add workshop columns (sorted for consistency)
            for workshop in sorted(all_workshops):
                row[f'workshop_{workshop}_busy_bays'] = workshop_bays[workshop]
            # Add resource utilization
            row['locomotives_busy'] = loco_busy
            row['wagons_in_process'] = sum(track_counts.values()) + sum(workshop_bays.values())

            timeline_data.append(row)
            current_time += interval

        df = pd.DataFrame(timeline_data)
        df.to_csv(filepath, index=False)

    def export_workshop_metrics(self, filepath: str) -> None:
        """Export workshop performance metrics."""
        # Calculate per-workshop metrics from events
        workshop_stats: dict[str, dict[str, float]] = {}

        # Get all workshop IDs from wagon events
        for e in self.wagon_events:
            if e.event_type in ['RETROFIT_STARTED', 'RETROFIT_COMPLETED'] and e.location:
                workshop_id = e.location
                if workshop_id not in workshop_stats:
                    workshop_stats[workshop_id] = {
                        'completed_retrofits': 0,
                        'total_retrofit_time': 0.0,
                        'start_times': {},
                    }

                if e.event_type == 'RETROFIT_STARTED':
                    workshop_stats[workshop_id]['start_times'][e.wagon_id] = e.timestamp
                elif e.event_type == 'RETROFIT_COMPLETED':
                    workshop_stats[workshop_id]['completed_retrofits'] += 1
                    if e.wagon_id in workshop_stats[workshop_id]['start_times']:
                        start_time = workshop_stats[workshop_id]['start_times'][e.wagon_id]
                        workshop_stats[workshop_id]['total_retrofit_time'] += e.timestamp - start_time

        # Calculate simulation duration
        all_timestamps = [e.timestamp for e in self.wagon_events + self.locomotive_events]
        sim_duration = max(all_timestamps) if all_timestamps else 1.0

        # Build output data
        output_data = []
        for workshop_id, stats in sorted(workshop_stats.items()):
            completed = stats['completed_retrofits']
            total_retrofit_time = stats['total_retrofit_time']

            # Estimate 2 bays per workshop (typical configuration)
            num_bays = 2
            total_available_time = sim_duration * num_bays
            total_waiting_time = total_available_time - total_retrofit_time

            # Calculate utilization
            utilization_pct = (total_retrofit_time / total_available_time * 100) if total_available_time > 0 else 0

            # Throughput per hour
            throughput = (completed / (sim_duration / 60)) if sim_duration > 0 else 0

            output_data.append(
                {
                    'workshop_id': workshop_id,
                    'completed_retrofits': completed,
                    'total_retrofit_time': total_retrofit_time,
                    'total_waiting_time': total_waiting_time,
                    'throughput_per_hour': throughput,
                    'utilization_percent': utilization_pct,
                }
            )

        df = pd.DataFrame(output_data)
        df.to_csv(filepath, index=False)
