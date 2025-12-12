"""Domain service for aggregating events into statistics."""
# ruff: noqa: C901, PLR0912, PLR0915

from collections import defaultdict
from typing import Any


class EventAggregator:
    """Aggregates domain events into statistical data for metrics calculation."""

    def __init__(self) -> None:
        self._stats: dict[str, Any] = {}
        self._initialize_stats()

    def aggregate_event(self, event: Any) -> None:  # pylint: disable=too-many-branches, too-many-statements
        """Aggregate a single domain event into statistics."""
        event_type = type(event).__name__

        # Train arrivals
        if event_type == 'TrainArrivedEvent':
            self._stats['train_arrivals'] += 1
            wagon_count = getattr(event, 'wagon_count', 0)
            self._stats['wagons_arrived'] += wagon_count
            timestamp = getattr(event, 'timestamp', 0.0)
            self._stats['arrivals_by_time'][timestamp] = wagon_count

        # Wagon state changes
        elif event_type == 'WagonRetrofittedEvent':
            self._stats['wagons_retrofitted'] += 1
        elif event_type == 'WagonRejectedEvent':
            self._stats['wagons_rejected'] += 1
        elif event_type == 'WagonParkedEvent':
            self._stats['wagons_in_parking'] += 1
        elif event_type == 'WagonRetrofitStartedEvent':
            self._stats['wagons_retrofitting'] += 1
        elif event_type == 'WagonMovedToRetrofitTrackEvent':
            self._stats['wagons_on_retrofit_track'] += 1
        elif event_type == 'WagonMovedToRetrofittedTrackEvent':
            self._stats['wagons_on_retrofitted_track'] += 1

        # Locomotive utilization
        elif event_type in [
            'LocomotiveParkingEvent',
            'LocomotiveMovingEvent',
            'LocomotiveCouplingEvent',
            'LocomotiveDecouplingEvent',
        ]:
            loco_id = getattr(event, 'locomotive_id', 'unknown')
            duration = getattr(event, 'duration', 0.0)
            loco_data = self._stats['locomotives'][loco_id]

            if event_type == 'LocomotiveParkingEvent':
                loco_data['parking_time'] += duration
            elif event_type == 'LocomotiveMovingEvent':
                loco_data['moving_time'] += duration
            elif event_type == 'LocomotiveCouplingEvent':
                loco_data['coupling_time'] += duration
            elif event_type == 'LocomotiveDecouplingEvent':
                loco_data['decoupling_time'] += duration

            loco_data['total_time'] += duration

        # Workshop metrics
        elif event_type == 'RetrofitCompletedEvent':
            workshop_id = getattr(event, 'workshop_id', 'unknown')
            self._stats['workshops'][workshop_id]['completed_retrofits'] += 1
        elif event_type == 'WorkshopWorkingEvent':
            workshop_id = getattr(event, 'workshop_id', 'unknown')
            duration = getattr(event, 'duration', 0.0)
            self._stats['workshops'][workshop_id]['working_time'] += duration
        elif event_type == 'WorkshopWaitingEvent':
            workshop_id = getattr(event, 'workshop_id', 'unknown')
            duration = getattr(event, 'duration', 0.0)
            self._stats['workshops'][workshop_id]['waiting_time'] += duration

        # Track capacity
        elif event_type == 'TrackCapacityChangedEvent':
            track_id = getattr(event, 'track_id', 'unknown')
            used = getattr(event, 'used_capacity', 0)
            total = getattr(event, 'total_capacity', 0)
            timestamp = getattr(event, 'timestamp', 0.0)

            self._stats['tracks'][track_id]['used_capacity'] = used
            self._stats['tracks'][track_id]['total_capacity'] = total

            # Track timeline
            self._stats['track_timelines'][track_id].append(
                {'timestamp': timestamp, 'used_capacity': used, 'total_capacity': total}
            )

        # Update current time
        if hasattr(event, 'timestamp'):
            self._stats['current_time'] = max(self._stats['current_time'], event.timestamp)

    def get_statistics(self) -> dict[str, Any]:
        """Get aggregated statistics."""
        # Calculate derived metrics
        for data in self._stats['workshops'].values():
            total_time = data['working_time'] + data['waiting_time']
            if total_time > 0:
                data['wagons_per_hour'] = data['completed_retrofits'] / (total_time / 3600.0)

        return dict(self._stats)

    def reset(self) -> None:
        """Reset all statistics."""
        self._initialize_stats()

    def _initialize_stats(self) -> None:
        """Initialize statisctics."""
        self._stats: dict[str, Any] = {
            'train_arrivals': 0,
            'wagons_arrived': 0,
            'wagons_retrofitted': 0,
            'wagons_rejected': 0,
            'wagons_in_parking': 0,
            'wagons_retrofitting': 0,
            'wagons_on_retrofit_track': 0,
            'wagons_on_retrofitted_track': 0,
            'arrivals_by_time': {},
            'locomotives': defaultdict(
                lambda: {
                    'parking_time': 0.0,
                    'moving_time': 0.0,
                    'coupling_time': 0.0,
                    'decoupling_time': 0.0,
                    'total_time': 0.0,
                }
            ),
            'workshops': defaultdict(
                lambda: {
                    'completed_retrofits': 0,
                    'working_time': 0.0,
                    'waiting_time': 0.0,
                    'wagons_per_hour': 0.0,
                }
            ),
            'tracks': defaultdict(lambda: {'used_capacity': 0, 'total_capacity': 0}),
            'track_timelines': defaultdict(list),
            'current_time': 0.0,
        }
