"""Domain service for querying computed metrics."""

from typing import Any

from contexts.analytics.domain.value_objects.metrics_snapshot import (
    BottleneckDetection,
    LocomotiveUtilization,
    TrackCapacitySnapshot,
    TrainArrivalMetrics,
    WagonMetrics,
    WorkshopMetrics,
)


class MetricsQueryService:
    """Domain service to query and compute metrics from collected events."""

    def __init__(self, event_stats: dict[str, Any]) -> None:
        self._stats = event_stats

    def get_train_arrivals(self) -> TrainArrivalMetrics:
        """Get train arrival metrics."""
        return TrainArrivalMetrics(
            total_arrivals=self._stats.get("train_arrivals", 0),
            total_wagons=self._stats.get("wagons_arrived", 0),
            arrivals_by_time=self._stats.get("arrivals_by_time", {}),
        )

    def get_wagon_metrics(self) -> WagonMetrics:
        """Get wagon state metrics across all contexts."""
        return WagonMetrics(
            retrofitted_count=self._stats.get("wagons_retrofitted", 0),
            rejected_count=self._stats.get("wagons_rejected", 0),
            in_parking_count=self._stats.get("wagons_in_parking", 0),
            retrofitting_count=self._stats.get("wagons_retrofitting", 0),
            on_retrofit_track_count=self._stats.get("wagons_on_retrofit_track", 0),
            on_retrofitted_track_count=self._stats.get(
                "wagons_on_retrofitted_track", 0
            ),
        )

    def get_locomotive_utilization(self, locomotive_id: str) -> LocomotiveUtilization:
        """Get utilization breakdown for a specific locomotive."""
        loco_data = self._stats.get("locomotives", {}).get(locomotive_id, {})
        return LocomotiveUtilization(
            parking_time=loco_data.get("parking_time", 0.0),
            moving_time=loco_data.get("moving_time", 0.0),
            coupling_time=loco_data.get("coupling_time", 0.0),
            decoupling_time=loco_data.get("decoupling_time", 0.0),
            total_time=loco_data.get("total_time", 0.0),
        )

    def get_all_locomotive_utilizations(self) -> dict[str, LocomotiveUtilization]:
        """Get utilization for all locomotives."""
        locomotives = self._stats.get("locomotives", {})
        return {
            loco_id: self.get_locomotive_utilization(loco_id) for loco_id in locomotives
        }

    def get_workshop_metrics(self, workshop_id: str) -> WorkshopMetrics:
        """Get metrics for a specific workshop."""
        workshop_data = self._stats.get("workshops", {}).get(workshop_id, {})
        return WorkshopMetrics(
            completed_retrofits=workshop_data.get("completed_retrofits", 0),
            total_working_time=workshop_data.get("working_time", 0.0),
            total_waiting_time=workshop_data.get("waiting_time", 0.0),
            wagons_per_hour=workshop_data.get("wagons_per_hour", 0.0),
        )

    def get_all_workshop_metrics(self) -> dict[str, WorkshopMetrics]:
        """Get metrics for all workshops."""
        workshops = self._stats.get("workshops", {})
        return {
            workshop_id: self.get_workshop_metrics(workshop_id)
            for workshop_id in workshops
        }

    def get_track_capacity(
        self, track_id: str, timestamp: float
    ) -> TrackCapacitySnapshot:
        """Get track capacity at specific timestamp."""
        track_data = self._stats.get("tracks", {}).get(track_id, {})
        return TrackCapacitySnapshot(
            track_id=track_id,
            used_capacity=track_data.get("used_capacity", 0),
            total_capacity=track_data.get("total_capacity", 0),
            timestamp=timestamp,
        )

    def get_track_capacity_timeline(self, track_id: str) -> list[TrackCapacitySnapshot]:
        """Get track capacity over time."""
        timeline = self._stats.get("track_timelines", {}).get(track_id, [])
        return [
            TrackCapacitySnapshot(
                track_id=track_id,
                used_capacity=entry["used_capacity"],
                total_capacity=entry["total_capacity"],
                timestamp=entry["timestamp"],
            )
            for entry in timeline
        ]

    def detect_bottlenecks(
        self, over_threshold: float = 90.0, under_threshold: float = 20.0
    ) -> list[BottleneckDetection]:
        """Detect bottlenecks across all resources."""
        bottlenecks: list[BottleneckDetection] = []

        # Workshop bottlenecks
        for workshop_id, metrics in self.get_all_workshop_metrics().items():
            bottleneck = BottleneckDetection.detect(
                "workshop",
                workshop_id,
                metrics.working_percentage,
                over_threshold,
                under_threshold,
            )
            if bottleneck.threshold_exceeded:
                bottlenecks.append(bottleneck)

        # Locomotive bottlenecks (based on non-parking time)
        for loco_id, metrics in self.get_all_locomotive_utilizations().items():
            active_percentage = 100.0 - metrics.parking_percentage
            bottleneck = BottleneckDetection.detect(
                "locomotive",
                loco_id,
                active_percentage,
                over_threshold,
                under_threshold,
            )
            if bottleneck.threshold_exceeded:
                bottlenecks.append(bottleneck)

        # Track bottlenecks (current state)
        tracks = self._stats.get("tracks", {})
        current_time = self._stats.get("current_time", 0.0)
        for track_id in tracks:
            snapshot = self.get_track_capacity(track_id, current_time)
            bottleneck = BottleneckDetection.detect(
                "track",
                track_id,
                snapshot.utilization_percentage,
                over_threshold,
                under_threshold,
            )
            if bottleneck.threshold_exceeded:
                bottlenecks.append(bottleneck)

        return bottlenecks
