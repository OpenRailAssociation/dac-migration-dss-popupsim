"""Analytics Context application layer."""

from pathlib import Path
from typing import Any

from contexts.analytics.domain.repositories.analytics_repository import (
    AnalyticsRepository,
)
from contexts.analytics.domain.services.analytics_service import (
    AnalyticsService,
)
from contexts.analytics.domain.services.event_stream_calculator import (
    EventStreamCalculator,
)
from contexts.analytics.domain.services.rake_analytics_service import (
    RakeAnalyticsService,
)
from contexts.analytics.domain.services.real_time_visualizer import (
    RealTimeVisualizer,
)
from contexts.analytics.domain.services.time_series_service import (
    TimeSeriesService,
)
from contexts.analytics.domain.value_objects.analytics_metrics import (
    AnalyticsMetrics,
    Threshold,
)
from contexts.analytics.infrastructure.exporters.csv_exporter import (
    CSVExporter,
)
from contexts.analytics.infrastructure.exporters.dashboard_exporter import (
    DashboardExporter,
)
from contexts.analytics.infrastructure.exporters.json_exporter import (
    JSONExporter,
)
from contexts.analytics.infrastructure.visualization import (
    Visualizer,
)
from contexts.analytics.infrastructure.visualization.rake_visualizer import (
    RakeVisualizer,
)
from infrastructure.event_bus.event_bus import EventBus
from shared.domain.events.rake_events import (
    RakeFormedEvent,
    RakeProcessingCompletedEvent,
    RakeTransportedEvent,
)

from .services.analytics_application_service import AnalyticsApplicationService
from .services.analytics_query_service import AnalyticsQueryService
from .services.event_stream_service import EventStreamService


