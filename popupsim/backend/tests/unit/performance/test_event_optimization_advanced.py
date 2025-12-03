"""Advanced event broadcasting optimizations."""

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


# Option 4: Direct collector dispatch (skip routing dict)
class DirectDispatchMetrics(SimulationMetrics):
    def __init__(self) -> None:
        super().__init__()
        self.wagon_collectors = []
        self.loco_collectors = []
        self.workshop_collectors = []

    def register(self, collector) -> None:
        self.collectors.append(collector)
        if isinstance(collector, WagonCollector):
            self.wagon_collectors.append(collector)
        elif isinstance(collector, LocomotiveCollector):
            self.loco_collectors.append(collector)
        elif isinstance(collector, WorkshopCollector):
            self.workshop_collectors.append(collector)

    def record_event(self, event) -> None:
        if isinstance(event, (WagonDeliveredEvent, WagonRetrofittedEvent)):
            for c in self.wagon_collectors:
                c.record_event(event)
        elif isinstance(event, LocomotiveStatusChangeEvent):
            for c in self.loco_collectors:
                c.record_event(event)
        elif isinstance(event, WorkshopUtilizationChangedEvent):
            for c in self.workshop_collectors:
                c.record_event(event)


# Option 5: Inline processing (no method calls)
class InlineMetrics:
    def __init__(self) -> None:
        self.wagon_start_times = {}
        self.total_flow_time = 0.0
        self.flow_time_count = 0
        self.loco_times = {}
        self.workshop_times = {}

    def record_event(self, event) -> None:
        if isinstance(event, WagonDeliveredEvent):
            self.wagon_start_times[event.wagon_id] = event.timestamp.to_minutes()
        elif isinstance(event, WagonRetrofittedEvent):
            start = self.wagon_start_times.pop(event.wagon_id, None)
            if start:
                self.total_flow_time += event.timestamp.to_minutes() - start
                self.flow_time_count += 1
        elif isinstance(event, LocomotiveStatusChangeEvent):
            self.loco_times[event.locomotive_id] = event.timestamp.to_minutes()
        elif isinstance(event, WorkshopUtilizationChangedEvent):
            self.workshop_times[event.workshop_id] = event.timestamp.to_minutes()


# Option 6: Type-based dispatch (no isinstance)
class TypeDispatchMetrics(SimulationMetrics):
    def record_event(self, event) -> None:
        event_type = type(event)
        collectors = self.collectors_by_event_type.get(event_type)
        if collectors:
            for collector in collectors:
                collector.record_event(event)


def test_baseline_current(benchmark: object) -> None:
    """Baseline: Current with event type routing."""
    metrics = SimulationMetrics()
    metrics.register(WagonCollector())
    metrics.register(LocomotiveCollector())
    metrics.register(WorkshopCollector())

    events = []
    for i in range(2500):
        events.extend(
            [
                WagonDeliveredEvent(EventId.generate(), Timestamp.from_simulation_time(i), 'a', f'w{i}'),
                LocomotiveStatusChangeEvent(
                    EventId.generate(), Timestamp.from_simulation_time(i), 'a', f'l{i}', 'IDLE'
                ),
                WorkshopUtilizationChangedEvent(
                    EventId.generate(), Timestamp.from_simulation_time(i), 'a', f'ws{i}', 50.0, 5
                ),
                WagonRetrofittedEvent(
                    EventId.generate(), Timestamp.from_simulation_time(i + 1), 'a', f'w{i}', f'ws{i}', 30.0
                ),
            ]
        )

    benchmark(lambda: [metrics.record_event(e) for e in events])


def test_direct_dispatch(benchmark: object) -> None:
    """Option 4: Direct isinstance dispatch."""
    metrics = DirectDispatchMetrics()
    metrics.register(WagonCollector())
    metrics.register(LocomotiveCollector())
    metrics.register(WorkshopCollector())

    events = []
    for i in range(2500):
        events.extend(
            [
                WagonDeliveredEvent(EventId.generate(), Timestamp.from_simulation_time(i), 'a', f'w{i}'),
                LocomotiveStatusChangeEvent(
                    EventId.generate(), Timestamp.from_simulation_time(i), 'a', f'l{i}', 'IDLE'
                ),
                WorkshopUtilizationChangedEvent(
                    EventId.generate(), Timestamp.from_simulation_time(i), 'a', f'ws{i}', 50.0, 5
                ),
                WagonRetrofittedEvent(
                    EventId.generate(), Timestamp.from_simulation_time(i + 1), 'a', f'w{i}', f'ws{i}', 30.0
                ),
            ]
        )

    benchmark(lambda: [metrics.record_event(e) for e in events])


def test_inline_processing(benchmark: object) -> None:
    """Option 5: Inline processing (no collectors)."""
    metrics = InlineMetrics()

    events = []
    for i in range(2500):
        events.extend(
            [
                WagonDeliveredEvent(EventId.generate(), Timestamp.from_simulation_time(i), 'a', f'w{i}'),
                LocomotiveStatusChangeEvent(
                    EventId.generate(), Timestamp.from_simulation_time(i), 'a', f'l{i}', 'IDLE'
                ),
                WorkshopUtilizationChangedEvent(
                    EventId.generate(), Timestamp.from_simulation_time(i), 'a', f'ws{i}', 50.0, 5
                ),
                WagonRetrofittedEvent(
                    EventId.generate(), Timestamp.from_simulation_time(i + 1), 'a', f'w{i}', f'ws{i}', 30.0
                ),
            ]
        )

    benchmark(lambda: [metrics.record_event(e) for e in events])


def test_type_dispatch(benchmark: object) -> None:
    """Option 6: Type dispatch without .get() default."""
    metrics = TypeDispatchMetrics()
    metrics.register(WagonCollector())
    metrics.register(LocomotiveCollector())
    metrics.register(WorkshopCollector())

    events = []
    for i in range(2500):
        events.extend(
            [
                WagonDeliveredEvent(EventId.generate(), Timestamp.from_simulation_time(i), 'a', f'w{i}'),
                LocomotiveStatusChangeEvent(
                    EventId.generate(), Timestamp.from_simulation_time(i), 'a', f'l{i}', 'IDLE'
                ),
                WorkshopUtilizationChangedEvent(
                    EventId.generate(), Timestamp.from_simulation_time(i), 'a', f'ws{i}', 50.0, 5
                ),
                WagonRetrofittedEvent(
                    EventId.generate(), Timestamp.from_simulation_time(i + 1), 'a', f'w{i}', f'ws{i}', 30.0
                ),
            ]
        )

    benchmark(lambda: [metrics.record_event(e) for e in events])
