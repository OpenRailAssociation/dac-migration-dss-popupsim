"""State tracking service for real-time system state."""

from collections import defaultdict
from typing import Any


class StateTrackingService:
    """Tracks current system state from events."""

    def __init__(self) -> None:
        self.wagons_retrofitting: set[str] = set()
        self.wagons_on_retrofit_track: set[str] = set()
        self.wagons_on_retrofitted_track: set[str] = set()
        self.wagon_locations: dict[str, str] = {}
        self.workshop_states: dict[str, dict[str, Any]] = defaultdict(
            lambda: {'working': 0, 'waiting': 0, 'total_bays': 0, 'occupied_bays': 0}
        )
        self.locomotive_actions: dict[str, str] = {}
        self.track_occupancy: dict[str, set[str]] = defaultdict(set)
        self.retrofit_start_times: dict[str, float] = {}
        self.workshop_idle_start: dict[str, float] = {}
        self.wagon_lengths: dict[str, float] = {}
        self.track_capacities: dict[str, float] = {}

    def process_event(self, event: Any) -> None:
        """Update state based on event."""
        event_type = type(event).__name__
        timestamp = getattr(event, 'timestamp', 0.0)

        if event_type == 'RetrofitStartedEvent':
            wagon_id = getattr(event, 'wagon_id', None)
            workshop_id = getattr(event, 'workshop_id', None)
            if wagon_id:
                self.wagons_retrofitting.add(wagon_id)
                self.retrofit_start_times[wagon_id] = timestamp
            if workshop_id:
                self.workshop_states[workshop_id]['working'] += 1
                self.workshop_states[workshop_id]['occupied_bays'] += 1
                if workshop_id in self.workshop_idle_start:
                    del self.workshop_idle_start[workshop_id]

        elif event_type == 'RetrofitCompletedEvent':
            wagon_id = getattr(event, 'wagon_id', None)
            workshop_id = getattr(event, 'workshop_id', None)
            if wagon_id:
                self.wagons_retrofitting.discard(wagon_id)
                if wagon_id in self.retrofit_start_times:
                    del self.retrofit_start_times[wagon_id]
            if workshop_id:
                if self.workshop_states[workshop_id]['working'] > 0:
                    self.workshop_states[workshop_id]['working'] -= 1
                if self.workshop_states[workshop_id]['occupied_bays'] > 0:
                    self.workshop_states[workshop_id]['occupied_bays'] -= 1
                if self.workshop_states[workshop_id]['occupied_bays'] == 0:
                    self.workshop_idle_start[workshop_id] = timestamp

        elif event_type == 'WagonLocationChangedEvent':
            wagon_id = getattr(event, 'wagon_id', None)
            from_location = getattr(event, 'from_location', None)
            to_location = getattr(event, 'to_location', None)
            if wagon_id and to_location:
                self.wagon_locations[wagon_id] = to_location
                if from_location:
                    self.track_occupancy[from_location].discard(wagon_id)
                self.track_occupancy[to_location].add(wagon_id)
                if 'retrofit_track' in to_location.lower():
                    self.wagons_on_retrofit_track.add(wagon_id)
                elif 'retrofitted_track' in to_location.lower():
                    self.wagons_on_retrofitted_track.add(wagon_id)
                    self.wagons_on_retrofit_track.discard(wagon_id)

        elif event_type == 'WagonDistributedEvent':
            wagon_id = getattr(event, 'wagon_id', None)
            track_id = getattr(event, 'track_id', None)
            if wagon_id:
                self.wagons_on_retrofit_track.add(wagon_id)
                wagon_length = getattr(event, 'wagon_length', None)
                if wagon_length is not None:
                    self.wagon_lengths[wagon_id] = wagon_length
                if track_id:
                    self.wagon_locations[wagon_id] = track_id
                    self.track_occupancy[track_id].add(wagon_id)

        elif event_type == 'WagonParkedEvent':
            wagon_id = getattr(event, 'wagon_id', None)
            track_id = getattr(event, 'track_id', None)
            if wagon_id:
                self.wagons_on_retrofitted_track.add(wagon_id)
                self.wagons_on_retrofit_track.discard(wagon_id)
                wagon_length = getattr(event, 'wagon_length', None)
                if wagon_length is not None:
                    self.wagon_lengths[wagon_id] = wagon_length
                if track_id:
                    self.wagon_locations[wagon_id] = track_id
                    self.track_occupancy[track_id].add(wagon_id)

        elif event_type in ('LocomotiveAllocatedEvent', 'ResourceAllocatedEvent'):
            loco_id = getattr(event, 'locomotive_id', None) or getattr(event, 'resource_id', None)
            resource_type = getattr(event, 'resource_type', 'locomotive')
            if loco_id and resource_type == 'locomotive':
                self.locomotive_actions[loco_id] = 'moving'

        elif event_type in ('LocomotiveReleasedEvent', 'ResourceReleasedEvent'):
            loco_id = getattr(event, 'locomotive_id', None) or getattr(event, 'resource_id', None)
            resource_type = getattr(event, 'resource_type', 'locomotive')
            if loco_id and resource_type == 'locomotive':
                self.locomotive_actions[loco_id] = 'parking'

        elif event_type == 'LocomotiveLocationChangedEvent':
            loco_id = getattr(event, 'loco_id', None)
            status = getattr(event, 'status', 'idle')
            if loco_id:
                self.locomotive_actions[loco_id] = status

        elif event_type == 'WorkshopStationOccupiedEvent':
            workshop_id = getattr(event, 'workshop_id', None)
            if workshop_id:
                self.workshop_states[workshop_id]['occupied_bays'] += 1
                if workshop_id in self.workshop_idle_start:
                    del self.workshop_idle_start[workshop_id]

        elif event_type == 'WorkshopStationIdleEvent':
            workshop_id = getattr(event, 'workshop_id', None)
            if workshop_id:
                if self.workshop_states[workshop_id]['occupied_bays'] > 0:
                    self.workshop_states[workshop_id]['occupied_bays'] -= 1
                if self.workshop_states[workshop_id]['occupied_bays'] == 0:
                    self.workshop_idle_start[workshop_id] = timestamp

    def get_current_state(self) -> dict[str, Any]:
        """Get current system state snapshot."""
        loco_breakdown = defaultdict(int)
        for action in self.locomotive_actions.values():
            loco_breakdown[action] += 1

        track_states = {}
        for track_id, wagons in self.track_occupancy.items():
            track_states[track_id] = {
                'current_occupancy': len(wagons),
                'wagon_ids': list(wagons),
            }

        return {
            'wagons_retrofitting': len(self.wagons_retrofitting),
            'wagons_on_retrofit_track': len(self.wagons_on_retrofit_track),
            'wagons_on_retrofitted_track': len(self.wagons_on_retrofitted_track),
            'wagon_locations': dict(self.wagon_locations),
            'workshop_states': dict(self.workshop_states),
            'locomotive_action_breakdown': dict(loco_breakdown),
            'total_active_locomotives': len(self.locomotive_actions),
            'track_occupancy': track_states,
            'active_retrofits': list(self.wagons_retrofitting),
        }

    def set_track_capacity(self, track_id: str, capacity: float) -> None:
        """Set maximum capacity for a track.

        Parameters
        ----------
        track_id : str
            Track identifier.
        capacity : float
            Maximum capacity in length units.
        """
        self.track_capacities[track_id] = capacity

    def get_track_metrics(self) -> dict[str, Any]:
        """Get track capacity metrics.

        Returns
        -------
        dict[str, Any]
            Track metrics with utilization and state.
        """
        from .track_capacity_calculator import TrackCapacityCalculator

        calculator = TrackCapacityCalculator(self.track_capacities, self.track_occupancy, self.wagon_lengths)
        return calculator.calculate()

    def clear(self) -> None:
        """Clear all state."""
        self.wagons_retrofitting.clear()
        self.wagons_on_retrofit_track.clear()
        self.wagons_on_retrofitted_track.clear()
        self.wagon_locations.clear()
        self.workshop_states.clear()
        self.locomotive_actions.clear()
        self.track_occupancy.clear()
        self.retrofit_start_times.clear()
        self.workshop_idle_start.clear()
        self.wagon_lengths.clear()
        self.track_capacities.clear()
