"""Tests for locomotive collector."""


from analytics.collectors.locomotive import LocomotiveCollector


def test_locomotive_collector_initialization() -> None:
    """Test LocomotiveCollector initialization."""
    collector = LocomotiveCollector()

    assert len(collector.resource_times) == 0
    assert len(collector.resource_last_event) == 0


def test_record_locomotive_status_change() -> None:
    """Test recording locomotive status change."""
    collector = LocomotiveCollector()

    collector.record_event('locomotive_status_change', {'locomotive_id': 'L001', 'status': 'moving', 'time': 0.0})
    collector.record_event('locomotive_status_change', {'locomotive_id': 'L001', 'status': 'parking', 'time': 100.0})

    assert 'L001' in collector.resource_times
    assert collector.resource_times['L001']['moving'] == 100.0


def test_multiple_locomotives() -> None:
    """Test tracking multiple locomotives."""
    collector = LocomotiveCollector()

    collector.record_event('locomotive_status_change', {'locomotive_id': 'L001', 'status': 'moving', 'time': 0.0})
    collector.record_event('locomotive_status_change', {'locomotive_id': 'L002', 'status': 'parking', 'time': 0.0})
    collector.record_event('locomotive_status_change', {'locomotive_id': 'L001', 'status': 'parking', 'time': 50.0})
    collector.record_event('locomotive_status_change', {'locomotive_id': 'L002', 'status': 'moving', 'time': 30.0})

    assert 'L001' in collector.resource_times
    assert 'L002' in collector.resource_times
    assert collector.resource_times['L001']['moving'] == 50.0
    assert collector.resource_times['L002']['parking'] == 30.0


def test_simulation_end_event() -> None:
    """Test simulation end event finalizes times."""
    collector = LocomotiveCollector()

    collector.record_event('locomotive_status_change', {'locomotive_id': 'L001', 'status': 'moving', 'time': 0.0})
    collector.record_event('simulation_end', {'time': 100.0})

    assert collector.resource_times['L001']['moving'] == 100.0


def test_get_results() -> None:
    """Test getting locomotive utilization results."""
    collector = LocomotiveCollector()

    collector.record_event('locomotive_status_change', {'locomotive_id': 'L001', 'status': 'moving', 'time': 0.0})
    collector.record_event('locomotive_status_change', {'locomotive_id': 'L001', 'status': 'parking', 'time': 60.0})
    collector.record_event('simulation_end', {'time': 100.0})

    results = collector.get_results()

    assert len(results) == 2
    assert any(r.name == 'L001_moving_utilization' and r.value == 60.0 for r in results)
    assert any(r.name == 'L001_parking_utilization' and r.value == 40.0 for r in results)


def test_reset_collector() -> None:
    """Test resetting collector state."""
    collector = LocomotiveCollector()

    collector.record_event('locomotive_status_change', {'locomotive_id': 'L001', 'status': 'moving', 'time': 0.0})
    collector.reset()

    assert len(collector.resource_times) == 0
    assert len(collector.resource_last_event) == 0


def test_metric_categories() -> None:
    """Test that all metrics have correct category."""
    collector = LocomotiveCollector()

    collector.record_event('locomotive_status_change', {'locomotive_id': 'L001', 'status': 'moving', 'time': 0.0})
    collector.record_event('simulation_end', {'time': 100.0})

    results = collector.get_results()

    assert all(r.category == 'locomotive' for r in results)
