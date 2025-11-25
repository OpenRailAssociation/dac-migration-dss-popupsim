"""Tests for wagon collector."""


from analytics.domain.collectors.wagon_collector import WagonCollector


def test_wagon_collector_initialization() -> None:
    """Test WagonCollector initialization."""
    collector = WagonCollector()

    assert collector.wagons_delivered == 0
    assert collector.wagons_retrofitted == 0
    assert collector.wagons_rejected == 0
    assert collector.total_flow_time == 0.0
    assert len(collector.wagon_start_times) == 0


def test_record_wagon_delivered() -> None:
    """Test recording wagon delivered event."""
    collector = WagonCollector()

    collector.record_event('wagon_delivered', {'wagon_id': 'W001', 'time': 10.0})

    assert collector.wagons_delivered == 1
    assert 'W001' in collector.wagon_start_times
    assert collector.wagon_start_times['W001'] == 10.0


def test_record_wagon_retrofitted() -> None:
    """Test recording wagon retrofitted event."""
    collector = WagonCollector()

    collector.record_event('wagon_delivered', {'wagon_id': 'W001', 'time': 10.0})
    collector.record_event('wagon_retrofitted', {'wagon_id': 'W001', 'time': 50.0})

    assert collector.wagons_retrofitted == 1
    assert collector.total_flow_time == 40.0


def test_record_wagon_rejected() -> None:
    """Test recording wagon rejected event."""
    collector = WagonCollector()

    collector.record_event('wagon_rejected', {'wagon_id': 'W001'})

    assert collector.wagons_rejected == 1


def test_multiple_wagon_flow() -> None:
    """Test tracking multiple wagons through the system."""
    collector = WagonCollector()

    collector.record_event('wagon_delivered', {'wagon_id': 'W001', 'time': 0.0})
    collector.record_event('wagon_delivered', {'wagon_id': 'W002', 'time': 5.0})
    collector.record_event('wagon_retrofitted', {'wagon_id': 'W001', 'time': 30.0})
    collector.record_event('wagon_retrofitted', {'wagon_id': 'W002', 'time': 45.0})

    assert collector.wagons_delivered == 2
    assert collector.wagons_retrofitted == 2
    assert collector.total_flow_time == 70.0


def test_get_results_with_no_data() -> None:
    """Test getting results with no recorded events."""
    collector = WagonCollector()

    results = collector.get_results()

    assert len(results) == 4
    assert results[0].name == 'wagons_delivered'
    assert results[0].value == 0
    assert results[1].name == 'wagons_retrofitted'
    assert results[1].value == 0
    assert results[2].name == 'wagons_rejected'
    assert results[2].value == 0
    assert results[3].name == 'avg_flow_time'
    assert results[3].value == 0.0


def test_get_results_with_data() -> None:
    """Test getting results with recorded events."""
    collector = WagonCollector()

    collector.record_event('wagon_delivered', {'wagon_id': 'W001', 'time': 0.0})
    collector.record_event('wagon_delivered', {'wagon_id': 'W002', 'time': 10.0})
    collector.record_event('wagon_retrofitted', {'wagon_id': 'W001', 'time': 60.0})
    collector.record_event('wagon_retrofitted', {'wagon_id': 'W002', 'time': 80.0})
    collector.record_event('wagon_rejected', {'wagon_id': 'W003'})

    results = collector.get_results()

    assert len(results) == 4
    assert results[0].value == 2
    assert results[1].value == 2
    assert results[2].value == 1
    assert results[3].value == 65.0


def test_avg_flow_time_calculation() -> None:
    """Test average flow time calculation."""
    collector = WagonCollector()

    collector.record_event('wagon_delivered', {'wagon_id': 'W001', 'time': 0.0})
    collector.record_event('wagon_delivered', {'wagon_id': 'W002', 'time': 0.0})
    collector.record_event('wagon_delivered', {'wagon_id': 'W003', 'time': 0.0})
    collector.record_event('wagon_retrofitted', {'wagon_id': 'W001', 'time': 30.0})
    collector.record_event('wagon_retrofitted', {'wagon_id': 'W002', 'time': 60.0})
    collector.record_event('wagon_retrofitted', {'wagon_id': 'W003', 'time': 90.0})

    results = collector.get_results()
    avg_flow_time = next(r for r in results if r.name == 'avg_flow_time')

    assert avg_flow_time.value == 60.0
    assert avg_flow_time.unit == 'min'


def test_reset_collector() -> None:
    """Test resetting collector state."""
    collector = WagonCollector()

    collector.record_event('wagon_delivered', {'wagon_id': 'W001', 'time': 10.0})
    collector.record_event('wagon_retrofitted', {'wagon_id': 'W001', 'time': 50.0})
    collector.record_event('wagon_rejected', {'wagon_id': 'W002'})

    collector.reset()

    assert collector.wagons_delivered == 0
    assert collector.wagons_retrofitted == 0
    assert collector.wagons_rejected == 0
    assert collector.total_flow_time == 0.0
    assert len(collector.wagon_start_times) == 0


def test_unknown_event_type() -> None:
    """Test handling unknown event types."""
    collector = WagonCollector()

    collector.record_event('unknown_event', {'data': 'test'})

    results = collector.get_results()
    assert all(r.value == 0 or r.value == 0.0 for r in results)


def test_wagon_retrofitted_without_delivery() -> None:
    """Test retrofitted event without prior delivery event."""
    collector = WagonCollector()

    collector.record_event('wagon_retrofitted', {'wagon_id': 'W001', 'time': 50.0})

    assert collector.wagons_retrofitted == 1
    assert collector.total_flow_time == 0.0


def test_metric_result_categories() -> None:
    """Test that all metrics have correct category."""
    collector = WagonCollector()
    collector.record_event('wagon_delivered', {'wagon_id': 'W001', 'time': 0.0})

    results = collector.get_results()

    assert all(r.category == 'wagon' for r in results)


def test_metric_result_units() -> None:
    """Test that metrics have correct units."""
    collector = WagonCollector()

    results = collector.get_results()

    assert results[0].unit == 'wagons'
    assert results[1].unit == 'wagons'
    assert results[2].unit == 'wagons'
    assert results[3].unit == 'min'
