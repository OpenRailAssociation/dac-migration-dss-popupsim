"""Benchmark event broadcasting performance."""

from analytics.application.metrics_aggregator import SimulationMetrics
from analytics.domain.collectors.locomotive_collector import LocomotiveCollector
from analytics.domain.collectors.wagon_collector import WagonCollector
from analytics.domain.collectors.workshop_collector import WorkshopCollector
from analytics.domain.events.locomotive_events import LocomotiveStatusChangeEvent
from analytics.domain.events.simulation_events import WagonDeliveredEvent
from analytics.domain.events.simulation_events import WagonRetrofittedEvent
from analytics.domain.events.simulation_events import WorkshopUtilizationChangedEvent
from analytics.domain.value_objects.event_id import EventId
from analytics.domain.value_objects.timestamp import Timestamp


def test_event_broadcasting_small(benchmark: object) -> None:
    """Benchmark small scenario: 3 collectors, 100 events."""
    metrics = SimulationMetrics()
    metrics.register(WagonCollector())
    metrics.register(LocomotiveCollector())
    metrics.register(WorkshopCollector())

    events = []
    for i in range(25):
        events.extend(
            [
                WagonDeliveredEvent(EventId.generate(), Timestamp.from_simulation_time(i * 1.0), 'analytics', 'w1'),
                LocomotiveStatusChangeEvent(
                    EventId.generate(), Timestamp.from_simulation_time(i * 1.0), 'analytics', 'l1', 'IDLE'
                ),
                WorkshopUtilizationChangedEvent(
                    EventId.generate(), Timestamp.from_simulation_time(i * 1.0), 'analytics', 'ws1', 50.0, 5
                ),
                WagonRetrofittedEvent(
                    EventId.generate(), Timestamp.from_simulation_time(i * 1.5), 'analytics', 'w1', 'ws1', 30.0
                ),
            ]
        )

    def run() -> None:
        for event in events:
            metrics.record_event(event)

    benchmark(run)


def test_event_broadcasting_medium(benchmark: object) -> None:
    """Benchmark medium scenario: 3 collectors, 1000 events."""
    metrics = SimulationMetrics()
    metrics.register(WagonCollector())
    metrics.register(LocomotiveCollector())
    metrics.register(WorkshopCollector())

    events = []
    for i in range(250):
        events.extend(
            [
                WagonDeliveredEvent(EventId.generate(), Timestamp.from_simulation_time(i * 1.0), 'analytics', f'w{i}'),
                LocomotiveStatusChangeEvent(
                    EventId.generate(), Timestamp.from_simulation_time(i * 1.0), 'analytics', f'l{i}', 'IDLE'
                ),
                WorkshopUtilizationChangedEvent(
                    EventId.generate(), Timestamp.from_simulation_time(i * 1.0), 'analytics', f'ws{i}', 50.0, 5
                ),
                WagonRetrofittedEvent(
                    EventId.generate(), Timestamp.from_simulation_time(i * 1.5), 'analytics', f'w{i}', f'ws{i}', 30.0
                ),
            ]
        )

    def run() -> None:
        for event in events:
            metrics.record_event(event)

    benchmark(run)


def test_event_broadcasting_large(benchmark: object) -> None:
    """Benchmark large scenario: 3 collectors, 10000 events."""
    metrics = SimulationMetrics()
    metrics.register(WagonCollector())
    metrics.register(LocomotiveCollector())
    metrics.register(WorkshopCollector())

    events = []
    for i in range(2500):
        events.extend(
            [
                WagonDeliveredEvent(EventId.generate(), Timestamp.from_simulation_time(i * 1.0), 'analytics', f'w{i}'),
                LocomotiveStatusChangeEvent(
                    EventId.generate(), Timestamp.from_simulation_time(i * 1.0), 'analytics', f'l{i}', 'IDLE'
                ),
                WorkshopUtilizationChangedEvent(
                    EventId.generate(), Timestamp.from_simulation_time(i * 1.0), 'analytics', f'ws{i}', 50.0, 5
                ),
                WagonRetrofittedEvent(
                    EventId.generate(), Timestamp.from_simulation_time(i * 1.5), 'analytics', f'w{i}', f'ws{i}', 30.0
                ),
            ]
        )

    def run() -> None:
        for event in events:
            metrics.record_event(event)

    benchmark(run)
