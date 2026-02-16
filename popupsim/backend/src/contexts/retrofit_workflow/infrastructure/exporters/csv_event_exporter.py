"""CSV exporter for simulation events."""

import json
from typing import Any

from contexts.retrofit_workflow.domain.events import CouplingEvent
from contexts.retrofit_workflow.domain.events import LocomotiveMovementEvent
from contexts.retrofit_workflow.domain.events import ResourceStateChangeEvent
from contexts.retrofit_workflow.domain.events import WagonJourneyEvent
from contexts.retrofit_workflow.domain.events.batch_events import BatchArrivedAtDestination
from contexts.retrofit_workflow.domain.events.batch_events import BatchFormed
from contexts.retrofit_workflow.domain.events.batch_events import BatchTransportStarted
import pandas as pd
from shared.infrastructure.simpy_time_converters import sim_ticks_to_datetime


class CsvEventExporter:
    """Exports simulation events to CSV files."""

    def __init__(self, start_datetime: str | None = None) -> None:
        """Initialize CSV exporter."""
        self.start_datetime = start_datetime

    def _to_datetime(self, sim_time: float) -> str:
        """Convert simulation time to datetime string."""
        if not self.start_datetime:
            return ''
        return sim_ticks_to_datetime(sim_time, self.start_datetime)

    def export_wagon_journey(self, events: list[WagonJourneyEvent], filepath: str) -> None:
        """Export wagon journey events to CSV."""
        df = pd.DataFrame(
            [
                {
                    'timestamp': e.timestamp,
                    'datetime': self._to_datetime(e.timestamp),
                    'wagon_id': e.wagon_id,
                    'train_id': e.train_id or '',
                    'event': e.event_type,
                    'track_id': e.location,
                    'status': e.status,
                    'rejection_reason': e.rejection_reason or '',
                    'rejection_description': e.rejection_description or '',
                }
                for e in events
            ]
        )
        df.to_csv(filepath, index=False)

    def export_rejected_wagons(self, events: list[WagonJourneyEvent], filepath: str) -> None:
        """Export rejected wagons to CSV."""
        rejected = [e for e in events if e.event_type == 'REJECTED']

        def map_rejection_type(reason: str) -> str:
            if not reason:
                return 'UNKNOWN'
            reason_upper = reason.upper()
            if 'LOADED' in reason_upper:
                return 'WAGON_LOADED'
            if 'NO_RETROFIT_NEEDED' in reason_upper or 'NO RETROFIT' in reason_upper:
                return 'NO_RETROFIT_NEEDED'
            if 'CAPACITY' in reason_upper or 'FULL' in reason_upper:
                return 'TRACK_FULL'
            return 'TRACK_FULL'

        df = pd.DataFrame(
            [
                {
                    'timestamp': e.timestamp,
                    'datetime': self._to_datetime(e.timestamp),
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

    def export_locomotive_movements(self, events: list[LocomotiveMovementEvent], filepath: str) -> None:
        """Export locomotive movements to CSV."""
        df = pd.DataFrame(
            [
                {
                    'timestamp': e.timestamp,
                    'datetime': self._to_datetime(e.timestamp),
                    'locomotive_id': e.locomotive_id,
                    'event': e.event_type,
                    'from_location': e.from_location or '',
                    'to_location': e.to_location or '',
                    'purpose': e.purpose or '',
                }
                for e in events
            ]
        )
        df.to_csv(filepath, index=False)

    def export_track_capacity(self, resource_events: list[ResourceStateChangeEvent], filepath: str) -> None:
        """Export track capacity changes."""
        track_events = [e for e in resource_events if e.resource_type == 'track']
        df = pd.DataFrame(
            [
                {
                    'timestamp': e.timestamp,
                    'datetime': self._to_datetime(e.timestamp),
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

    def _get_or_init_loco_times(self, loco_times: dict, loco_id: str) -> None:
        """Initialize locomotive times if not exists."""
        if loco_id not in loco_times:
            loco_times[loco_id] = {'moving': 0.0, 'parking': 0.0, 'coupling': 0.0, 'decoupling': 0.0, 'idle': 0.0}

    def _map_event_to_state(self, event_type: str, loco_times: dict) -> str:
        """Map event type to state."""
        event_lower = event_type.lower()
        if event_lower in loco_times:
            return event_lower
        if event_lower == 'allocated':
            return 'coupling'
        return 'parking'

    def export_locomotive_summary(
        self,
        locomotive_events: list[LocomotiveMovementEvent],
        filepath: str,
    ) -> None:
        """Export per-locomotive summary statistics."""
        loco_times: dict[str, dict[str, float]] = {}
        loco_state: dict[str, tuple[float, str]] = {}

        for event in sorted(locomotive_events, key=lambda e: e.timestamp):
            loco_id = event.locomotive_id

            self._get_or_init_loco_times(loco_times, loco_id)
            if loco_id not in loco_state:
                loco_state[loco_id] = (0.0, 'parking')

            last_time, last_state = loco_state[loco_id]
            if last_time > 0:
                loco_times[loco_id][last_state] += event.timestamp - last_time

            new_state = self._map_event_to_state(event.event_type, loco_times[loco_id])
            loco_state[loco_id] = (event.timestamp, new_state)

        if locomotive_events:
            sim_end = max(e.timestamp for e in locomotive_events)
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

    def _init_loco_breakdown(self) -> dict[str, float]:
        """Initialize locomotive breakdown dict."""
        return {
            'moving_time': 0.0,
            'coupling_time_screw': 0.0,
            'coupling_time_automatic': 0.0,
            'decoupling_time_screw': 0.0,
            'decoupling_time_automatic': 0.0,
        }

    def _update_coupling_time(self, breakdown: dict, event: Any) -> None:
        """Update coupling time in breakdown."""
        if event.coupler_type.upper() == 'SCREW':
            breakdown['coupling_time_screw'] += event.duration
        else:
            breakdown['coupling_time_automatic'] += event.duration

    def _update_decoupling_time(self, breakdown: dict, event: Any) -> None:
        """Update decoupling time in breakdown."""
        if event.coupler_type.upper() == 'SCREW':
            breakdown['decoupling_time_screw'] += event.duration
        else:
            breakdown['decoupling_time_automatic'] += event.duration

    def export_locomotive_time_breakdown(
        self, locomotive_events: list[LocomotiveMovementEvent], coupling_events: list[Any], filepath: str
    ) -> None:
        """Export detailed per-locomotive time breakdown with coupling details."""
        loco_breakdown: dict[str, dict[str, float]] = {}

        # Calculate moving time per locomotive
        for loco_id in {e.locomotive_id for e in locomotive_events}:
            loco_events = sorted(
                [e for e in locomotive_events if e.locomotive_id == loco_id], key=lambda x: x.timestamp
            )

            moving_time = 0.0
            for i in range(len(loco_events) - 1):
                if loco_events[i].event_type == 'MOVING':
                    duration = loco_events[i + 1].timestamp - loco_events[i].timestamp
                    moving_time += duration

            loco_breakdown[loco_id] = self._init_loco_breakdown()
            loco_breakdown[loco_id]['moving_time'] = moving_time

        # Calculate coupling/decoupling time per locomotive and coupler type
        for event in coupling_events:
            if isinstance(event, CouplingEvent) and event.duration:
                loco_id = event.locomotive_id
                if loco_id not in loco_breakdown:
                    loco_breakdown[loco_id] = self._init_loco_breakdown()

                if 'COUPLING' in event.event_type and 'DECOUPLING' not in event.event_type:
                    self._update_coupling_time(loco_breakdown[loco_id], event)
                elif 'DECOUPLING' in event.event_type:
                    self._update_decoupling_time(loco_breakdown[loco_id], event)

        # Calculate idle time and export
        output_data = []
        for loco_id, times in sorted(loco_breakdown.items()):
            output_data.append(
                {
                    'locomotive_id': loco_id,
                    'moving_time_min': times['moving_time'],
                    'coupling_time_screw_min': times['coupling_time_screw'],
                    'coupling_time_automatic_min': times['coupling_time_automatic'],
                    'decoupling_time_screw_min': times['decoupling_time_screw'],
                    'decoupling_time_automatic_min': times['decoupling_time_automatic'],
                    'total_coupling_time_min': times['coupling_time_screw'] + times['coupling_time_automatic'],
                    'total_decoupling_time_min': times['decoupling_time_screw'] + times['decoupling_time_automatic'],
                }
            )

        pd.DataFrame(output_data).to_csv(filepath, index=False)

    def _create_movement_event_dict(self, e: LocomotiveMovementEvent) -> dict:
        """Create movement event dictionary."""
        return {
            'timestamp': e.timestamp,
            'locomotive_id': e.locomotive_id,
            'event_type': e.event_type,
            'location': e.to_location or e.from_location or '',
            'from_location': e.from_location or '',
            'to_location': e.to_location or '',
            'purpose': e.purpose or '',
            'coupler_type': '',
            'wagon_count': 0,
            'duration_min': None,
        }

    def _create_coupling_event_dict(self, e: Any) -> dict:
        """Create coupling event dictionary."""
        event_type = 'SHUNTING_PREP' if e.event_type == 'SHUNTING_PREPARATION' else e.event_type
        return {
            'timestamp': e.timestamp,
            'locomotive_id': e.locomotive_id,
            'event_type': event_type,
            'location': e.location,
            'from_location': '',
            'to_location': '',
            'purpose': '',
            'coupler_type': e.coupler_type,
            'wagon_count': e.wagon_count or 0,
            'duration_min': e.duration or 0.0,
        }

    def export_locomotive_journey(
        self, locomotive_events: list[LocomotiveMovementEvent], coupling_events: list[Any], filepath: str
    ) -> None:
        """Export detailed locomotive journey with all activities."""
        # Combine all events
        all_events = []

        # Add movement events
        for e in locomotive_events:
            all_events.append(self._create_movement_event_dict(e))

        # Add coupling events
        for e in coupling_events:
            if isinstance(e, CouplingEvent):
                all_events.append(self._create_coupling_event_dict(e))

        # Sort by timestamp and locomotive_id
        all_events.sort(key=lambda x: (x['locomotive_id'], x['timestamp']))

        # Calculate duration for events without explicit duration
        for i in range(len(all_events) - 1):
            if all_events[i]['duration_min'] is None:
                # Same locomotive, calculate time to next event
                if all_events[i]['locomotive_id'] == all_events[i + 1]['locomotive_id']:
                    all_events[i]['duration_min'] = all_events[i + 1]['timestamp'] - all_events[i]['timestamp']
                else:
                    all_events[i]['duration_min'] = 0.0

        # Last event has no duration
        if all_events and all_events[-1]['duration_min'] is None:
            all_events[-1]['duration_min'] = 0.0

        # Convert to DataFrame and add datetime
        df = pd.DataFrame(all_events)
        if not df.empty:
            df['datetime'] = df['timestamp'].apply(self._to_datetime)
            df = df[
                [
                    'timestamp',
                    'datetime',
                    'locomotive_id',
                    'event_type',
                    'location',
                    'from_location',
                    'to_location',
                    'purpose',
                    'coupler_type',
                    'wagon_count',
                    'duration_min',
                ]
            ]

        df.to_csv(filepath, index=False)

    def export_locomotive_utilization(self, resource_events: list[ResourceStateChangeEvent], filepath: str) -> None:
        """Export locomotive utilization changes."""
        loco_events = [e for e in resource_events if e.resource_type == 'locomotive']

        if not loco_events:
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
                        'datetime': self._to_datetime(e.timestamp),
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

    def export_workshop_utilization(self, resource_events: list[ResourceStateChangeEvent], filepath: str) -> None:
        """Export workshop bay utilization changes."""
        workshop_events = [e for e in resource_events if e.resource_type == 'workshop']

        if not workshop_events:
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
                        'datetime': self._to_datetime(e.timestamp),
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

    def export_events_csv(
        self,
        wagon_events: list[WagonJourneyEvent],
        locomotive_events: list[LocomotiveMovementEvent],
        batch_events: list[BatchFormed | BatchTransportStarted | BatchArrivedAtDestination],
        filepath: str,
    ) -> None:
        """Export all events in chronological order."""
        all_events = []

        for e in wagon_events:
            all_events.append(
                {
                    'timestamp': e.timestamp,
                    'datetime': self._to_datetime(e.timestamp),
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

        for e in locomotive_events:
            all_events.append(
                {
                    'timestamp': e.timestamp,
                    'datetime': self._to_datetime(e.timestamp),
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

        for e in batch_events:
            event_type = e.__class__.__name__
            details_dict = {
                'destination': e.destination,
                'wagon_count': e.wagon_count if hasattr(e, 'wagon_count') else len(e.wagon_ids),
                'locomotive_id': e.locomotive_id if hasattr(e, 'locomotive_id') else '',
            }
            if hasattr(e, 'wagon_ids'):
                details_dict['wagon_ids'] = ','.join(e.wagon_ids)

            all_events.append(
                {
                    'timestamp': e.timestamp,
                    'datetime': self._to_datetime(e.timestamp),
                    'event_type': event_type,
                    'resource_type': 'batch',
                    'resource_id': e.batch_id,
                    'details': json.dumps(details_dict),
                }
            )

        all_events.sort(key=lambda x: x['timestamp'])
        pd.DataFrame(all_events).to_csv(filepath, index=False)

    def export_timeline(
        self,
        wagon_events: list[WagonJourneyEvent],
        resource_events: list[ResourceStateChangeEvent],
        filepath: str,
    ) -> None:
        """Export bottleneck analysis timeline."""
        all_timestamps = [e.timestamp for e in wagon_events + resource_events]
        if not all_timestamps:
            pd.DataFrame(columns=['timestamp', 'datetime']).to_csv(filepath, index=False)
            return

        tracks, workshops = self._discover_resources(wagon_events, resource_events)
        max_time = max(all_timestamps)
        timeline_data = []
        current_time = 0.0

        while current_time <= max_time:
            snapshot = self._build_timeline_snapshot(current_time, wagon_events, resource_events, (tracks, workshops))
            timeline_data.append(snapshot)
            current_time += 60.0

        pd.DataFrame(timeline_data).to_csv(filepath, index=False)

    def _discover_resources(
        self, wagon_events: list[WagonJourneyEvent], resource_events: list[ResourceStateChangeEvent]
    ) -> tuple[set[str], set[str]]:
        """Discover all tracks and workshops from events."""
        tracks = {
            e.location
            for e in wagon_events
            if e.location and e.location not in ['REJECTED'] and not e.location.startswith('parking')
        }
        workshops = {e.resource_id for e in resource_events if e.resource_type == 'workshop'}
        return tracks, workshops

    def _build_timeline_snapshot(
        self,
        current_time: float,
        wagon_events: list[WagonJourneyEvent],
        resource_events: list[ResourceStateChangeEvent],
        resources: tuple[set[str], set[str]],
    ) -> dict[str, float | int | str]:
        """Build timeline snapshot at given time."""
        tracks, workshops = resources
        wagon_locations = self._replay_wagon_locations(wagon_events, current_time)
        track_counts = self._count_wagons_per_track(wagon_locations, tracks)
        workshop_bays = self._get_workshop_state(resource_events, current_time, workshops)
        loco_busy = self._get_locomotive_state(resource_events, current_time)

        row: dict[str, float | int | str] = {
            'timestamp': current_time,
            'datetime': self._to_datetime(current_time),
        }
        for track in sorted(tracks):
            row[f'track_{track}'] = track_counts[track]
        for workshop in sorted(workshops):
            row[f'workshop_{workshop}_busy_bays'] = workshop_bays[workshop]
        row['locomotives_busy'] = loco_busy
        row['wagons_in_process'] = sum(track_counts.values()) + sum(workshop_bays.values())
        return row

    def _replay_wagon_locations(self, wagon_events: list[WagonJourneyEvent], current_time: float) -> dict[str, str]:
        """Replay wagon events to get locations at given time."""
        wagon_locations: dict[str, str] = {}
        for e in sorted(wagon_events, key=lambda x: x.timestamp):
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
        return wagon_locations

    def _count_wagons_per_track(self, wagon_locations: dict[str, str], tracks: set[str]) -> dict[str, int]:
        """Count wagons per track."""
        track_counts: dict[str, int] = dict.fromkeys(tracks, 0)
        for location in wagon_locations.values():
            if location in tracks:
                track_counts[location] += 1
        return track_counts

    def _get_workshop_state(
        self, resource_events: list[ResourceStateChangeEvent], current_time: float, workshops: set[str]
    ) -> dict[str, int]:
        """Get workshop busy bays at given time."""
        workshop_bays: dict[str, int] = dict.fromkeys(workshops, 0)
        for e in sorted([e for e in resource_events if e.resource_type == 'workshop'], key=lambda x: x.timestamp):
            if e.timestamp > current_time:
                break
            if e.resource_id in workshop_bays:
                workshop_bays[e.resource_id] = e.busy_bays_after if hasattr(e, 'busy_bays_after') else 0
        return workshop_bays

    def _get_locomotive_state(self, resource_events: list[ResourceStateChangeEvent], current_time: float) -> int:
        """Get busy locomotives at given time."""
        loco_busy = 0
        for e in sorted([e for e in resource_events if e.resource_type == 'locomotive'], key=lambda x: x.timestamp):
            if e.timestamp > current_time:
                break
            loco_busy = e.busy_count_after if hasattr(e, 'busy_count_after') else 0
        return loco_busy

    def export_workshop_metrics(self, wagon_events: list[WagonJourneyEvent], filepath: str) -> None:
        """Export workshop performance metrics."""
        workshop_stats = self._collect_workshop_stats(wagon_events)
        sim_duration = max((e.timestamp for e in wagon_events), default=1.0)
        output_data = self._build_workshop_metrics(workshop_stats, sim_duration)
        pd.DataFrame(output_data).to_csv(filepath, index=False)

    def _collect_workshop_stats(self, wagon_events: list[WagonJourneyEvent]) -> dict[str, dict[str, float]]:
        """Collect workshop statistics from wagon events."""
        workshop_stats: dict[str, dict[str, float]] = {}

        for e in wagon_events:
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

        return workshop_stats

    def _build_workshop_metrics(
        self, workshop_stats: dict[str, dict[str, float]], sim_duration: float
    ) -> list[dict[str, str | int | float]]:
        """Build workshop metrics output data."""
        output_data = []
        for workshop_id, stats in sorted(workshop_stats.items()):
            completed = int(stats['completed_retrofits'])
            total_retrofit_time = stats['total_retrofit_time']

            num_bays = 2
            total_available_time = sim_duration * num_bays
            total_waiting_time = total_available_time - total_retrofit_time

            utilization_pct = (total_retrofit_time / total_available_time * 100) if total_available_time > 0 else 0
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

        return output_data