class AnalyticsContext:
    """Analytics Context facade."""

    def __init__(
        self,
        event_bus: EventBus,
        repository: AnalyticsRepository,
        track_configs: list[Any] | None = None,
        fill_factor: float = 0.75,
        real_time_callback: Any = None,
    ) -> None:
        self.event_bus = event_bus
        self.event_stream = EventStreamService(event_bus)
        self.app_service = AnalyticsApplicationService(
            event_bus, repository, self.event_stream
        )
        self.query_service = AnalyticsQueryService(repository)
        self.analytics_service = AnalyticsService(self.event_stream, event_bus)
        self.kpi_calculator = EventStreamCalculator(self.event_stream)
        self.visualizer = Visualizer()
        self.json_exporter = JSONExporter()
        self.dashboard_exporter = DashboardExporter()
        self.track_configs = track_configs or []
        self.fill_factor = fill_factor

        # Real-time visualization
        self.real_time_visualizer = RealTimeVisualizer(real_time_callback)
        self.rake_analytics_service = RakeAnalyticsService()
        
        # Track capacity monitoring
        self.track_capacities: dict[str, dict[str, float]] = {}
        self.track_occupancy: dict[str, float] = {}

        self._sync_track_capacities()
        self._subscribe_to_rake_events()
        self._subscribe_to_wagon_events()

    def initialize(self, infrastructure: Any, scenario: Any) -> None:
        """Initialize context."""

    def start_processes(self) -> None:
        """Start processes."""

    def start_session(self, session_id: str) -> None:
        """Start analytics session."""
        self.app_service.start_session(session_id)

    def end_session(self) -> None:
        """End current analytics session."""
        self.app_service.end_session()

    def record_metric(
        self, collector_id: str, key: str, value: Any, timestamp: float | None = None
    ) -> None:
        """Record metric value with optional timestamp."""
        self.app_service.record_metric(collector_id, key, value, timestamp)

    def set_threshold(self, threshold: Threshold) -> None:
        """Set threshold for metric monitoring."""
        self.app_service.set_threshold(threshold)

    def subscribe_to_event(self, event_type: type[Any]) -> None:
        """Subscribe to specific event type."""
        self.event_bus.subscribe(event_type, self.event_collector._collect_event)

    def analyze_session(self) -> AnalyticsMetrics:
        """Analyze current session."""
        return self.app_service.analyze_session()

    def get_metrics(self) -> dict[str, Any]:
        """Get all metrics computed from event stream."""
        metrics = self.app_service.get_metrics()
        # Add event history for timeline validation
        metrics["event_history"] = self.event_stream.collector.get_events()
        return metrics

    def check_threshold_violations(self) -> list[Any]:
        """Check for threshold violations."""
        return self.app_service.check_threshold_violations()

    def compute_all_metrics(self, scenario: Any) -> dict[str, Any]:
        """Compute all system metrics from scenario + events."""
        # Get event-based metrics
        analytics_metrics = self.get_metrics()

        # Compute static configuration metrics from scenario
        config_metrics = {
            "total_scenarios": 1,
            "draft_scenarios": 0,
            "finalized_scenarios": 1,
        }

        # Compute railway infrastructure metrics from scenario
        railway_metrics = {
            "tracks_count": len(scenario.tracks or []),
            "routes_count": len(scenario.routes or []),
            "workshops_count": len(scenario.workshops or []),
        }

        # Compute shunting metrics from scenario + events
        shunting_metrics = {
            "total_locomotives": len(scenario.locomotives or []),
            "available_locomotives": len(scenario.locomotives or []),
            "allocated_locomotives": 0,
            "utilization_percentage": 0.0,
            "total_operations": 0,
            "successful_operations": 0,
            "success_rate": 0.0,
            "average_operation_time": 0.0,
        }

        # Compute external trains metrics from events
        external_trains_metrics = {
            "scheduled_trains": 0,
            "processed_trains": 0,
            "total_wagons": analytics_metrics.get("wagons_arrived", 0),
            "completed_wagons": analytics_metrics.get("retrofits_completed", 0),
        }

        # Compute yard metrics from events
        yard_metrics = {
            "classified_wagons": analytics_metrics.get("wagons_arrived", 0),
            "rejected_wagons": analytics_metrics.get("wagons_rejected", 0),
            "parking_areas": 0,
        }

        # Compute popup metrics from scenario
        popup_metrics = {
            "workshops": len(scenario.workshops or []),
            "total_bays": sum(
                getattr(w, "retrofit_stations", 2) for w in (scenario.workshops or [])
            ),
        }

        return {
            "configuration": config_metrics,
            "railway": railway_metrics,
            "shunting": shunting_metrics,
            "external_trains": external_trains_metrics,
            "yard": yard_metrics,
            "popup": popup_metrics,
            "analytics": analytics_metrics,
        }

    def get_current_state(self) -> dict[str, Any]:
        """Get current system state snapshot."""
        return self.event_stream.collector.get_current_state()

    def _sync_track_capacities(self) -> None:
        """Calculate and sync track capacities from configuration."""
        # Initialize with default track capacities (will be updated from scenario)
        default_tracks = {
            "parking1": 150.0, "parking2": 270.0, "parking3": 257.0,
            "parking5": 216.0, "parking6": 266.0, "parking7": 212.0,
            "parking8": 203.0, "parking9": 400.0, "parking10": 600.0,
            "parking11": 400.0, "parking12": 400.0, "parking13": 400.0,
            "parking14": 400.0, "parking15": 400.0, "parking16": 100.0,
            "collection1": 500.0, "collection2": 500.0,
            "retrofit": 426.0, "retrofitted": 352.0,
            "WS1": 260.0, "WS2": 260.0,
        }
        for track_id, length in default_tracks.items():
            self.track_capacities[track_id] = {"max_capacity": length}
            self.track_occupancy[track_id] = 0.0

    def get_track_metrics(self) -> dict[str, Any]:
        """Get track capacity metrics with utilization and state.

        Returns:
            Dict with track metrics including:
            - max_capacity: Maximum capacity in meters
            - current_occupancy: Current occupied length in meters
            - utilization_percent: Utilization percentage
            - state: green/yellow/red classification
        """
        metrics = {}
        for track_id, capacity_info in self.track_capacities.items():
            max_capacity = capacity_info.get("max_capacity", 0)
            current = self.track_occupancy.get(track_id, 0)
            utilization = (current / max_capacity * 100) if max_capacity > 0 else 0
            state = "green" if utilization < 70 else "yellow" if utilization < 90 else "red"
            
            metrics[track_id] = {
                "max_capacity": max_capacity,
                "current_occupancy": current,
                "utilization_percent": utilization,
                "state": state,
            }
        return metrics

    def get_time_series(
        self, metric_name: str, interval_seconds: float = 3600.0
    ) -> list[tuple[float, Any]]:
        """Get time-series data for specific metric.

        Args:
            metric_name: Metric to track (train_arrivals, wagons_arrived, etc.)
            interval_seconds: Time interval in seconds (default: 1 hour)
                - Use TimeGranularity enum values or custom seconds
                - Examples: 60 (1 min), 300 (5 min), 3600 (1 hour)

        Returns:
            List of (timestamp, value) tuples
        """
        events = self.event_stream.collector.get_events()
        ts_service = TimeSeriesService(events)
        return ts_service.get_time_series(metric_name, interval_seconds)

    def get_all_time_series(
        self, interval_seconds: float = 3600.0
    ) -> dict[str, list[tuple[float, Any]]]:
        """Get all time-series metrics.

        Args:
            interval_seconds: Time interval in seconds (default: 1 hour)
                - Use TimeGranularity enum values or custom seconds
                - Examples: 60 (1 min), 300 (5 min), 3600 (1 hour)

        Returns:
            Dict mapping metric names to time-series data
        """
        events = self.event_stream.collector.get_events()
        ts_service = TimeSeriesService(events)
        return ts_service.get_all_time_series(interval_seconds)

    def get_track_capacity_time_series(
        self,
    ) -> dict[str, list[tuple[float, dict[str, Any]]]]:
        """Get track capacity utilization over time.

        Returns:
            Dict mapping track IDs to time-series of capacity metrics
        """
        # This will be populated as events are processed
        # For now, return current state
        current_metrics = self.get_track_metrics()
        return {"current": [(0.0, current_metrics)]}

    def get_context_metrics(self, context_name: str) -> dict[str, Any]:
        """Get metrics for specific context from events."""
        # Filter events by context and compute metrics
        all_stats = self.event_stream.compute_statistics()
        return {k: v for k, v in all_stats.items() if context_name.lower() in k.lower()}

    def clear_all_metrics(self) -> None:
        """Clear all collected events and metrics."""
        self.app_service.clear_all_metrics()

    def get_context_analysis(self) -> dict[str, Any]:
        """Get context analysis including bottlenecks and flow."""
        return self.analytics_service.get_cross_context_metrics()

    def get_status(self) -> dict[str, Any]:
        """Get system status and alerts."""
        self.analytics_service.check_alerts()  # Update alerts
        return self.analytics_service.get_current_status()

    def get_kpis(self) -> dict[str, Any]:
        """Get KPI analysis."""
        return self.kpi_calculator.get_kpi_summary()

    def generate_visualizations(self, output_dir: Any) -> list[Any]:
        """Generate all visualization charts."""
        return self.visualizer.generate_all_charts(self, output_dir)

    def export_to_json(self, output_path: Any) -> None:
        """Export analytics report to JSON."""
        self.json_exporter.export_report(self, output_path)

    def export_dashboard_json(self, output_path: Any) -> None:
        """Export dashboard-ready data to JSON."""
        self.json_exporter.export_dashboard_data(self, output_path)

    def export_time_series_json(
        self, output_path: Any, interval_seconds: float = 3600.0
    ) -> None:
        """Export time-series data to JSON."""
        time_series_data = self.get_all_time_series(interval_seconds)
        self.json_exporter.export_time_series(time_series_data, output_path)

    def export_time_series_csv(
        self, output_path: Any, interval_seconds: float = 3600.0
    ) -> None:
        """Export time-series data to CSV."""
        time_series_data = self.get_all_time_series(interval_seconds)
        csv_exporter = CSVExporter()
        csv_exporter.export_time_series(time_series_data, output_path)

    def export_time_series_both(
        self, base_path: Any, interval_seconds: float = 3600.0
    ) -> None:
        """Export time-series data to both JSON and CSV formats."""
        base = Path(base_path)
        self.export_time_series_json(base.with_suffix(".json"), interval_seconds)
        self.export_time_series_csv(base.with_suffix(".csv"), interval_seconds)

    def export_utilization_breakdown_csv(self, output_path: Any) -> None:
        """Export utilization breakdown to CSV."""
        breakdown_data = self.get_comprehensive_metrics()["utilization_breakdowns"]
        csv_exporter = CSVExporter()
        csv_exporter.export_utilization_breakdown(breakdown_data, output_path)

    def export_dashboard_data(
        self, output_dir: Path, interval_seconds: float = 3600.0, yard_context: Any = None
    ) -> dict[str, Path]:
        """Export all data required for Streamlit dashboard.

        Parameters
        ----------
        output_dir : Path
            Output directory for all dashboard files.
        interval_seconds : float
            Time granularity for time-series data (default: 1 hour = 3600s).

        Returns
        -------
        dict[str, Path]
            Mapping of file type to generated file path.

        Examples
        --------
        >>> context = AnalyticsContext(event_bus, repository)
        >>> context.start_session("my_simulation")
        >>> # ... simulation runs ...
        >>> context.end_session()
        >>> files = context.export_dashboard_data(Path("output/dashboard"))
        >>> print(f"Exported {len(files)} files")
        """
        return self.dashboard_exporter.export_all(self, output_dir, interval_seconds, yard_context)

    def start_real_time_visualization(self) -> None:
        """Start real-time visualization updates."""
        self.real_time_visualizer.start_real_time_updates()

    def stop_real_time_visualization(self) -> None:
        """Stop real-time visualization updates."""
        self.real_time_visualizer.stop_real_time_updates()

    def update_real_time_metrics(self, timestamp: float) -> None:
        """Update real-time metrics for visualization."""
        if self.real_time_visualizer.is_active:
            current_metrics = self.get_metrics()
            self.real_time_visualizer.update_metrics(current_metrics, timestamp)

    def get_metrics_report(
        self,
        interval_seconds: float = 3600.0,
        thresholds: Any | None = None,
    ) -> dict[str, Any]:
        """Get metrics report including all KPIs, statistics, and bottlenecks.

        This method provides all metrics required by the analytics context:
        - Train arrivals with wagon counts over time
        - Wagon state distribution (retrofitted, rejected, parking, retrofitting, on tracks)
        - Locomotive utilization breakdown and time-series
        - Workshop performance metrics and utilization
        - Track capacity utilization and state visualization
        - Bottleneck detection across all resources

        Parameters
        ----------
        interval_seconds : float
            Time interval for time-series aggregation (default: 1 hour = 3600s).
        thresholds : BottleneckThresholds | None
            Custom thresholds for bottleneck detection. If None, uses defaults:
            - Workshop overutilization: 90%
            - Workshop underutilization: 30%
            - Track high capacity: 85%
            - Track full capacity: 95%
            - Locomotive overutilization: 90%
            - Locomotive underutilization: 20%

        Returns
        -------
        dict[str, Any]
            Complete metrics report with:
            - train_arrivals: TrainArrivalMetrics
            - wagon_states: WagonStateMetrics
            - locomotive_metrics: LocomotiveMetrics
            - workshop_metrics: list[WorkshopMetrics]
            - track_metrics: list[TrackStateMetrics]
            - bottlenecks: list[BottleneckDetection]
            - simulation_duration_hours: float

        Examples
        --------
        >>> context = AnalyticsContext(event_bus, repository)
        >>> context.start_session("my_simulation")
        >>> # ... simulation runs ...
        >>> metrics = context.get_metrics_report()
        >>> print(f"Trains arrived: {metrics['train_arrivals'].total_trains}")
        >>> print(f"Wagons retrofitted: {metrics['wagon_states'].retrofitted}")
        >>> for bottleneck in metrics['bottlenecks']:
        ...     print(f"Bottleneck: {bottleneck.description}")
        """
        return self.app_service.get_metrics_report(
            interval_seconds=interval_seconds, thresholds=thresholds
        )

    def _subscribe_to_rake_events(self) -> None:
        """Subscribe to rake domain events for analytics."""
        self.event_bus.subscribe(RakeFormedEvent, self._handle_rake_formed)
        self.event_bus.subscribe(RakeTransportedEvent, self._handle_rake_transported)
        self.event_bus.subscribe(
            RakeProcessingCompletedEvent, self._handle_rake_processing_completed
        )
    
    def _subscribe_to_wagon_events(self) -> None:
        """Subscribe to wagon events for track capacity monitoring."""
        from contexts.yard_operations.domain.events.yard_events import WagonParkedEvent, WagonDistributedEvent
        self.event_bus.subscribe(WagonParkedEvent, self._handle_wagon_parked)
        self.event_bus.subscribe(WagonDistributedEvent, self._handle_wagon_distributed)
    
    def _handle_wagon_parked(self, event: Any) -> None:
        """Track wagon parking for capacity monitoring."""
        parking_id = getattr(event, "parking_area_id", None)
        if parking_id and parking_id in self.track_capacities:
            # Assume 15m per wagon
            self.track_occupancy[parking_id] = self.track_occupancy.get(parking_id, 0) + 15.0
            
            # Remove from retrofitted track when moved to parking
            retrofitted_id = "retrofitted"
            if retrofitted_id in self.track_capacities:
                self.track_occupancy[retrofitted_id] = max(0.0, self.track_occupancy.get(retrofitted_id, 0) - 15.0)
    
    def _handle_wagon_distributed(self, event: Any) -> None:
        """Track wagon distribution for capacity monitoring."""
        # Wagons distributed to track specified in event
        track_id = getattr(event, "track_id", "retrofitted")
        if track_id in self.track_capacities:
            self.track_occupancy[track_id] = self.track_occupancy.get(track_id, 0) + 15.0

    def _handle_rake_formed(self, event: RakeFormedEvent) -> None:
        """Handle rake formation event."""
        # Extract rake from event (assuming event has rake attribute)
        if hasattr(event, "rake"):
            self.rake_analytics_service.record_rake_formation(
                timestamp=getattr(event, "timestamp", 0.0),
                rake=event.rake,
                strategy="workshop_capacity",  # Default strategy
            )

    def _handle_rake_transported(self, event: RakeTransportedEvent) -> None:
        """Handle rake transport event."""
        if hasattr(event, "rake"):
            self.rake_analytics_service.record_rake_transport(
                timestamp=getattr(event, "timestamp", 0.0),
                rake=event.rake,
                from_track=event.from_track,
                to_track=event.to_track,
            )

    def _handle_rake_processing_completed(
        self, event: RakeProcessingCompletedEvent
    ) -> None:
        """Handle rake processing completion event."""
        if hasattr(event, "rake"):
            self.rake_analytics_service.record_rake_processing(
                timestamp=getattr(event, "timestamp", 0.0),
                rake=event.rake,
                status="completed",
            )

    def get_rake_analytics(self) -> dict[str, Any]:
        """Get comprehensive rake analytics."""
        return {
            "formations_by_time": self.rake_analytics_service.get_rake_formations_by_time(),
            "size_distribution": self.rake_analytics_service.get_rake_size_distribution(),
            "strategy_stats": self.rake_analytics_service.get_formation_strategy_stats(),
            "track_occupancy": {
                track: self.rake_analytics_service.get_track_occupancy_timeline(track)
                for track in ["classification", "WS1", "WS2", "collection"]
            },
        }

    def generate_rake_visualizations(self, output_dir: str) -> list[str]:
        """Generate rake-specific visualizations."""
        visualizer = RakeVisualizer(self.rake_analytics_service)
        generated_files = []

        # Generate timeline plot
        timeline_path = f"{output_dir}/rake_formations_timeline.png"
        visualizer.plot_rake_formations_timeline(timeline_path)
        generated_files.append(timeline_path)

        # Generate track occupancy plot
        occupancy_path = f"{output_dir}/track_occupancy.png"
        tracks = ["classification", "WS1", "WS2", "collection"]
        visualizer.plot_track_occupancy(tracks, occupancy_path)
        generated_files.append(occupancy_path)

        # Generate Gantt chart
        gantt_path = f"{output_dir}/rake_gantt_chart.png"
        visualizer.plot_rake_gantt_chart(gantt_path)
        generated_files.append(gantt_path)

        # Generate size distribution
        size_dist_path = f"{output_dir}/rake_size_distribution.png"
        visualizer.plot_rake_size_distribution(size_dist_path)
        generated_files.append(size_dist_path)

        # Generate comprehensive dashboard
        dashboard_path = f"{output_dir}/rake_dashboard.png"
        visualizer.create_rake_dashboard(tracks, dashboard_path)
        generated_files.append(dashboard_path)

        return generated_files

    def get_status(self) -> dict[str, Any]:
        """Get status."""
        return {"status": "ready"}

    def cleanup(self) -> None:
        """Cleanup."""

    def on_simulation_started(self, event: Any) -> None:
        """Handle simulation started."""

    def on_simulation_ended(self, event: Any) -> None:
        """Handle simulation ended."""

    def on_simulation_failed(self, event: Any) -> None:
        """Handle simulation failed."""
