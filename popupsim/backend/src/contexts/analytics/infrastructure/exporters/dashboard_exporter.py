"""Dashboard data exporter for Streamlit frontend integration."""

# ruff: noqa: PLR0911, PLR0912, PLR0915, C901
import csv
import json
from pathlib import Path
from typing import Any


class DashboardExporter:
    """Export all data required for Streamlit dashboard."""

    # pylint: disable=too-many-locals, too-many-positional-arguments, too-many-arguments
    def export_all(
        self,
        analytics_context: Any,
        output_dir: Path,
        interval_seconds: float = 3600.0,
        yard_context: Any = None,
        popup_context: Any = None,
    ) -> dict[str, Path]:
        """Export all dashboard data files.

        Parameters
        ----------
        analytics_context : AnalyticsContext
            Analytics context with collected data.
        output_dir : Path
            Output directory for all files.
        interval_seconds : float
            Time granularity for time-series data (default: 1 hour).

        Returns
        -------
        dict[str, Path]
            Mapping of file type to generated file path.
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        exported_files = {}

        # 1. Summary metrics JSON
        metrics_path = output_dir / 'summary_metrics.json'
        self._export_summary_metrics(analytics_context, metrics_path, popup_context)
        exported_files['summary_metrics'] = metrics_path

        # 2. Events CSV (temporal event stream)
        events_path = output_dir / 'events.csv'
        self._export_events_csv(analytics_context, events_path)
        exported_files['events'] = events_path

        # 3. Process log (resource state changes)
        process_log_path = output_dir / 'process.log'
        self._export_process_log(analytics_context, process_log_path)
        exported_files['process_log'] = process_log_path

        # 4. Locomotive utilization CSV
        loco_path = output_dir / 'locomotive_utilization.csv'
        self._export_locomotive_utilization(analytics_context, loco_path)
        exported_files['locomotive_utilization'] = loco_path

        # 5. Workshop metrics CSV
        workshop_path = output_dir / 'workshop_metrics.csv'
        self._export_workshop_metrics(analytics_context, workshop_path, popup_context)
        exported_files['workshop_metrics'] = workshop_path

        # 6. Track capacity time-series CSV
        track_path = output_dir / 'track_capacity.csv'
        self._export_track_capacity(analytics_context, track_path)
        exported_files['track_capacity'] = track_path

        # 7. Timeline CSV (time-series metrics)
        timeline_path = output_dir / 'timeline.csv'
        self._export_timeline(analytics_context, timeline_path, interval_seconds)
        exported_files['timeline'] = timeline_path

        # 8. Rejected wagons CSV
        rejected_path = output_dir / 'rejected_wagons.csv'
        self._export_rejected_wagons(rejected_path, yard_context)
        exported_files['rejected_wagons'] = rejected_path

        # 9. Wagon locations CSV (current state)
        locations_path = output_dir / 'wagon_locations.csv'
        self._export_wagon_locations(analytics_context, locations_path)
        exported_files['wagon_locations'] = locations_path

        # 10. Wagon journey CSV (complete history)
        journey_path = output_dir / 'wagon_journey.csv'
        self._export_wagon_journey(analytics_context, journey_path)
        exported_files['wagon_journey'] = journey_path

        return exported_files

    def _export_summary_metrics(self, analytics_context: Any, output_path: Path, popup_context: Any = None) -> None:
        """Export summary metrics to JSON."""
        metrics = analytics_context.get_metrics()

        # Remove event_history from metrics as it's exported separately
        if 'event_history' in metrics:
            del metrics['event_history']

        # Use simulation time directly
        # TODO: This call is not nice here!
        metrics['simulation_duration_minutes'] = popup_context.infra.engine.current_time()
        popup_metrics = popup_context.get_metrics()
        metrics['workshop_utilization'] = popup_metrics.get('utilization_percentage', 0.0)

        # Convert to JSON-serializable format
        serializable_metrics = self._make_serializable(metrics)

        with output_path.open('w', encoding='utf-8') as f:
            json.dump(serializable_metrics, f, indent=2)

    def _export_events_csv(self, analytics_context: Any, output_path: Path) -> None:
        """Export event stream to CSV."""
        events = analytics_context.event_stream.collector.get_events()

        with output_path.open('w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'event_type', 'resource_type', 'resource_id', 'details'])

            for timestamp, event in events:
                event_type = event.__class__.__name__
                resource_type = self._extract_resource_type(event)
                resource_id = self._extract_resource_id(event)
                details = self._extract_event_details(event)

                writer.writerow([timestamp, event_type, resource_type, resource_id, details])

    def _export_process_log(self, analytics_context: Any, output_path: Path) -> None:
        """Export process state changes to log file."""
        events = analytics_context.event_stream.collector.get_events()

        with output_path.open('w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
            writer.writerow(['timestamp', 'process', 'resource_type', 'resource_id', 'state', 'details'])

            for timestamp, event in events:
                process = self._extract_process_name(event)
                resource_type = self._extract_resource_type(event)
                resource_id = self._extract_resource_id(event)
                state = self._extract_state(event)
                details = self._extract_event_details(event)

                writer.writerow([timestamp, process, resource_type, resource_id, state, details])

    def _export_locomotive_utilization(self, analytics_context: Any, output_path: Path) -> None:  # pylint: disable=too-many-branches, too-many-locals
        """Export locomotive utilization breakdown to CSV."""
        events = analytics_context.event_stream.collector.get_events()

        # Calculate per-locomotive metrics from events
        loco_times: dict[str, dict[str, float]] = {}
        loco_last_event = {}
        loco_movements: dict[str, list[()]] = {}

        for timestamp, event in events:
            event_type = event.__class__.__name__

            if event_type == 'LocomotiveAllocatedEvent':
                loco_id = getattr(event, 'locomotive_id', None)
                if loco_id:
                    loco_last_event[loco_id] = (timestamp, 'allocated')
                    if loco_id not in loco_times:
                        loco_times[loco_id] = {'parking': 0, 'moving': 0, 'coupling': 0, 'decoupling': 0}
                        loco_movements[loco_id] = []

            elif event_type == 'LocomotiveMovementStartedEvent':
                loco_id = getattr(event, 'locomotive_id', None)
                from_track = getattr(event, 'from_track', '')
                to_track = getattr(event, 'to_track', '')
                if loco_id and loco_id in loco_last_event:
                    last_time, _ = loco_last_event[loco_id]
                    # Estimate coupling time before movement (if picking up wagons)
                    if any(track in to_track for track in ['WS', 'retrofit', 'collection']):
                        loco_times[loco_id]['coupling'] += 0.5  # Estimate 0.5 min coupling
                    loco_times[loco_id]['parking'] += timestamp - last_time
                    loco_last_event[loco_id] = (timestamp, 'moving')
                    loco_movements[loco_id].append((from_track, to_track))

            elif event_type == 'LocomotiveMovementCompletedEvent':
                loco_id = getattr(event, 'locomotive_id', None)
                from_track = getattr(event, 'from_track', '')
                to_track = getattr(event, 'to_track', '')
                if loco_id and loco_id in loco_last_event:
                    last_time, _ = loco_last_event[loco_id]
                    loco_times[loco_id]['moving'] += timestamp - last_time
                    # Estimate decoupling time after movement (if dropping off wagons)
                    if any(track in from_track for track in ['WS', 'retrofit', 'parking', 'retrofitted']):
                        loco_times[loco_id]['decoupling'] += 0.5  # Estimate 0.5 min decoupling
                    loco_last_event[loco_id] = (timestamp, 'idle')

            elif event_type == 'LocomotiveReleasedEvent':
                loco_id = getattr(event, 'locomotive_id', None)
                if loco_id and loco_id in loco_last_event:
                    last_time, _ = loco_last_event[loco_id]
                    loco_times[loco_id]['parking'] += timestamp - last_time
                    loco_last_event[loco_id] = (timestamp, 'parking')

        with output_path.open('w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    'locomotive_id',
                    'parking_time',
                    'moving_time',
                    'coupling_time',
                    'decoupling_time',
                    'parking_percent',
                    'moving_percent',
                    'coupling_percent',
                    'decoupling_percent',
                ]
            )

            for loco_id, times in sorted(loco_times.items()):
                total_time = sum(times.values())
                if total_time > 0:
                    writer.writerow(
                        [
                            loco_id,
                            times['parking'],
                            times['moving'],
                            times['coupling'],
                            times['decoupling'],
                            (times['parking'] / total_time) * 100,
                            (times['moving'] / total_time) * 100,
                            (times['coupling'] / total_time) * 100,
                            (times['decoupling'] / total_time) * 100,
                        ]
                    )

    def _export_workshop_metrics(self, analytics_context: Any, output_path: Path, popup_context: Any = None) -> None:  # pylint: disable=too-many-branches, too-many-locals
        """Export workshop performance metrics to CSV."""
        # Use popup context metrics if available (correct utilization)
        if popup_context:
            popup_metrics = popup_context.get_metrics()
            per_workshop_util = popup_metrics.get('per_workshop_utilization', {})
        else:
            per_workshop_util = {}

        metrics = analytics_context.get_metrics()
        workshop_stats = metrics.get('workshop_statistics', {}).get('workshops', {})

        with output_path.open('w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    'workshop_id',
                    'completed_retrofits',
                    'total_retrofit_time',
                    'total_waiting_time',
                    'throughput_per_hour',
                    'utilization_percent',
                ]
            )

            for workshop_id, stats in workshop_stats.items():
                if isinstance(stats, dict):
                    # Use wagons_processed as completed count
                    completed = stats.get('wagons_processed', stats.get('completed_retrofits', 0))

                    # Use correct utilization from popup context if available
                    utilization_pct = per_workshop_util.get(workshop_id, stats.get('utilization_percent', 0))

                    # Calculate times from utilization and simulation duration
                    events = analytics_context.event_stream.collector.get_events()
                    if events:
                        sim_duration_min = max(ts for ts, _ in events)
                        # Total retrofit time = utilization% * duration * num_bays
                        # Estimate 2 bays per workshop (from scenario)
                        num_bays = 2
                        total_retrofit_time = (utilization_pct / 100) * sim_duration_min * num_bays
                        total_waiting_time = ((100 - utilization_pct) / 100) * sim_duration_min * num_bays

                        # Throughput = wagons per hour
                        throughput = (completed / (sim_duration_min / 60)) if sim_duration_min > 0 else 0
                    else:
                        total_retrofit_time = 0
                        total_waiting_time = 0
                        throughput = 0

                    writer.writerow(
                        [
                            workshop_id,
                            completed,
                            total_retrofit_time,
                            total_waiting_time,
                            throughput,
                            utilization_pct,
                        ]
                    )

    def _export_track_capacity(self, analytics_context: Any, output_path: Path) -> None:
        """Export track capacity from analytics context."""
        # Get track metrics from analytics context
        track_metrics = analytics_context.get_track_metrics()

        with output_path.open('w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    'track_id',
                    'max_capacity_m',
                    'current_occupancy_m',
                    'utilization_percent',
                    'state',
                ]
            )

            # Export all track capacity data
            for track_id, metrics in sorted(track_metrics.items()):
                writer.writerow(
                    [
                        track_id,
                        metrics['max_capacity'],
                        metrics['current_occupancy'],
                        metrics['utilization_percent'],
                        metrics['state'],
                    ]
                )

    def _export_timeline(self, analytics_context: Any, output_path: Path, interval_seconds: float) -> None:
        """Export time-series metrics to CSV."""
        time_series = analytics_context.get_all_time_series(interval_seconds)

        with output_path.open('w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'metric', 'value'])

            for metric_name, data_points in time_series.items():
                for timestamp, value in data_points:
                    writer.writerow([timestamp, metric_name, value])

    def _extract_resource_type(self, event: Any) -> str:  # pylint: disable=too-many-return-statements
        """Extract resource type from event."""
        if hasattr(event, 'wagon_id'):
            return 'wagon'
        if hasattr(event, 'train_id'):
            return 'train'
        if hasattr(event, 'workshop_id'):
            return 'workshop'
        if hasattr(event, 'locomotive_id'):
            return 'locomotive'
        if hasattr(event, 'track_id'):
            return 'track'
        if hasattr(event, 'rake_id'):
            return 'rake'
        return 'unknown'

    def _extract_resource_id(self, event: Any) -> str:
        """Extract resource ID from event."""
        for attr in [
            'wagon_id',
            'train_id',
            'workshop_id',
            'locomotive_id',
            'track_id',
            'rake_id',
        ]:
            if hasattr(event, attr):
                return str(getattr(event, attr))
        return 'unknown'

    def _extract_process_name(self, event: Any) -> str:  # pylint: disable=too-many-return-statements
        """Extract process name from event type."""
        event_name = event.__class__.__name__
        if 'Train' in event_name:
            return 'train_arrival'
        if 'Retrofit' in event_name:
            return 'retrofit'
        if 'Locomotive' in event_name:
            return 'shunting'
        if 'Workshop' in event_name:
            return 'workshop'
        if 'Track' in event_name:
            return 'track'
        if 'Wagon' in event_name:
            return 'wagon'
        return 'unknown'

    def _extract_state(self, event: Any) -> str:
        """Extract state from event."""
        event_name = event.__class__.__name__.lower()
        if 'start' in event_name:
            return 'started'
        if 'complete' in event_name or 'end' in event_name:
            return 'completed'
        if 'arrive' in event_name:
            return 'arrived'
        if 'depart' in event_name:
            return 'departed'
        if 'reject' in event_name:
            return 'rejected'
        return 'in_progress'

    def _extract_event_details(self, event: Any) -> str:
        """Extract additional details from event as JSON string."""
        details = {}
        for attr in dir(event):
            if not attr.startswith('_') and attr not in [
                'event_timestamp',
                'wagon_id',
                'train_id',
                'workshop_id',
                'locomotive_id',
                'track_id',
                'rake_id',
            ]:
                value = getattr(event, attr, None)
                if value is not None and not callable(value):
                    details[attr] = str(value)
        return json.dumps(details) if details else ''

    def _make_serializable(self, obj: Any, seen: set[int] | None = None) -> Any:  # pylint: disable=too-many-return-statements
        """Convert object to JSON-serializable format."""
        if seen is None:
            seen = set()

        # Check for circular references
        obj_id = id(obj)
        if obj_id in seen:
            return '<circular reference>'

        # Basic types
        if isinstance(obj, (int, float, str, bool)) or obj is None:
            return obj

        # Skip known non-serializable types
        type_name = type(obj).__name__
        if any(
            skip in type_name.lower()
            for skip in [
                'simpy',
                'environment',
                'timeout',
                'process',
                'event',
                'bound',
                'function',
                'method',
                'iterator',
                'generator',
            ]
        ):
            return f'<{type_name}>'

        seen.add(obj_id)

        try:
            if isinstance(obj, dict):
                return {k: self._make_serializable(v, seen) for k, v in obj.items()}
            if isinstance(obj, (list, tuple)):
                return [self._make_serializable(item, seen) for item in obj]
            if hasattr(obj, '__dict__'):
                return self._make_serializable(obj.__dict__, seen)
            return str(obj)
        finally:
            seen.discard(obj_id)

    def export_timeline(self, analytics_context: Any, output_path: Path, interval_seconds: float = 3600.0) -> None:
        """Export timeline data to CSV (public method for standalone use)."""
        self._export_timeline(analytics_context, output_path, interval_seconds)

    # ruff: noqa: ARG002
    def export_track_capacity(self, analytics_context: Any, output_path: Path, yard_context: Any = None) -> None:  # pylint: disable=unused-argument
        """Export track capacity data to CSV (public method for standalone use)."""
        self._export_track_capacity(analytics_context, output_path)

    def export_wagon_locations(self, analytics_context: Any, output_path: Path) -> None:
        """Export wagon locations to CSV (public method for standalone use)."""
        self._export_wagon_locations(analytics_context, output_path)

    def _export_wagon_journey(self, analytics_context: Any, output_path: Path) -> None:  # pylint: disable=too-many-locals, too-many-branches, too-many-statements
        """Export complete wagon journey history to CSV - simplified to key transitions only."""
        wagon_journey = []
        wagon_states: dict[str, dict[str, Any]] = {}  # Track last state per wagon

        events = analytics_context.event_stream.collector.get_events()

        for timestamp, event in events:
            event_type = type(event).__name__

            # Track only key wagon state transitions
            if 'TrainArrived' in event_type:
                train_id = getattr(event, 'train_id', None)
                wagons = getattr(event, 'wagons', [])
                for wagon in wagons:
                    wagon_id = getattr(wagon, 'id', None)
                    arrival_track = getattr(event, 'arrival_track', 'collection')

                    if wagon_id:
                        wagon_journey.append(
                            {
                                'timestamp': timestamp,
                                'wagon_id': wagon_id,
                                'train_id': train_id,
                                'event': 'ARRIVED',
                                'location': arrival_track,
                                'status': 'ARRIVED',
                            }
                        )
                        wagon_states[wagon_id] = {'location': arrival_track, 'event': 'ARRIVED'}

            elif 'WagonMoved' in event_type:
                wagon_id = getattr(event, 'wagon_id', None)
                to_track = getattr(event, 'to_track', None)
                if wagon_id and to_track:
                    last_state = wagon_states.get(wagon_id, {})
                    last_location = last_state.get('location')

                    # Only track movements to key locations and avoid duplicates
                    if (
                        'retrofit' in to_track.lower()
                        and 'retrofitted' not in to_track.lower()
                        and last_location != to_track
                    ):
                        wagon_journey.append(
                            {
                                'timestamp': timestamp,
                                'wagon_id': wagon_id,
                                'train_id': '',
                                'event': 'ON_RETROFIT_TRACK',
                                'location': to_track,
                                'status': 'WAITING',
                            }
                        )
                        wagon_states[wagon_id] = {'location': to_track, 'event': 'ON_RETROFIT_TRACK'}

                    if 'retrofitted' == to_track.lower():
                        wagon_journey.append(
                            {
                                'timestamp': timestamp,
                                'wagon_id': wagon_id,
                                'train_id': '',
                                'event': 'ON_RETROFITTING_TRACK',
                                'location': to_track,
                                'status': 'WAITING',
                            }
                        )
                    # NOTE: Do NOT create AT_WORKSHOP entry from WagonMoved event
                    # Wagons should only show at workshop when retrofit actually starts

            elif 'RetrofitStarted' in event_type:
                wagon_id = getattr(event, 'wagon_id', None)
                workshop_id = getattr(event, 'workshop_id', None)
                if wagon_id:
                    last_state = wagon_states.get(wagon_id, {})
                    last_location = last_state.get('location')

                    # Add AT_WORKSHOP entry if wagon is moving from retrofit track to workshop
                    if last_location != workshop_id:
                        wagon_journey.append(
                            {
                                'timestamp': timestamp,
                                'wagon_id': wagon_id,
                                'train_id': '',
                                'event': 'AT_WORKSHOP',
                                'location': workshop_id or 'workshop',
                                'status': 'READY',
                            }
                        )

                    wagon_journey.append(
                        {
                            'timestamp': timestamp,
                            'wagon_id': wagon_id,
                            'train_id': '',
                            'event': 'RETROFIT_STARTED',
                            'location': workshop_id or 'workshop',
                            'status': 'RETROFITTING',
                        }
                    )
                    wagon_states[wagon_id] = {'location': workshop_id, 'event': 'RETROFIT_STARTED'}

            elif 'RetrofitCompleted' in event_type or 'WagonRetrofitCompleted' in event_type:
                wagon_id = getattr(event, 'wagon_id', None)
                workshop_id = getattr(event, 'workshop_id', None)
                if wagon_id:
                    wagon_journey.append(
                        {
                            'timestamp': timestamp,
                            'wagon_id': wagon_id,
                            'train_id': '',
                            'event': 'RETROFIT_COMPLETED',
                            'location': workshop_id or 'workshop',
                            'status': 'COMPLETED',
                        }
                    )
                    wagon_states[wagon_id] = {'location': workshop_id, 'event': 'RETROFIT_COMPLETED'}

            elif 'WagonParked' in event_type:
                wagon_id = getattr(event, 'wagon_id', None)
                parking_area = getattr(event, 'parking_area_id', 'parking')
                if wagon_id:
                    wagon_journey.append(
                        {
                            'timestamp': timestamp,
                            'wagon_id': wagon_id,
                            'train_id': '',
                            'event': 'PARKED',
                            'location': parking_area,
                            'status': 'PARKED',
                        }
                    )
                    wagon_states[wagon_id] = {'location': parking_area, 'event': 'PARKED'}

            elif 'WagonRejected' in event_type:
                wagon_id = getattr(event, 'wagon_id', None)
                if wagon_id:
                    wagon_journey.append(
                        {
                            'timestamp': timestamp,
                            'wagon_id': wagon_id,
                            'train_id': '',
                            'event': 'REJECTED',
                            'location': 'rejected',
                            'status': 'REJECTED',
                        }
                    )
                    wagon_states[wagon_id] = {'location': 'rejected', 'event': 'REJECTED'}

        # Post-process: Move rejected wagons to "rejected" track
        rejected_wagon_ids = set()
        rejected_file = output_path.parent / 'rejected_wagons.csv'
        if rejected_file.exists():
            with rejected_file.open('r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    rejected_wagon_ids.add(row['wagon_id'])

        # Update location for rejected wagons
        for entry in wagon_journey:
            if entry['wagon_id'] in rejected_wagon_ids and entry['event'] == 'ARRIVED':
                entry['location'] = 'rejected'
                entry['status'] = 'REJECTED'

        with output_path.open('w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'wagon_id', 'train_id', 'event', 'location', 'status'])

            for entry in sorted(wagon_journey, key=lambda x: (x['wagon_id'], x['timestamp'])):
                writer.writerow(
                    [
                        entry['timestamp'],
                        entry['wagon_id'],
                        entry['train_id'],
                        entry['event'],
                        entry['location'],
                        entry['status'],
                    ]
                )

    def _export_rejected_wagons(self, output_path: Path, yard_context: Any = None) -> None:
        """Export rejected wagons with reasons to CSV."""
        rejected_wagons = []

        # Get rejected wagons from yard context if available
        if yard_context and hasattr(yard_context, 'rejected_wagons'):
            rejected_wagons = yard_context.rejected_wagons

        with output_path.open('w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    'wagon_id',
                    'train_id',
                    'rejection_time',
                    'rejection_type',
                    'detailed_reason',
                    'collection_track_id',
                ]
            )

            for wagon in rejected_wagons:
                wagon_id = getattr(wagon, 'id', 'unknown')
                train_id = getattr(wagon, 'train_id', 'unknown')
                rejection_time = getattr(wagon, 'rejection_time', 0.0)
                detailed_reason = getattr(wagon, 'detailed_rejection_reason', 'Collection track full')
                collection_track_id = getattr(wagon, 'collection_track_id', '')

                # Determine rejection type from detailed reason
                rejection_reason = getattr(wagon, 'rejection_reason', 'UNKNOWN')
                if 'loaded' in detailed_reason.lower():
                    rejection_type = 'Loaded'
                elif "doesn't need retrofit" in detailed_reason.lower() or 'no retrofit' in detailed_reason.lower():
                    rejection_type = 'No Retrofit Needed'
                elif '_FULL' in rejection_reason or 'track full' in detailed_reason.lower():
                    # Extract track name from rejection reason (e.g., 'collection1_FULL' -> 'collection1 Full')
                    if '_FULL' in rejection_reason:
                        track_name = rejection_reason.replace('_FULL', '')
                        rejection_type = f'{track_name} Full'
                    else:
                        rejection_type = 'Collection Track Full'
                else:
                    rejection_type = 'Other'

                writer.writerow(
                    [
                        wagon_id,
                        train_id,
                        rejection_time,
                        rejection_type,
                        detailed_reason,
                        collection_track_id,
                    ]
                )

    def _export_wagon_locations(self, analytics_context: Any, output_path: Path) -> None:  # pylint: disable=too-many-statements, too-many-branches, too-many-locals
        """Export current wagon locations to CSV."""
        wagon_locations = []

        # Get all wagons from events to ensure we track everyone
        events = analytics_context.event_stream.collector.get_events()
        all_wagon_ids = set()
        wagon_status_map = {}
        wagon_track_map = {}
        wagon_train_map = {}

        # Build wagon state from events
        for _event in events:
            event = _event[1]  # event[0] is the timestamp
            event_type = type(event).__name__

            if 'TrainArrived' in event_type:
                train_id = getattr(event, 'train_id', None)
                arrival_track = getattr(event, 'arrival_track', 'collection')
                wagons = getattr(event, 'wagons', [])
                for wagon in wagons:
                    wagon_id = getattr(wagon, 'id', None)
                    if wagon_id:
                        all_wagon_ids.add(wagon_id)
                        wagon_train_map[wagon_id] = train_id
                        wagon_status_map[wagon_id] = 'ARRIVED'
                        wagon_track_map[wagon_id] = arrival_track

            elif 'WagonReadyForRetrofit' in event_type:
                wagon_id = getattr(event, 'wagon_id', None)
                track = getattr(event, 'track', 'retrofit')
                if wagon_id:
                    wagon_status_map[wagon_id] = 'WAITING_RETROFIT'
                    wagon_track_map[wagon_id] = track

            elif 'RetrofitStarted' in event_type:
                wagon_id = getattr(event, 'wagon_id', None)
                workshop_id = getattr(event, 'workshop_id', None)
                if wagon_id:
                    wagon_status_map[wagon_id] = 'RETROFITTING'
                    wagon_track_map[wagon_id] = workshop_id or 'workshop'

            elif 'RetrofitCompleted' in event_type or 'Retrofitted' in event_type:
                wagon_id = getattr(event, 'wagon_id', None)
                if wagon_id:
                    wagon_status_map[wagon_id] = 'COMPLETED'

            elif 'WagonParked' in event_type:
                wagon_id = getattr(event, 'wagon_id', None)
                parking_area = getattr(event, 'parking_area_id', None)
                if wagon_id:
                    wagon_status_map[wagon_id] = 'PARKED'
                    wagon_track_map[wagon_id] = parking_area or 'parking'

            elif 'WagonRejected' in event_type:
                wagon_id = getattr(event, 'wagon_id', None)
                collection_track = getattr(event, 'collection_track_id', None)
                if wagon_id:
                    wagon_status_map[wagon_id] = 'REJECTED'
                    if collection_track:
                        wagon_track_map[wagon_id] = 'REJECTED'  # collection_track

        # Export all wagons
        for wagon_id in all_wagon_ids:
            status = wagon_status_map.get(wagon_id, 'UNKNOWN')
            track = wagon_track_map.get(wagon_id, 'unknown')
            train_id = wagon_train_map.get(wagon_id, 'unknown')

            wagon_locations.append(
                {
                    'wagon_id': wagon_id,
                    'train_id': train_id,
                    'current_track': track,
                    'status': status,
                }
            )

        with output_path.open('w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['wagon_id', 'train_id', 'current_track', 'status'])

            for location in sorted(wagon_locations, key=lambda x: x['wagon_id']):
                writer.writerow(
                    [
                        location['wagon_id'],
                        location['train_id'],
                        location['current_track'],
                        location['status'],
                    ]
                )
