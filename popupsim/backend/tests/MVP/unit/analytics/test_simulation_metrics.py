"""Tests for simulation metrics registry."""

from popupsim.backend.src.MVP.analytics.application.metrics_aggregator import (
    SimulationMetrics,
)
from popupsim.backend.src.MVP.analytics.domain.collectors.base import (
    MetricCollector,
    MetricResult,
)
from popupsim.backend.src.MVP.analytics.domain.collectors.wagon_collector import (
    WagonCollector,
)
from popupsim.backend.src.MVP.analytics.domain.events.base_event import DomainEvent
from popupsim.backend.src.MVP.analytics.domain.events.simulation_events import (
    WagonDeliveredEvent,
    WagonRetrofittedEvent,
)
from popupsim.backend.src.MVP.analytics.domain.value_objects.metric_value import (
    MetricValue,
)
from popupsim.backend.src.MVP.analytics.domain.value_objects.timestamp import Timestamp


def test_simulation_metrics_initialization() -> None:
    """Test SimulationMetrics initialization."""
    metrics = SimulationMetrics()

    assert len(metrics.collectors) == 0


def test_register_collector() -> None:
    """Test registering a collector."""
    metrics = SimulationMetrics()
    collector = WagonCollector()

    metrics.register(collector)

    assert len(metrics.collectors) == 1
    assert metrics.collectors[0] is collector


def test_register_multiple_collectors() -> None:
    """Test registering multiple collectors."""
    metrics = SimulationMetrics()
    collector1 = WagonCollector()
    collector2 = WagonCollector()

    metrics.register(collector1)
    metrics.register(collector2)

    assert len(metrics.collectors) == 2


def test_record_event_to_single_collector() -> None:
    """Test recording event to single collector."""
    metrics = SimulationMetrics()
    collector = WagonCollector()
    metrics.register(collector)

    event = WagonDeliveredEvent.create(
        Timestamp.from_simulation_time(10.0), wagon_id="W001"
    )
    metrics.record_event(event)

    assert "W001" in collector.wagon_start_times


def test_record_event_to_multiple_collectors() -> None:
    """Test recording event to multiple collectors."""
    metrics = SimulationMetrics()
    collector1 = WagonCollector()
    collector2 = WagonCollector()
    metrics.register(collector1)
    metrics.register(collector2)

    event = WagonDeliveredEvent.create(
        Timestamp.from_simulation_time(10.0), wagon_id="W001"
    )
    metrics.record_event(event)

    assert "W001" in collector1.wagon_start_times
    assert "W001" in collector2.wagon_start_times


def test_get_results_empty() -> None:
    """Test getting results with no collectors."""
    metrics = SimulationMetrics()

    results = metrics.get_results()

    assert results == {}


def test_get_results_single_collector() -> None:
    """Test getting results from single collector."""
    metrics = SimulationMetrics()
    collector = WagonCollector()
    metrics.register(collector)

    delivered_event = WagonDeliveredEvent.create(
        Timestamp.from_simulation_time(0.0), wagon_id="W001"
    )
    retrofitted_event = WagonRetrofittedEvent.create(
        Timestamp.from_simulation_time(60.0),
        wagon_id="W001",
        workshop_id="WS001",
        processing_duration=60.0,
    )

    collector.record_event(delivered_event)
    collector.record_event(retrofitted_event)

    results = metrics.get_results()

    assert "wagon" in results
    assert len(results["wagon"]) == 2
    assert results["wagon"][0]["name"] == "avg_flow_time"
    assert results["wagon"][0]["value"] == 60.0


def test_get_results_grouped_by_category() -> None:
    """Test that results are grouped by category."""
    metrics = SimulationMetrics()
    collector = WagonCollector()
    metrics.register(collector)

    event = WagonDeliveredEvent.create(
        Timestamp.from_simulation_time(0.0), wagon_id="W001"
    )
    collector.record_event(event)

    results = metrics.get_results()

    assert "wagon" in results
    assert all("name" in m and "value" in m and "unit" in m for m in results["wagon"])


def test_reset_all_collectors() -> None:
    """Test resetting all collectors."""
    metrics = SimulationMetrics()
    collector1 = WagonCollector()
    collector2 = WagonCollector()
    metrics.register(collector1)
    metrics.register(collector2)

    event1 = WagonDeliveredEvent.create(
        Timestamp.from_simulation_time(10.0), wagon_id="W001"
    )
    event2 = WagonDeliveredEvent.create(
        Timestamp.from_simulation_time(20.0), wagon_id="W002"
    )

    collector1.record_event(event1)
    collector2.record_event(event2)

    metrics.reset()

    assert len(collector1.wagon_start_times) == 0
    assert len(collector2.wagon_start_times) == 0


def test_get_results_format() -> None:
    """Test that results are in correct format."""
    metrics = SimulationMetrics()
    collector = WagonCollector()
    metrics.register(collector)

    event = WagonDeliveredEvent.create(
        Timestamp.from_simulation_time(0.0), wagon_id="W001"
    )
    collector.record_event(event)

    results = metrics.get_results()

    for category, metric_list in results.items():
        assert isinstance(category, str)
        assert isinstance(metric_list, list)
        for metric in metric_list:
            assert "name" in metric
            assert "value" in metric
            assert "unit" in metric


def test_multiple_categories() -> None:
    """Test handling multiple metric categories."""

    class CustomCollector(MetricCollector):
        def record_event(self, event: DomainEvent) -> None:
            pass

        def get_results(self) -> list[MetricResult]:
            return [
                MetricResult("metric1", MetricValue(10, "units"), "category1"),
                MetricResult("metric2", MetricValue(20, "units"), "category2"),
            ]

        def reset(self) -> None:
            pass

    metrics = SimulationMetrics()
    metrics.register(CustomCollector())

    results = metrics.get_results()

    assert "category1" in results
    assert "category2" in results
    assert len(results["category1"]) == 1
    assert len(results["category2"]) == 1
