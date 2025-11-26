"""Tests for locomotive collector."""

from analytics.domain.collectors.locomotive_collector import LocomotiveCollector
from analytics.domain.events.locomotive_events import LocomotiveStatusChangeEvent
from analytics.domain.value_objects.event_id import EventId
from analytics.domain.value_objects.timestamp import Timestamp


def test_locomotive_collector_initialization() -> None:
    """Test LocomotiveCollector initialization."""
    collector = LocomotiveCollector()

    assert collector.category == 'locomotive'
    assert len(collector.resource_times) == 0
    assert len(collector.resource_last_event) == 0


def test_record_locomotive_status_change() -> None:
    """Test recording locomotive status change."""
    collector = LocomotiveCollector()

    event = LocomotiveStatusChangeEvent(
        event_id=EventId.generate(),
        timestamp=Timestamp.from_simulation_time(0.0),
        locomotive_id='L001',
        status='moving',
    )
    collector.record_event(event)

    assert 'L001' in collector.resource_last_event
    assert collector.resource_last_event['L001'] == (0.0, 'moving')


def test_multiple_locomotives() -> None:
    """Test tracking multiple locomotives."""
    collector = LocomotiveCollector()

    events = [
        LocomotiveStatusChangeEvent(EventId.generate(), Timestamp.from_simulation_time(0.0), 'L001', 'idle'),
        LocomotiveStatusChangeEvent(EventId.generate(), Timestamp.from_simulation_time(5.0), 'L002', 'moving'),
        LocomotiveStatusChangeEvent(EventId.generate(), Timestamp.from_simulation_time(10.0), 'L001', 'moving'),
    ]

    for event in events:
        collector.record_event(event)

    assert len(collector.resource_last_event) == 2
    assert collector.resource_last_event['L001'] == (10.0, 'moving')
    assert collector.resource_last_event['L002'] == (5.0, 'moving')


def test_simulation_end_event() -> None:
    """Test finalizing times at simulation end."""
    collector = LocomotiveCollector()

    event = LocomotiveStatusChangeEvent(EventId.generate(), Timestamp.from_simulation_time(0.0), 'L001', 'idle')
    collector.record_event(event)

    collector._finalize_times(60.0)

    assert 'L001' in collector.resource_times
    assert collector.resource_times['L001']['idle'] == 60.0


def test_get_results() -> None:
    """Test getting utilization results."""
    collector = LocomotiveCollector()

    events = [
        LocomotiveStatusChangeEvent(EventId.generate(), Timestamp.from_simulation_time(0.0), 'L001', 'idle'),
        LocomotiveStatusChangeEvent(EventId.generate(), Timestamp.from_simulation_time(30.0), 'L001', 'moving'),
    ]

    for event in events:
        collector.record_event(event)

    collector._finalize_times(60.0)
    results = collector.get_results()

    assert len(results) == 2
    assert any(r.name == 'L001_idle_utilization' for r in results)
    assert any(r.name == 'L001_moving_utilization' for r in results)


def test_reset_collector() -> None:
    """Test resetting collector state."""
    collector = LocomotiveCollector()

    event = LocomotiveStatusChangeEvent(EventId.generate(), Timestamp.from_simulation_time(0.0), 'L001', 'idle')
    collector.record_event(event)

    collector.reset()

    assert len(collector.resource_times) == 0
    assert len(collector.resource_last_event) == 0


def test_metric_categories() -> None:
    """Test that all metrics have correct category."""
    collector = LocomotiveCollector()

    event = LocomotiveStatusChangeEvent(EventId.generate(), Timestamp.from_simulation_time(0.0), 'L001', 'idle')
    collector.record_event(event)
    collector._finalize_times(60.0)

    results = collector.get_results()

    assert all(r.category == 'locomotive' for r in results)
