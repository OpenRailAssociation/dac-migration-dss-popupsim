"""Example usage of metrics service.

This example demonstrates how to use the MetricsService to get
all required analytics metrics, KPIs, and statistics.
"""

from pathlib import Path

from contexts.analytics.application.analytics_context import (
    AnalyticsContext,
)
from contexts.analytics.domain.services.metrics_service import (
    BottleneckThresholds,
)
from contexts.analytics.infrastructure.repositories.in_memory_analytics_repository import (
    InMemoryAnalyticsRepository,
)
from infrastructure.event_bus.event_bus import EventBus


def example_metrics_report() -> None:
    """Example: Get metrics report from analytics context."""
    # Setup
    event_bus = EventBus()
    repository = InMemoryAnalyticsRepository()
    context = AnalyticsContext(event_bus, repository)

    # Start analytics session
    context.start_session("metrics_demo")

    # Simulate some events (in real usage, these come from other contexts)
    # ... simulation runs and events are collected ...

    # Get metrics with default thresholds
    metrics = context.get_metrics_report()

    # Access different metric categories
    metrics["train_arrivals"]

    metrics["wagon_states"]

    metrics["locomotive_metrics"]

    for _workshop in metrics["workshop_metrics"]:
        pass

    for _track in metrics["track_metrics"]:
        pass

    bottlenecks = metrics["bottlenecks"]
    if bottlenecks:
        for _bottleneck in bottlenecks:
            pass
    else:
        pass

    # End session
    context.end_session()


def example_custom_thresholds() -> None:
    """Example: Use custom bottleneck detection thresholds."""
    event_bus = EventBus()
    repository = InMemoryAnalyticsRepository()
    context = AnalyticsContext(event_bus, repository)

    context.start_session("custom_thresholds_demo")

    # Define custom thresholds
    custom_thresholds = BottleneckThresholds(
        workshop_overutilization=0.85,  # 85% instead of default 90%
        workshop_underutilization=0.25,  # 25% instead of default 30%
        track_high_capacity=0.80,  # 80% instead of default 85%
        track_full_capacity=0.90,  # 90% instead of default 95%
        locomotive_overutilization=0.85,  # 85% instead of default 90%
        locomotive_underutilization=0.15,  # 15% instead of default 20%
    )

    # Get metrics with custom thresholds
    metrics = context.get_metrics_report(
        interval_seconds=1800.0,  # 30-minute intervals
        thresholds=custom_thresholds,
    )

    for _bottleneck in metrics["bottlenecks"]:
        pass

    context.end_session()


def example_time_series_analysis() -> None:
    """Example: Analyze time-series data from metrics."""
    event_bus = EventBus()
    repository = InMemoryAnalyticsRepository()
    context = AnalyticsContext(event_bus, repository)

    context.start_session("time_series_demo")

    # Get metrics with hourly intervals
    metrics = context.get_metrics_report(interval_seconds=3600.0)

    # Analyze train arrivals over time
    train_metrics = metrics["train_arrivals"]
    for _timestamp, _data in train_metrics.arrivals_by_time:
        pass

    # Analyze locomotive utilization over time
    loco_metrics = metrics["locomotive_metrics"]
    for _timestamp, _breakdown in loco_metrics.utilization_over_time:
        pass

    # Analyze track occupancy over time
    for track in metrics["track_metrics"]:
        for _timestamp, _occupancy in track.occupancy_over_time[:5]:  # First 5 entries
            pass

    context.end_session()


def example_export_metrics() -> None:
    """Example: Export metrics to JSON."""
    import json
    from dataclasses import asdict

    event_bus = EventBus()
    repository = InMemoryAnalyticsRepository()
    context = AnalyticsContext(event_bus, repository)

    context.start_session("export_demo")

    # Get metrics
    metrics = context.get_metrics_report()

    # Convert to dict for JSON export
    def convert_to_dict(obj: object) -> dict:
        """Convert dataclass to dict recursively."""
        if hasattr(obj, "__dataclass_fields__"):
            return {
                k: convert_to_dict(v)
                for k, v in asdict(obj).items()  # type: ignore[arg-type]
            }
        if isinstance(obj, list):
            return [convert_to_dict(item) for item in obj]  # type: ignore[misc]
        if isinstance(obj, dict):
            return {k: convert_to_dict(v) for k, v in obj.items()}  # type: ignore[misc]
        return obj  # type: ignore[return-value]

    metrics_dict = convert_to_dict(metrics)

    # Export to JSON file
    output_path = Path("output/metrics.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(metrics_dict, f, indent=2)

    context.end_session()


if __name__ == "__main__":
    example_metrics_report()

    example_custom_thresholds()

    example_time_series_analysis()

    example_export_metrics()
