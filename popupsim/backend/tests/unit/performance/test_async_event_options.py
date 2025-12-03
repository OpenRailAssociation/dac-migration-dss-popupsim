"""Benchmark async event broadcasting options."""

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


# Option 1: Queue-based (deferred processing)
class QueuedMetrics(SimulationMetrics):
    def __init__(self) -> None:
        super().__init__()
        self.event_queue: list = []

    def record_event(self, event) -> None:
        self.event_queue.append(event)

    def process_events(self) -> None:
        for event in self.event_queue:
            event_type = type(event)
            for collector in self.collectors_by_event_type.get(event_type, []):
                collector.record_event(event)
        self.event_queue.clear()


# Option 2: Batch processing
class BatchedMetrics(SimulationMetrics):
    def __init__(self, batch_size: int = 100) -> None:
        super().__init__()
        self.event_queue: list = []
        self.batch_size = batch_size

    def record_event(self, event) -> None:
        self.event_queue.append(event)
        if len(self.event_queue) >= self.batch_size:
            self._flush()

    def _flush(self) -> None:
        for event in self.event_queue:
            event_type = type(event)
            for collector in self.collectors_by_event_type.get(event_type, []):
                collector.record_event(event)
        self.event_queue.clear()


# Option 3: Current synchronous (baseline)
# Already implemented in SimulationMetrics


def test_sync_baseline_large(benchmark: object) -> None:
    """Baseline: Current synchronous implementation."""
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


def test_queued_large(benchmark: object) -> None:
    """Option 1: Queue events, process after simulation."""
    metrics = QueuedMetrics()
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
        metrics.process_events()

    benchmark(run)


def test_batched_large(benchmark: object) -> None:
    """Option 2: Batch processing (flush every 100 events)."""
    metrics = BatchedMetrics(batch_size=100)
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
        metrics._flush()

    benchmark(run)
