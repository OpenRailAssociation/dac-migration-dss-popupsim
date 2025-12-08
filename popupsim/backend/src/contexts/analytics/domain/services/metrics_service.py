"""Metrics service for all analytics requirements.

This service provides all metrics, KPIs, and statistics required by the analytics context:
- Train arrivals with wagon counts over time
- Wagon state tracking (retrofitted, rejected, parking, retrofitting, on tracks)
- Locomotive utilization breakdown and time-series
- Workshop utilization, completion metrics, and time tracking
- Track capacity utilization and state visualization
- Bottleneck detection across all resources
"""

from collections import defaultdict
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class BottleneckThresholds:
    """Configuration for bottleneck detection."""

    workshop_overutilization: float = 0.9  # 90%
    workshop_underutilization: float = 0.3  # 30%
    track_high_capacity: float = 0.85  # 85%
    track_full_capacity: float = 0.95  # 95%
    locomotive_overutilization: float = 0.9  # 90%
    locomotive_underutilization: float = 0.2  # 20%


@dataclass
class BottleneckDetection:
    """Bottleneck detection result."""

    resource_type: str  # "workshop", "track", "locomotive"
    resource_id: str
    severity: str  # "overutilization", "underutilization", "full"
    utilization: float
    threshold: float
    description: str


@dataclass
class TrainArrivalMetrics:
    """Train arrival metrics over time."""

    total_trains: int
    total_wagons: int
    arrivals_by_time: list[
        tuple[float, dict[str, int]]
    ]  # (timestamp, {trains, wagons})


@dataclass
class WagonStateMetrics:
    """Current wagon state across all contexts."""

    retrofitted: int
    rejected: int
    in_parking: int
    retrofitting: int
    on_retrofit_track: int
    on_retrofitted_track: int
    total_arrived: int


@dataclass
class LocomotiveMetrics:
    """Locomotive utilization metrics."""

    total_locomotives: int
    utilization_breakdown: dict[str, int]  # {parking, moving, coupling, decoupling}
    utilization_over_time: list[tuple[float, dict[str, int]]]
    average_utilization: float


@dataclass
class WorkshopMetrics:
    """Workshop performance metrics."""

    workshop_id: str
    completed_retrofits: int
    total_retrofit_time: float
    total_waiting_time: float
    wagons_per_hour: float
    utilization_breakdown: dict[str, float]  # {working, waiting}
    utilization_percent: float


@dataclass
class TrackStateMetrics:
    """Track capacity and state metrics."""

    track_id: str
    capacity: float
    current_occupancy: float
    utilization_percent: float
    state: str  # "empty", "nearly_full", "full"
    occupancy_over_time: list[tuple[float, float]]


