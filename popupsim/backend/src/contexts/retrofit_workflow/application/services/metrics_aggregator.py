"""Metrics aggregator for simulation events."""

from contexts.retrofit_workflow.domain.events import CouplingEvent
from contexts.retrofit_workflow.domain.events import LocomotiveMovementEvent
from contexts.retrofit_workflow.domain.events import ResourceStateChangeEvent
from contexts.retrofit_workflow.domain.events import WagonJourneyEvent
from contexts.retrofit_workflow.domain.events.batch_events import BatchArrivedAtDestination
from contexts.retrofit_workflow.domain.events.batch_events import BatchFormed
from contexts.retrofit_workflow.domain.events.batch_events import BatchTransportStarted


class MetricsAggregator:
    """Aggregates metrics from simulation events (all methods public for flexible composition)."""

    def get_event_counts(
        self,
        wagon_events: list[WagonJourneyEvent],
        locomotive_events: list[LocomotiveMovementEvent],
        batch_events: list[BatchFormed | BatchTransportStarted | BatchArrivedAtDestination],
    ) -> dict[str, int | dict[str, int]]:
        """Get event counts."""
        event_type_counts: dict[str, int] = {}
        for e in wagon_events + locomotive_events + batch_events:
            event_name = e.__class__.__name__
            event_type_counts[event_name] = event_type_counts.get(event_name, 0) + 1

        return {
            'total_events': len(wagon_events) + len(locomotive_events) + len(batch_events),
            'event_counts': event_type_counts,
        }

    def get_wagon_metrics(self, wagon_events: list[WagonJourneyEvent]) -> dict[str, int | float]:  # pylint: disable=too-many-locals
        """Get wagon-related metrics.

        Note: Multiple local variables needed for comprehensive wagon metrics calculation.
        """
        arrived = [e for e in wagon_events if e.event_type == 'ARRIVED']
        parked = [e for e in wagon_events if e.event_type == 'PARKED']
        rejected = [e for e in wagon_events if e.event_type == 'REJECTED']
        retrofitted = [e for e in wagon_events if e.event_type == 'RETROFIT_COMPLETED']
        distributed = [e for e in wagon_events if e.event_type == 'DISTRIBUTED']

        # Total wagons = all unique wagons that entered simulation (arrived OR rejected)
        unique_arrived = {e.wagon_id for e in arrived}
        unique_rejected = {e.wagon_id for e in rejected}
        total_wagons = len(unique_arrived | unique_rejected)  # Union of both sets

        wagons_arrived = len(unique_arrived)
        wagons_parked = len(parked)
        wagons_rejected = len(rejected)

        # Count rejections by reason (match actual rejection_reason values from code)
        rejected_no_retrofit = len([e for e in rejected if e.rejection_reason and 'No Retrofit' in e.rejection_reason])
        rejected_loaded = len([e for e in rejected if e.rejection_reason and 'Loaded' in e.rejection_reason])
        rejected_track_full = len([e for e in rejected if e.rejection_reason and 'TRACK' in e.rejection_reason.upper()])
        rejected_other = wagons_rejected - rejected_no_retrofit - rejected_loaded - rejected_track_full

        # Wagons eligible for retrofit = total - no_retrofit_needed
        wagons_eligible = total_wagons - rejected_no_retrofit

        # Wagons that could be processed = eligible - loaded
        wagons_processable = wagons_eligible - rejected_loaded

        # Wagons in process = arrived but not yet parked
        wagons_in_process = wagons_arrived - wagons_parked

        all_timestamps = [e.timestamp for e in wagon_events]
        sim_duration = max(all_timestamps) if all_timestamps else 1

        return {
            'trains_arrived': len({e.train_id for e in arrived if e.train_id}),
            'total_wagons': total_wagons,
            'wagons_eligible': wagons_eligible,
            'wagons_processable': wagons_processable,
            'wagons_arrived': wagons_arrived,
            'wagons_parked': wagons_parked,
            'retrofits_completed': len(retrofitted),
            'wagons_rejected': wagons_rejected,
            'rejected_no_retrofit': rejected_no_retrofit,
            'rejected_loaded': rejected_loaded,
            'rejected_track_full': rejected_track_full,
            'rejected_other': rejected_other,
            'wagons_distributed': len(distributed),
            'wagons_in_process': wagons_in_process,
            'completion_rate': wagons_parked / wagons_processable if wagons_processable > 0 else 0,
            'throughput_rate_per_hour': (wagons_parked / sim_duration * 60) if sim_duration > 0 else 0,
        }

    def get_workshop_metrics(  # pylint: disable=too-many-locals
        self, wagon_events: list[WagonJourneyEvent], resource_events: list[ResourceStateChangeEvent]
    ) -> dict[str, dict[str, int | float]]:
        """Get workshop metrics.

        Note: Multiple local variables needed for workshop statistics calculation.
        """
        workshop_stats: dict[str, dict[str, int]] = {}
        for e in wagon_events:
            if e.event_type == 'RETROFIT_STARTED' and e.location:
                ws_id = e.location
                if ws_id not in workshop_stats:
                    workshop_stats[ws_id] = {'wagons_processed': 0, 'retrofits_started': 0}
                workshop_stats[ws_id]['retrofits_started'] += 1
                # Count as processed when retrofit starts (completed will be at different location)
                workshop_stats[ws_id]['wagons_processed'] += 1

        all_timestamps = [e.timestamp for e in wagon_events]
        sim_duration = max(all_timestamps) if all_timestamps else 1

        workshop_util = self.calculate_workshop_utilization(resource_events, workshop_stats, sim_duration)

        return {
            'workshop_statistics': {
                'total_workshops': len(workshop_stats),
                'workshops': workshop_stats,
                'total_wagons_processed': sum(ws['wagons_processed'] for ws in workshop_stats.values()),
            },
            'workshop_utilization': workshop_util,
        }

    def get_locomotive_metrics(
        self, locomotive_events: list[LocomotiveMovementEvent], resource_events: list[ResourceStateChangeEvent]
    ) -> dict[str, dict[str, int | float]]:
        """Get locomotive metrics."""
        loco_allocated = len([e for e in locomotive_events if e.event_type == 'ALLOCATED'])
        loco_released = len([e for e in locomotive_events if e.event_type == 'RELEASED'])
        loco_movements = len([e for e in locomotive_events if e.event_type == 'MOVING'])

        loco_util_pct = 0.0
        loco_resource_events = [e for e in resource_events if e.resource_type == 'locomotive']
        if loco_resource_events:
            last_event = max(loco_resource_events, key=lambda e: e.timestamp)
            if (
                hasattr(last_event, 'busy_count_after')
                and hasattr(last_event, 'total_count')
                and last_event.total_count
                and last_event.total_count > 0
            ):
                loco_util_pct = (last_event.busy_count_after / last_event.total_count) * 100

        return {
            'locomotive_statistics': {
                'utilization_percent': loco_util_pct,
                'allocations': loco_allocated,
                'releases': loco_released,
                'movements': loco_movements,
                'total_operations': loco_allocated + loco_released + loco_movements,
            }
        }

    def get_static_metrics(self) -> dict[str, dict[str, int | float] | int]:
        """Get static/placeholder metrics."""
        return {
            'wagons_classified': 0,
            'shunting_statistics': {
                'total_operations': 0,
                'successful_operations': 0,
                'success_rate': 0.0,
            },
            'yard_statistics': {
                'wagons_classified': 0,
                'wagons_distributed': 0,
                'wagons_parked': 0,
            },
            'capacity_statistics': {
                'total_wagon_movements': 0,
                'active_operations': 0,
                'events_per_hour': 0,
            },
            'current_state': {},
        }

    def get_sim_duration(
        self,
        wagon_events: list[WagonJourneyEvent],
        locomotive_events: list[LocomotiveMovementEvent],
        resource_events: list[ResourceStateChangeEvent],
    ) -> float:
        """Get simulation duration."""
        all_timestamps = [e.timestamp for e in wagon_events + locomotive_events + resource_events]
        return max(all_timestamps) if all_timestamps else 0

    def calculate_workshop_utilization(  # pylint: disable=too-many-locals
        self,
        resource_events: list[ResourceStateChangeEvent],
        workshop_stats: dict[str, dict[str, int]],
        sim_duration: float,
    ) -> float:
        """Calculate average workshop utilization.

        Note: Multiple local variables needed for time-based utilization calculation.
        """
        if not workshop_stats:
            return 0.0

        total_util = 0.0
        for ws_id in workshop_stats:
            ws_events = [e for e in resource_events if e.resource_type == 'workshop' and e.resource_id == ws_id]
            if not ws_events:
                continue

            total_time = 0.0
            busy_time = 0.0
            prev_time = 0.0
            prev_busy = 0.0
            prev_total = 0.0

            for e in sorted(ws_events, key=lambda x: x.timestamp):
                if prev_time > 0 and prev_total > 0:
                    duration = e.timestamp - prev_time
                    total_time += duration
                    busy_time += duration * (prev_busy / prev_total)

                prev_time = e.timestamp
                prev_busy = float(e.busy_bays_after if hasattr(e, 'busy_bays_after') else 0)
                prev_total = float(e.total_bays if hasattr(e, 'total_bays') else 0)

            if 0 < prev_time < sim_duration and prev_total > 0:
                duration = sim_duration - prev_time
                total_time += duration
                busy_time += duration * (prev_busy / prev_total)

            if total_time > 0:
                total_util += (busy_time / total_time) * 100

        return total_util / len(workshop_stats)

    def get_locomotive_time_breakdown(  # pylint: disable=too-many-locals
        self,
        locomotive_events: list[LocomotiveMovementEvent],
        coupling_events: list[CouplingEvent],
        sim_duration: float,
    ) -> dict[str, dict[str, float]]:
        """Calculate per-locomotive time breakdown.

        Note: Multiple local variables and branches needed for comprehensive time breakdown.
        """
        loco_breakdown: dict[str, dict[str, float]] = {}

        # Group events by locomotive
        for loco_id in {e.locomotive_id for e in locomotive_events}:
            loco_events = sorted(
                [e for e in locomotive_events if e.locomotive_id == loco_id], key=lambda x: x.timestamp
            )
            loco_coupling = sorted(
                [e for e in coupling_events if e.locomotive_id == loco_id], key=lambda x: x.timestamp
            )

            moving_time = 0.0
            idle_time = 0.0
            coupling_time = 0.0
            decoupling_time = 0.0
            coupling_time_by_type: dict[str, float] = {}
            decoupling_time_by_type: dict[str, float] = {}

            # Calculate moving time
            for i in range(len(loco_events) - 1):
                if loco_events[i].event_type == 'MOVING':
                    duration = loco_events[i + 1].timestamp - loco_events[i].timestamp
                    moving_time += duration

            # Calculate coupling/decoupling time
            for event in loco_coupling:
                if event.duration:
                    if 'COUPLING' in event.event_type and 'DECOUPLING' not in event.event_type:
                        coupling_time += event.duration
                        coupling_time_by_type[event.coupler_type] = (
                            coupling_time_by_type.get(event.coupler_type, 0) + event.duration
                        )
                    elif 'DECOUPLING' in event.event_type:
                        decoupling_time += event.duration
                        decoupling_time_by_type[event.coupler_type] = (
                            decoupling_time_by_type.get(event.coupler_type, 0) + event.duration
                        )

            # Calculate idle time
            total_active = moving_time + coupling_time + decoupling_time
            idle_time = max(0, sim_duration - total_active)

            loco_breakdown[loco_id] = {
                'moving_time': moving_time,
                'idle_time': idle_time,
                'coupling_time': coupling_time,
                'decoupling_time': decoupling_time,
                'coupling_screw': coupling_time_by_type.get('screw', 0),
                'coupling_automatic': coupling_time_by_type.get('automatic', 0),
                'decoupling_screw': decoupling_time_by_type.get('screw', 0),
                'decoupling_automatic': decoupling_time_by_type.get('automatic', 0),
            }

        return loco_breakdown
