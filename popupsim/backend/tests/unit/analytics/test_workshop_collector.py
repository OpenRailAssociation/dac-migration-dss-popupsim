"""Tests for workshop collector."""


from analytics.domain.collectors.workshop_collector import WorkshopCollector


def test_workshop_collector_initialization() -> None:
    """Test WorkshopCollector initialization."""
    collector = WorkshopCollector()

    assert len(collector.workshop_station_usage) == 0
    assert len(collector.workshop_active_time) == 0
    assert len(collector.workshop_idle_time) == 0


def test_record_workshop_station_occupied() -> None:
    """Test recording workshop station occupation."""
    collector = WorkshopCollector()

    collector.record_event('workshop_station_occupied', {'workshop_id': 'WS001', 'stations_used': 5, 'time': 0.0})
    collector.record_event('workshop_station_occupied', {'workshop_id': 'WS001', 'stations_used': 0, 'time': 100.0})

    assert 'WS001' in collector.workshop_active_time
    assert collector.workshop_active_time['WS001'] == 100.0


def test_workshop_idle_time() -> None:
    """Test tracking workshop idle time."""
    collector = WorkshopCollector()

    collector.record_event('workshop_station_occupied', {'workshop_id': 'WS001', 'stations_used': 0, 'time': 0.0})
    collector.record_event('workshop_station_occupied', {'workshop_id': 'WS001', 'stations_used': 5, 'time': 50.0})

    assert 'WS001' in collector.workshop_idle_time
    assert collector.workshop_idle_time['WS001'] == 50.0


def test_multiple_workshops() -> None:
    """Test tracking multiple workshops."""
    collector = WorkshopCollector()

    collector.record_event('workshop_station_occupied', {'workshop_id': 'WS001', 'stations_used': 5, 'time': 0.0})
    collector.record_event('workshop_station_occupied', {'workshop_id': 'WS002', 'stations_used': 3, 'time': 0.0})
    collector.record_event('workshop_station_occupied', {'workshop_id': 'WS001', 'stations_used': 0, 'time': 60.0})
    collector.record_event('workshop_station_occupied', {'workshop_id': 'WS002', 'stations_used': 0, 'time': 40.0})

    assert 'WS001' in collector.workshop_active_time
    assert 'WS002' in collector.workshop_active_time
    assert collector.workshop_active_time['WS001'] == 60.0
    assert collector.workshop_active_time['WS002'] == 40.0


def test_simulation_end_event() -> None:
    """Test simulation end event finalizes times."""
    collector = WorkshopCollector()

    collector.record_event('workshop_station_occupied', {'workshop_id': 'WS001', 'stations_used': 5, 'time': 0.0})
    collector.record_event('simulation_end', {'time': 100.0})

    assert collector.workshop_active_time['WS001'] == 100.0


def test_get_results() -> None:
    """Test getting workshop utilization results."""
    collector = WorkshopCollector()

    collector.record_event('workshop_station_occupied', {'workshop_id': 'WS001', 'stations_used': 5, 'time': 0.0})
    collector.record_event('workshop_station_occupied', {'workshop_id': 'WS001', 'stations_used': 0, 'time': 60.0})
    collector.record_event('simulation_end', {'time': 100.0})

    results = collector.get_results()

    assert len(results) == 2
    assert any(r.name == 'WS001_utilization' and r.value == 60.0 for r in results)
    assert any(r.name == 'WS001_idle_time' for r in results)


def test_reset_collector() -> None:
    """Test resetting collector state."""
    collector = WorkshopCollector()

    collector.record_event('workshop_station_occupied', {'workshop_id': 'WS001', 'stations_used': 5, 'time': 0.0})
    collector.reset()

    assert len(collector.workshop_active_time) == 0
    assert len(collector.workshop_idle_time) == 0
    assert len(collector.workshop_last_event) == 0


def test_metric_categories() -> None:
    """Test that all metrics have correct category."""
    collector = WorkshopCollector()

    collector.record_event('workshop_station_occupied', {'workshop_id': 'WS001', 'stations_used': 5, 'time': 0.0})
    collector.record_event('simulation_end', {'time': 100.0})

    results = collector.get_results()

    assert all(r.category == 'workshop' for r in results)
