"""Example usage of metrics output feature."""

from pathlib import Path
from typing import Any

from contexts.analytics.application.services.metrics_output_service import (
    MetricsOutputService,
)
from contexts.analytics.domain.services.event_aggregator import (
    EventAggregator,
)
from contexts.analytics.domain.services.metrics_query_service import (
    MetricsQueryService,
)


def example_usage() -> None:
    """Demonstrate metrics output usage."""

    # 1. Create aggregator
    aggregator = EventAggregator()

    # 2. Simulate events (in real usage, these come from event bus)
    mock_events = create_mock_events()

    for event in mock_events:
        aggregator.aggregate_event(event)

    # 3. Get statistics
    stats = aggregator.get_statistics()

    # 4. Create query service
    query_service = MetricsQueryService(stats)

    # 5. Query metrics
    query_service.get_train_arrivals()

    query_service.get_wagon_metrics()

    for _util in query_service.get_all_locomotive_utilizations().values():
        pass

    for _metrics in query_service.get_all_workshop_metrics().values():
        pass

    bottlenecks = query_service.detect_bottlenecks(
        over_threshold=90.0, under_threshold=20.0
    )
    if bottlenecks:
        for _bottleneck in bottlenecks:
            pass
    else:
        pass

    # 6. Export metrics
    output_service = MetricsOutputService(query_service)

    output_dir = Path("output/metrics_example")

    output_service.export_to_csv(output_dir)

    output_service.export_to_json(output_dir / "summary.json")

    # 7. Generate summary report
    output_service.generate_summary_report()


def create_mock_events() -> list[Any]:
    """Create mock events for demonstration."""
    from dataclasses import dataclass

    @dataclass
    class TrainArrivedEvent:
        timestamp: float
        wagon_count: int

    @dataclass
    class WagonRetrofittedEvent:
        timestamp: float

    @dataclass
    class WagonRejectedEvent:
        timestamp: float

    @dataclass
    class LocomotiveMovingEvent:
        locomotive_id: str
        duration: float
        timestamp: float

    @dataclass
    class LocomotiveParkingEvent:
        locomotive_id: str
        duration: float
        timestamp: float

    @dataclass
    class RetrofitCompletedEvent:
        workshop_id: str
        timestamp: float

    @dataclass
    class WorkshopWorkingEvent:
        workshop_id: str
        duration: float
        timestamp: float

    @dataclass
    class WorkshopWaitingEvent:
        workshop_id: str
        duration: float
        timestamp: float

    @dataclass
    class TrackCapacityChangedEvent:
        track_id: str
        used_capacity: int
        total_capacity: int
        timestamp: float

    return [
        # Train arrivals
        TrainArrivedEvent(timestamp=0.0, wagon_count=10),
        TrainArrivedEvent(timestamp=100.0, wagon_count=15),
        TrainArrivedEvent(timestamp=200.0, wagon_count=12),
        # Wagon events
        WagonRetrofittedEvent(timestamp=50.0),
        WagonRetrofittedEvent(timestamp=60.0),
        WagonRetrofittedEvent(timestamp=70.0),
        WagonRejectedEvent(timestamp=55.0),
        # Locomotive events
        LocomotiveMovingEvent(locomotive_id="loco_1", duration=30.0, timestamp=10.0),
        LocomotiveParkingEvent(locomotive_id="loco_1", duration=70.0, timestamp=40.0),
        LocomotiveMovingEvent(locomotive_id="loco_2", duration=80.0, timestamp=15.0),
        LocomotiveParkingEvent(locomotive_id="loco_2", duration=20.0, timestamp=95.0),
        # Workshop events
        RetrofitCompletedEvent(workshop_id="workshop_1", timestamp=50.0),
        RetrofitCompletedEvent(workshop_id="workshop_1", timestamp=60.0),
        WorkshopWorkingEvent(workshop_id="workshop_1", duration=80.0, timestamp=20.0),
        WorkshopWaitingEvent(workshop_id="workshop_1", duration=20.0, timestamp=100.0),
        RetrofitCompletedEvent(workshop_id="workshop_2", timestamp=70.0),
        WorkshopWorkingEvent(workshop_id="workshop_2", duration=50.0, timestamp=30.0),
        WorkshopWaitingEvent(workshop_id="workshop_2", duration=50.0, timestamp=80.0),
        # Track capacity events
        TrackCapacityChangedEvent(
            track_id="track_1", used_capacity=5, total_capacity=10, timestamp=25.0
        ),
        TrackCapacityChangedEvent(
            track_id="track_1", used_capacity=8, total_capacity=10, timestamp=50.0
        ),
        TrackCapacityChangedEvent(
            track_id="track_1", used_capacity=10, total_capacity=10, timestamp=75.0
        ),
    ]


if __name__ == "__main__":
    example_usage()
