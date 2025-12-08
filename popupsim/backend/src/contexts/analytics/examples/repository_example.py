"""Example demonstrating analytics repository usage."""

import time
from pathlib import Path

from contexts.analytics.application.analytics_context import (
    AnalyticsContext,
)
from contexts.analytics.domain.value_objects.analytics_metrics import (
    Threshold,
)
from contexts.analytics.infrastructure.repositories import (
    AnalyticsRepositoryFactory,
)
from infrastructure.event_bus.event_bus import EventBus


def example_in_memory() -> None:
    """Example using in-memory repository."""

    event_bus = EventBus()
    repository = AnalyticsRepositoryFactory.create("memory")
    analytics = AnalyticsContext(event_bus, repository)

    analytics.start_session("memory_example")
    analytics.record_metric("workshop_1", "wagons_processed", 10)
    analytics.record_metric("workshop_1", "wagons_processed", 20)

    analytics.analyze_session()


def example_csv() -> None:
    """Example using CSV repository."""

    event_bus = EventBus()
    output_dir = Path("output/analytics/csv")
    repository = AnalyticsRepositoryFactory.create("csv", output_dir)
    analytics = AnalyticsContext(event_bus, repository)

    session_id = f"csv_example_{int(time.time())}"
    analytics.start_session(session_id)

    base_time = time.time()
    analytics.record_metric("workshop_1", "wagons_processed", 5, base_time)
    analytics.record_metric("workshop_1", "wagons_processed", 10, base_time + 3600)

    analytics.set_threshold(Threshold("completion_rate", 0.8, 0.5))
    analytics.analyze_session()


def example_json() -> None:
    """Example using JSON repository."""

    event_bus = EventBus()
    output_dir = Path("output/analytics/json")
    repository = AnalyticsRepositoryFactory.create("json", output_dir)
    analytics = AnalyticsContext(event_bus, repository)

    session_id = f"json_example_{int(time.time())}"
    analytics.start_session(session_id)

    analytics.record_metric("workshop_1", "wagons_processed", 25)
    analytics.record_metric("yard_1", "wagons_classified", 55)
    analytics.set_threshold(Threshold("completion_rate", 0.8, 0.5))

    analytics.analyze_session()


def main() -> None:
    """Run all examples."""
    example_in_memory()
    example_csv()
    example_json()


if __name__ == "__main__":
    main()