class MetricsService:
    """Domain service for analytics metrics."""

    def __init__(
        self,
        events: list[tuple[float, Any]],
        event_counts: dict[str, int],
        duration_hours: float,
        current_state: dict[str, Any],
        thresholds: BottleneckThresholds | None = None,
    ) -> None:
        """Initialize comprehensive metrics service.

        Parameters
        ----------
        events : list[tuple[float, Any]]
            All simulation events with timestamps.
        event_counts : dict[str, int]
            Count of each event type.
        duration_hours : float
            Total simulation duration in hours.
        current_state : dict[str, Any]
            Current system state from StateTrackingService.
        thresholds : BottleneckThresholds | None
            Bottleneck detection thresholds.
        """
        self.events = events
        self.event_counts = event_counts
        self.duration_hours = duration_hours
        self.current_state = current_state
        self.thresholds = thresholds or BottleneckThresholds()

    def get_train_arrival_metrics(
        self, interval_seconds: float = 3600.0
    ) -> TrainArrivalMetrics:
        """Get train arrival metrics with time-series data.

        Parameters
        ----------
        interval_seconds : float
            Time interval for aggregation (default: 1 hour).

        Returns
        -------
        TrainArrivalMetrics
            Train arrivals and wagon counts over time.
        """
        train_events = [
            (ts, e) for ts, e in self.events if type(e).__name__ == "TrainArrivedEvent"
        ]

        total_trains = len(train_events)
        total_wagons = sum(len(getattr(e, "wagons", [])) for _, e in train_events)

        # Time-series aggregation
        arrivals_by_time = self._aggregate_train_arrivals(
            train_events, interval_seconds
        )

        return TrainArrivalMetrics(
            total_trains=total_trains,
            total_wagons=total_wagons,
            arrivals_by_time=arrivals_by_time,
        )

    def get_wagon_state_metrics(self) -> WagonStateMetrics:
        """Get current wagon state across all contexts.

        Returns
        -------
        WagonStateMetrics
            Current wagon distribution across states.
        """
        retrofitted = self.event_counts.get(
            "RetrofitCompletedEvent", 0
        ) + self.event_counts.get("WagonRetrofitCompletedEvent", 0)
        rejected = self.event_counts.get("WagonRejectedEvent", 0)
        in_parking = self.current_state.get("wagons_on_retrofitted_track", 0)
        retrofitting = self.current_state.get("wagons_retrofitting", 0)
        on_retrofit_track = self.current_state.get("wagons_on_retrofit_track", 0)
        on_retrofitted_track = self.current_state.get("wagons_on_retrofitted_track", 0)

        total_arrived = sum(
            len(getattr(e, "wagons", []))
            for _, e in self.events
            if type(e).__name__ == "TrainArrivedEvent"
        )

        return WagonStateMetrics(
            retrofitted=retrofitted,
            rejected=rejected,
            in_parking=in_parking,
            retrofitting=retrofitting,
            on_retrofit_track=on_retrofit_track,
            on_retrofitted_track=on_retrofitted_track,
            total_arrived=total_arrived,
        )

    def get_locomotive_metrics(
        self, interval_seconds: float = 3600.0
    ) -> LocomotiveMetrics:
        """Get locomotive utilization metrics.

        Parameters
        ----------
        interval_seconds : float
            Time interval for time-series data.

        Returns
        -------
        LocomotiveMetrics
            Locomotive utilization breakdown and time-series.
        """
        from .utilization_breakdown_service import UtilizationBreakdownService

        # Get detailed utilization breakdown
        breakdown_service = UtilizationBreakdownService(
            self.events, self.duration_hours
        )
        loco_breakdown = breakdown_service.get_locomotive_breakdown()

        total_locomotives = self.current_state.get("total_active_locomotives", 0)

        # Calculate utilization over time
        utilization_over_time = self._calculate_locomotive_utilization_over_time(
            interval_seconds
        )

        # Average utilization based on non-parking time
        non_parking_percentage = 100 - loco_breakdown.action_percentages.get(
            "parking", 0
        )
        avg_utilization = non_parking_percentage / 100

        return LocomotiveMetrics(
            total_locomotives=total_locomotives,
            utilization_breakdown=loco_breakdown.action_percentages,
            utilization_over_time=utilization_over_time,
            average_utilization=avg_utilization,
        )

    def get_workshop_metrics(self) -> list[WorkshopMetrics]:
        """Get workshop performance metrics for all workshops.

        Returns
        -------
        list[WorkshopMetrics]
            Metrics for each workshop.
        """
        workshop_states = self.current_state.get("workshop_states", {})
        workshop_metrics_list = []

        # Track retrofit times per workshop
        retrofit_times: dict[str, list[float]] = defaultdict(list)
        waiting_times: dict[str, float] = defaultdict(float)

        for _ts, event in self.events:
            event_type = type(event).__name__
            workshop_id = getattr(event, "workshop_id", None)

            if not workshop_id:
                continue

            if event_type == "RetrofitCompletedEvent":
                duration = getattr(event, "duration", 0.0)
                retrofit_times[workshop_id].append(duration)
            elif event_type == "WagonWaitingEvent":
                wait_duration = getattr(event, "duration", 0.0)
                waiting_times[workshop_id] += wait_duration

        # Get detailed workshop breakdowns
        from .utilization_breakdown_service import UtilizationBreakdownService

        breakdown_service = UtilizationBreakdownService(
            self.events, self.duration_hours
        )
        workshop_breakdowns = breakdown_service.get_workshop_breakdown()

        for workshop_id, state in workshop_states.items():
            completed = len(retrofit_times.get(workshop_id, []))
            total_retrofit_time = sum(retrofit_times.get(workshop_id, []))
            total_waiting = waiting_times.get(workshop_id, 0.0)

            wagons_per_hour = completed / max(self.duration_hours, 0.1)

            # Use detailed breakdown if available
            breakdown = workshop_breakdowns.get(workshop_id)
            if breakdown:
                utilization_breakdown = breakdown.action_percentages
                utilization_percent = breakdown.action_percentages.get("working", 0)
            else:
                working_bays = state.get("working", 0)
                total_bays = state.get("total_bays", 1)
                utilization_percent = (working_bays / max(total_bays, 1)) * 100
                utilization_breakdown = {
                    "working": utilization_percent,
                    "waiting": 100 - utilization_percent,
                }

            workshop_metrics_list.append(
                WorkshopMetrics(
                    workshop_id=workshop_id,
                    completed_retrofits=completed,
                    total_retrofit_time=total_retrofit_time,
                    total_waiting_time=total_waiting,
                    wagons_per_hour=wagons_per_hour,
                    utilization_breakdown=utilization_breakdown,
                    utilization_percent=utilization_percent,
                )
            )

        return workshop_metrics_list

    def get_track_state_metrics(
        self, interval_seconds: float = 3600.0
    ) -> list[TrackStateMetrics]:
        """Get track capacity and state metrics.

        Parameters
        ----------
        interval_seconds : float
            Time interval for occupancy time-series.

        Returns
        -------
        list[TrackStateMetrics]
            Metrics for each track with state visualization.
        """
        track_occupancy = self.current_state.get("track_occupancy", {})
        track_metrics_list = []

        for track_id, track_data in track_occupancy.items():
            current_occupancy = track_data.get("current_occupancy", 0)
            capacity = track_data.get("capacity", 100.0)  # Default capacity

            utilization_percent = (current_occupancy / max(capacity, 1)) * 100

            # Determine state based on thresholds
            if utilization_percent >= self.thresholds.track_full_capacity * 100:
                state = "full"
            elif utilization_percent >= self.thresholds.track_high_capacity * 100:
                state = "nearly_full"
            else:
                state = "empty"

            # Calculate occupancy over time
            occupancy_over_time = self._calculate_track_occupancy_over_time(
                track_id, interval_seconds
            )

            track_metrics_list.append(
                TrackStateMetrics(
                    track_id=track_id,
                    capacity=capacity,
                    current_occupancy=current_occupancy,
                    utilization_percent=utilization_percent,
                    state=state,
                    occupancy_over_time=occupancy_over_time,
                )
            )

        return track_metrics_list

    def detect_bottlenecks(self) -> list[BottleneckDetection]:
        """Detect bottlenecks across all resources.

        Returns
        -------
        list[BottleneckDetection]
            Detected bottlenecks with severity and recommendations.
        """
        bottlenecks = []

        # Workshop bottlenecks
        workshop_metrics = self.get_workshop_metrics()
        for workshop in workshop_metrics:
            utilization = workshop.utilization_percent / 100

            if utilization > self.thresholds.workshop_overutilization:
                bottlenecks.append(
                    BottleneckDetection(
                        resource_type="workshop",
                        resource_id=workshop.workshop_id,
                        severity="overutilization",
                        utilization=utilization,
                        threshold=self.thresholds.workshop_overutilization,
                        description=f"Workshop {workshop.workshop_id} is overutilized at {utilization:.1%}",
                    )
                )
            elif utilization < self.thresholds.workshop_underutilization:
                bottlenecks.append(
                    BottleneckDetection(
                        resource_type="workshop",
                        resource_id=workshop.workshop_id,
                        severity="underutilization",
                        utilization=utilization,
                        threshold=self.thresholds.workshop_underutilization,
                        description=f"Workshop {workshop.workshop_id} is underutilized at {utilization:.1%}",
                    )
                )

        # Track bottlenecks
        track_metrics = self.get_track_state_metrics()
        for track in track_metrics:
            utilization = track.utilization_percent / 100

            if utilization >= self.thresholds.track_full_capacity:
                bottlenecks.append(
                    BottleneckDetection(
                        resource_type="track",
                        resource_id=track.track_id,
                        severity="full",
                        utilization=utilization,
                        threshold=self.thresholds.track_full_capacity,
                        description=f"Track {track.track_id} is at full capacity ({utilization:.1%})",
                    )
                )
            elif utilization >= self.thresholds.track_high_capacity:
                bottlenecks.append(
                    BottleneckDetection(
                        resource_type="track",
                        resource_id=track.track_id,
                        severity="overutilization",
                        utilization=utilization,
                        threshold=self.thresholds.track_high_capacity,
                        description=f"Track {track.track_id} is nearly full at {utilization:.1%}",
                    )
                )

        # Locomotive bottlenecks
        loco_metrics = self.get_locomotive_metrics()
        if loco_metrics.total_locomotives > 0:
            utilization = loco_metrics.average_utilization

            if utilization > self.thresholds.locomotive_overutilization:
                bottlenecks.append(
                    BottleneckDetection(
                        resource_type="locomotive",
                        resource_id="fleet",
                        severity="overutilization",
                        utilization=utilization,
                        threshold=self.thresholds.locomotive_overutilization,
                        description=f"Locomotive fleet is overutilized at {utilization:.1%}",
                    )
                )
            elif utilization < self.thresholds.locomotive_underutilization:
                bottlenecks.append(
                    BottleneckDetection(
                        resource_type="locomotive",
                        resource_id="fleet",
                        severity="underutilization",
                        utilization=utilization,
                        threshold=self.thresholds.locomotive_underutilization,
                        description=f"Locomotive fleet is underutilized at {utilization:.1%}",
                    )
                )

        return bottlenecks

    def get_utilization_breakdowns(self) -> dict[str, Any]:
        """Get detailed utilization breakdowns for all resources.

        Returns
        -------
        dict[str, Any]
            Utilization breakdowns with time and percentages.
        """
        from .utilization_breakdown_service import UtilizationBreakdownService

        breakdown_service = UtilizationBreakdownService(
            self.events, self.duration_hours
        )

        return {
            "locomotive_breakdown": breakdown_service.get_locomotive_breakdown(),
            "wagon_breakdown": breakdown_service.get_wagon_breakdown(),
            "workshop_breakdowns": breakdown_service.get_workshop_breakdown(),
        }

    def get_all_metrics(self) -> dict[str, Any]:
        """Get all metrics in a single comprehensive report.

        Returns
        -------
        dict[str, Any]
            Complete metrics report with all KPIs and statistics.
        """
        return {
            "train_arrivals": self.get_train_arrival_metrics(),
            "wagon_states": self.get_wagon_state_metrics(),
            "locomotive_metrics": self.get_locomotive_metrics(),
            "workshop_metrics": self.get_workshop_metrics(),
            "track_metrics": self.get_track_state_metrics(),
            "bottlenecks": self.detect_bottlenecks(),
            "utilization_breakdowns": self.get_utilization_breakdowns(),
            "simulation_duration_hours": self.duration_hours,
        }

    # Private helper methods

    def _aggregate_train_arrivals(
        self, train_events: list[tuple[float, Any]], interval_seconds: float
    ) -> list[tuple[float, dict[str, int]]]:
        """Aggregate train arrivals into time buckets."""
        if not train_events:
            return []

        timestamps = [ts for ts, _ in train_events]
        start_time = min(timestamps)
        end_time = max(timestamps)

        time_series = []
        current_time = start_time

        while current_time <= end_time:
            bucket_end = current_time + interval_seconds
            bucket_events = [
                e for ts, e in train_events if current_time <= ts < bucket_end
            ]

            trains_count = len(bucket_events)
            wagons_count = sum(len(getattr(e, "wagons", [])) for e in bucket_events)

            time_series.append(
                (current_time, {"trains": trains_count, "wagons": wagons_count})
            )
            current_time = bucket_end

        return time_series

    def _calculate_locomotive_utilization_over_time(
        self, interval_seconds: float
    ) -> list[tuple[float, dict[str, int]]]:
        """Calculate locomotive utilization breakdown over time."""
        loco_events = [
            (ts, e)
            for ts, e in self.events
            if type(e).__name__
            in (
                "LocomotiveAllocatedEvent",
                "LocomotiveReleasedEvent",
                "LocomotiveLocationChangedEvent",
            )
        ]

        if not loco_events:
            return []

        timestamps = [ts for ts, _ in loco_events]
        start_time = min(timestamps)
        end_time = max(timestamps)

        time_series = []
        current_time = start_time

        while current_time <= end_time:
            bucket_end = current_time + interval_seconds
            bucket_events = [
                e for ts, e in loco_events if current_time <= ts < bucket_end
            ]

            breakdown = defaultdict(int)
            for event in bucket_events:
                event_type = type(event).__name__
                if event_type == "LocomotiveAllocatedEvent":
                    breakdown["moving"] += 1
                elif event_type == "LocomotiveReleasedEvent":
                    breakdown["parking"] += 1

            time_series.append((current_time, dict(breakdown)))
            current_time = bucket_end

        return time_series

    def _calculate_track_occupancy_over_time(
        self, track_id: str, interval_seconds: float
    ) -> list[tuple[float, float]]:
        """Calculate track occupancy over time."""
        track_events = [
            (ts, e)
            for ts, e in self.events
            if type(e).__name__ in ("WagonDistributedEvent", "WagonParkedEvent")
            and getattr(e, "track_id", None) == track_id
        ]

        if not track_events:
            return []

        timestamps = [ts for ts, _ in track_events]
        start_time = min(timestamps)
        end_time = max(timestamps)

        time_series = []
        current_time = start_time
        cumulative_occupancy = 0.0

        while current_time <= end_time:
            bucket_end = current_time + interval_seconds
            bucket_events = [
                e for ts, e in track_events if current_time <= ts < bucket_end
            ]

            # Count wagons added to track
            cumulative_occupancy += len(bucket_events)

            time_series.append((current_time, cumulative_occupancy))
            current_time = bucket_end

        return time_series
