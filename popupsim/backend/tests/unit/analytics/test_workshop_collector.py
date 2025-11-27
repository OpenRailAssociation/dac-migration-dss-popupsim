"""Tests for workshop collector."""

from analytics.domain.collectors.workshop_collector import WorkshopCollector
from analytics.domain.events.simulation_events import WorkshopUtilizationChangedEvent
from analytics.domain.value_objects.event_id import EventId
from analytics.domain.value_objects.timestamp import Timestamp


def test_workshop_collector_initialization() -> None:
    """Test WorkshopCollector initialization."""
    collector = WorkshopCollector()

    assert len(collector.station_usage) == 0
    assert len(collector.active_time) == 0
    assert len(collector.idle_time) == 0
    assert len(collector.last_event) == 0


def test_record_workshop_station_occupied() -> None:
    """Test recording workshop station occupied event."""
    collector = WorkshopCollector()

    event = WorkshopUtilizationChangedEvent(
        event_id=EventId.generate(),
        timestamp=Timestamp.from_simulation_time(0.0),
        workshop_id='WS001',
        utilization_percent=50.0,
        available_stations=2,
    )
    collector.record_event(event)

    assert 'WS001' in collector.last_event
    assert collector.last_event['WS001'] == (0.0, 2)


def test_idle_time() -> None:
    """Test tracking workshop idle time."""
    collector = WorkshopCollector()

    events = [
        WorkshopUtilizationChangedEvent(
            EventId.generate(),
            Timestamp.from_simulation_time(0.0),
            workshop_id='WS001',
            utilization_percent=0.0,
            available_stations=0,
        ),
        WorkshopUtilizationChangedEvent(
            EventId.generate(),
            Timestamp.from_simulation_time(30.0),
            workshop_id='WS001',
            utilization_percent=50.0,
            available_stations=1,
        ),
    ]

    for event in events:
        collector.record_event(event)

    assert collector.idle_time.get('WS001', 0.0) == 30.0


def test_multiple_workshops() -> None:
    """Test tracking multiple workshops."""
    collector = WorkshopCollector()

    events = [
        WorkshopUtilizationChangedEvent(
            EventId.generate(),
            Timestamp.from_simulation_time(0.0),
            workshop_id='WS001',
            utilization_percent=0.0,
            available_stations=0,
        ),
        WorkshopUtilizationChangedEvent(
            EventId.generate(),
            Timestamp.from_simulation_time(5.0),
            workshop_id='WS002',
            utilization_percent=25.0,
            available_stations=1,
        ),
    ]

    for event in events:
        collector.record_event(event)

    assert len(collector.last_event) == 2
    assert 'WS001' in collector.last_event
    assert 'WS002' in collector.last_event


def test_simulation_end_event() -> None:
    """Test handling simulation end."""
    collector = WorkshopCollector()

    event = WorkshopUtilizationChangedEvent(
        EventId.generate(),
        Timestamp.from_simulation_time(0.0),
        workshop_id='WS001',
        utilization_percent=50.0,
        available_stations=1,
    )
    collector.record_event(event)

    # Simulate end by recording final state
    end_event = WorkshopUtilizationChangedEvent(
        EventId.generate(),
        Timestamp.from_simulation_time(60.0),
        workshop_id='WS001',
        utilization_percent=0.0,
        available_stations=0,
    )
    collector.record_event(end_event)

    assert collector.active_time.get('WS001', 0.0) == 60.0


def test_get_results() -> None:
    """Test getting workshop utilization results."""
    collector = WorkshopCollector()

    events = [
        WorkshopUtilizationChangedEvent(
            EventId.generate(),
            Timestamp.from_simulation_time(0.0),
            workshop_id='WS001',
            utilization_percent=0.0,
            available_stations=0,
        ),
        WorkshopUtilizationChangedEvent(
            EventId.generate(),
            Timestamp.from_simulation_time(30.0),
            workshop_id='WS001',
            utilization_percent=50.0,
            available_stations=1,
        ),
        WorkshopUtilizationChangedEvent(
            EventId.generate(),
            Timestamp.from_simulation_time(60.0),
            workshop_id='WS001',
            utilization_percent=0.0,
            available_stations=0,
        ),
    ]

    for event in events:
        collector.record_event(event)

    results = collector.get_results()

    assert len(results) >= 2
    assert any('utilization' in r.name for r in results)
    assert any('idle_time' in r.name for r in results)


def test_reset_collector() -> None:
    """Test resetting collector state."""
    collector = WorkshopCollector()

    event = WorkshopUtilizationChangedEvent(
        EventId.generate(),
        Timestamp.from_simulation_time(0.0),
        workshop_id='WS001',
        utilization_percent=50.0,
        available_stations=1,
    )
    collector.record_event(event)

    collector.reset()

    assert len(collector.station_usage) == 0
    assert len(collector.active_time) == 0
    assert len(collector.idle_time) == 0
    assert len(collector.last_event) == 0


def test_metric_categories() -> None:
    """Test that all metrics have correct category."""
    collector = WorkshopCollector()

    events = [
        WorkshopUtilizationChangedEvent(
            EventId.generate(),
            Timestamp.from_simulation_time(0.0),
            workshop_id='WS001',
            utilization_percent=0.0,
            available_stations=0,
        ),
        WorkshopUtilizationChangedEvent(
            EventId.generate(),
            Timestamp.from_simulation_time(60.0),
            workshop_id='WS001',
            utilization_percent=0.0,
            available_stations=0,
        ),
    ]

    for event in events:
        collector.record_event(event)

    results = collector.get_results()

    assert all(r.category == 'workshop' for r in results)
