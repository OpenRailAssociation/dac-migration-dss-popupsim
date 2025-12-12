"""Utilization breakdown service for locomotives, wagons, and workshops."""

from collections import defaultdict
from dataclasses import dataclass
from typing import Any


@dataclass
class UtilizationBreakdown:
    """Utilization breakdown with time and percentage."""

    action_times: dict[str, float]  # Total time per action
    action_percentages: dict[str, float]  # Percentage per action
    total_time: float
    total_actions: int


class UtilizationBreakdownService:
    """Service for calculating detailed utilization breakdowns."""

    def __init__(self, events: list[tuple[float, Any]], total_duration: float) -> None:
        self.events = events
        self.total_duration = total_duration

    def get_locomotive_breakdown(self) -> UtilizationBreakdown:
        """Get locomotive utilization breakdown with time tracking."""
        action_times: dict[str, float] = defaultdict(float)
        action_starts: dict[str, float] = {}
        total_actions = 0

        for timestamp, event in self.events:
            event_type = type(event).__name__
            loco_id = getattr(event, 'locomotive_id', None)

            if not loco_id:
                continue

            if event_type == 'LocomotiveAllocatedEvent':
                action_starts[f'{loco_id}_moving'] = timestamp
                total_actions += 1
            elif event_type == 'LocomotiveReleasedEvent':
                start_time = action_starts.pop(f'{loco_id}_moving', timestamp)
                action_times['moving'] += timestamp - start_time
                action_starts[f'{loco_id}_parking'] = timestamp
                total_actions += 1
            elif event_type in ('CouplingStartedEvent', 'DecouplingStartedEvent'):
                action = 'coupling' if 'Coupling' in event_type else 'decoupling'
                action_starts[f'{loco_id}_{action}'] = timestamp
                total_actions += 1
            elif event_type in ('CouplingCompletedEvent', 'DecouplingCompletedEvent'):
                action = 'coupling' if 'Coupling' in event_type else 'decoupling'
                start_time = action_starts.pop(f'{loco_id}_{action}', timestamp)
                action_times[action] += timestamp - start_time

        # Calculate parking time as remaining time
        total_active_time = sum(action_times.values())
        action_times['parking'] = max(0, self.total_duration - total_active_time)

        # Calculate percentages
        action_percentages = {
            action: (time / self.total_duration * 100) if self.total_duration > 0 else 0
            for action, time in action_times.items()
        }

        return UtilizationBreakdown(
            action_times=dict(action_times),
            action_percentages=action_percentages,
            total_time=self.total_duration,
            total_actions=total_actions,
        )

    def get_wagon_breakdown(self) -> UtilizationBreakdown:
        """Get wagon utilization breakdown with time tracking."""
        action_times: dict[str, float] = defaultdict(float)
        action_starts: dict[str, float] = {}
        total_actions = 0

        for timestamp, event in self.events:
            event_type = type(event).__name__
            wagon_id = getattr(event, 'wagon_id', None)

            if not wagon_id:
                continue

            if event_type == 'WagonDistributedEvent':
                action_starts[f'{wagon_id}_on_track'] = timestamp
                total_actions += 1
            elif event_type == 'RetrofitStartedEvent':
                start_time = action_starts.pop(f'{wagon_id}_on_track', timestamp)
                action_times['waiting'] += timestamp - start_time
                action_starts[f'{wagon_id}_retrofitting'] = timestamp
                total_actions += 1
            elif event_type == 'RetrofitCompletedEvent':
                start_time = action_starts.pop(f'{wagon_id}_retrofitting', timestamp)
                action_times['retrofitting'] += timestamp - start_time
                action_starts[f'{wagon_id}_completed'] = timestamp
                total_actions += 1

        # Calculate percentages
        total_time = sum(action_times.values())
        action_percentages = {
            action: (time / total_time * 100) if total_time > 0 else 0 for action, time in action_times.items()
        }

        return UtilizationBreakdown(
            action_times=dict(action_times),
            action_percentages=action_percentages,
            total_time=total_time,
            total_actions=total_actions,
        )

    def get_workshop_breakdown(self) -> dict[str, UtilizationBreakdown]:
        """Get workshop utilization breakdown per workshop."""
        workshop_breakdowns = {}

        for workshop_id in self._get_workshop_ids():
            action_times: dict[str, float]= defaultdict(float)
            total_actions = 0

            for _event in self.events:
                event = _event[1]
                event_type = type(event).__name__
                event_workshop_id = getattr(event, 'workshop_id', None)

                if event_workshop_id != workshop_id:
                    continue

                # Track retrofit completion events (actual events used in simulation)
                if event_type in ('WagonRetrofitCompletedEvent', 'BatchRetrofittedEvent', 'WagonRetrofittedEvent'):
                    # Estimate working time from completion_time or use default retrofit duration
                    duration = getattr(event, 'duration', 15.0)  # Default 15 min per wagon
                    action_times['working'] += duration
                    total_actions += 1

            # Calculate waiting time as remaining time
            total_working_time = action_times['working']
            action_times['waiting'] = max(0, self.total_duration - total_working_time)

            # Calculate percentages
            action_percentages = {
                action: (time / self.total_duration * 100) if self.total_duration > 0 else 0
                for action, time in action_times.items()
            }

            workshop_breakdowns[workshop_id] = UtilizationBreakdown(
                action_times=dict(action_times),
                action_percentages=action_percentages,
                total_time=self.total_duration,
                total_actions=total_actions,
            )

        return workshop_breakdowns

    def _get_workshop_ids(self) -> set[str]:
        """Extract unique workshop IDs from events."""
        workshop_ids = set()
        for _, event in self.events:
            workshop_id = getattr(event, 'workshop_id', None)
            if workshop_id:
                workshop_ids.add(workshop_id)
        return workshop_ids
