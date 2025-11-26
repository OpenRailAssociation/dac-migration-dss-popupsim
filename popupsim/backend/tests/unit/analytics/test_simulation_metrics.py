"""Tests for simulation metrics registry."""


from analytics.collectors.base import MetricCollector
from analytics.collectors.base import MetricResult
from analytics.collectors.metrics import SimulationMetrics
from analytics.collectors.wagon import WagonCollector


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

    metrics.record_event('wagon_delivered', {'wagon_id': 'W001', 'time': 10.0})

    assert collector.wagons_delivered == 1


def test_record_event_to_multiple_collectors() -> None:
    """Test recording event to multiple collectors."""
    metrics = SimulationMetrics()
    collector1 = WagonCollector()
    collector2 = WagonCollector()
    metrics.register(collector1)
    metrics.register(collector2)

    metrics.record_event('wagon_delivered', {'wagon_id': 'W001', 'time': 10.0})

    assert collector1.wagons_delivered == 1
    assert collector2.wagons_delivered == 1


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

    collector.record_event('wagon_delivered', {'wagon_id': 'W001', 'time': 0.0})
    collector.record_event('wagon_retrofitted', {'wagon_id': 'W001', 'time': 60.0})

    results = metrics.get_results()

    assert 'wagon' in results
    assert len(results['wagon']) == 4
    assert results['wagon'][0]['name'] == 'wagons_delivered'
    assert results['wagon'][0]['value'] == 1


def test_get_results_grouped_by_category() -> None:
    """Test that results are grouped by category."""
    metrics = SimulationMetrics()
    collector = WagonCollector()
    metrics.register(collector)

    collector.record_event('wagon_delivered', {'wagon_id': 'W001', 'time': 0.0})

    results = metrics.get_results()

    assert 'wagon' in results
    assert all('name' in m and 'value' in m and 'unit' in m for m in results['wagon'])


def test_reset_all_collectors() -> None:
    """Test resetting all collectors."""
    metrics = SimulationMetrics()
    collector1 = WagonCollector()
    collector2 = WagonCollector()
    metrics.register(collector1)
    metrics.register(collector2)

    collector1.record_event('wagon_delivered', {'wagon_id': 'W001', 'time': 10.0})
    collector2.record_event('wagon_delivered', {'wagon_id': 'W002', 'time': 20.0})

    metrics.reset()

    assert collector1.wagons_delivered == 0
    assert collector2.wagons_delivered == 0


def test_get_results_format() -> None:
    """Test that results are in correct format."""
    metrics = SimulationMetrics()
    collector = WagonCollector()
    metrics.register(collector)

    collector.record_event('wagon_delivered', {'wagon_id': 'W001', 'time': 0.0})

    results = metrics.get_results()

    for category, metric_list in results.items():
        assert isinstance(category, str)
        assert isinstance(metric_list, list)
        for metric in metric_list:
            assert 'name' in metric
            assert 'value' in metric
            assert 'unit' in metric


def test_multiple_categories() -> None:
    """Test handling multiple metric categories."""

    class CustomCollector(MetricCollector):
        def record_event(self, event_type: str, data: dict) -> None:
            pass

        def get_results(self) -> list[MetricResult]:
            return [
                MetricResult('metric1', 10, 'units', 'category1'),
                MetricResult('metric2', 20, 'units', 'category2'),
            ]

        def reset(self) -> None:
            pass

    metrics = SimulationMetrics()
    metrics.register(CustomCollector())

    results = metrics.get_results()

    assert 'category1' in results
    assert 'category2' in results
    assert len(results['category1']) == 1
    assert len(results['category2']) == 1
