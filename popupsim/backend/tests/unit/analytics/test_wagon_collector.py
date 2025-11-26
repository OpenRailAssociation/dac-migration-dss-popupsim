"""Tests for wagon collector."""

from analytics.domain.collectors.wagon_collector import WagonCollector
from analytics.domain.events.simulation_events import WagonDeliveredEvent
from analytics.domain.events.simulation_events import WagonRejectedEvent
from analytics.domain.events.simulation_events import WagonRetrofittedEvent
from analytics.domain.value_objects.event_id import EventId
from analytics.domain.value_objects.timestamp import Timestamp


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

    event = WagonDeliveredEvent(
        event_id=EventId.generate(), timestamp=Timestamp.from_simulation_time(10.0), wagon_id='W001'
    )
    collector.record_event(event)

    assert collector.wagons_delivered == 1
    assert 'W001' in collector.wagon_start_times
    assert collector.wagon_start_times['W001'] == 10.0


def test_record_wagon_retrofitted() -> None:
    """Test recording wagon retrofitted event."""
    collector = WagonCollector()

    delivered_event = WagonDeliveredEvent(
        event_id=EventId.generate(), timestamp=Timestamp.from_simulation_time(10.0), wagon_id='W001'
    )
    retrofitted_event = WagonRetrofittedEvent(
        event_id=EventId.generate(),
        timestamp=Timestamp.from_simulation_time(50.0),
        wagon_id='W001',
        workshop_id='WS001',
        processing_duration=40.0,
    )

    collector.record_event(delivered_event)
    collector.record_event(retrofitted_event)

    assert collector.wagons_retrofitted == 1
    assert collector.total_flow_time == 40.0


def test_record_wagon_rejected() -> None:
    """Test recording wagon rejected event."""
    collector = WagonCollector()

    event = WagonRejectedEvent(
        event_id=EventId.generate(), timestamp=Timestamp.now(), wagon_id='W001', reason='capacity_exceeded'
    )
    collector.record_event(event)

    assert collector.wagons_rejected == 1


def test_multiple_wagon_flow() -> None:
    """Test tracking multiple wagons through the system."""
    collector = WagonCollector()

    events = [
        WagonDeliveredEvent(EventId.generate(), Timestamp.from_simulation_time(0.0), 'W001'),
        WagonDeliveredEvent(EventId.generate(), Timestamp.from_simulation_time(5.0), 'W002'),
        WagonRetrofittedEvent(EventId.generate(), Timestamp.from_simulation_time(30.0), 'W001', 'WS001', 30.0),
        WagonRetrofittedEvent(EventId.generate(), Timestamp.from_simulation_time(45.0), 'W002', 'WS001', 40.0),
    ]

    for event in events:
        collector.record_event(event)

    assert collector.wagons_delivered == 2
    assert collector.wagons_retrofitted == 2
    assert collector.total_flow_time == 70.0


def test_get_results_with_no_data() -> None:
    """Test getting results with no recorded events."""
    collector = WagonCollector()

    results = collector.get_results()

    assert len(results) == 4
    assert results[0].name == 'wagons_delivered'
    assert results[0].value.value == 0
    assert results[1].name == 'wagons_retrofitted'
    assert results[1].value.value == 0
    assert results[2].name == 'wagons_rejected'
    assert results[2].value.value == 0
    assert results[3].name == 'avg_flow_time'
    assert results[3].value.value == 0.0


def test_get_results_with_data() -> None:
    """Test getting results with recorded events."""
    collector = WagonCollector()

    events = [
        WagonDeliveredEvent(EventId.generate(), Timestamp.from_simulation_time(0.0), 'W001'),
        WagonDeliveredEvent(EventId.generate(), Timestamp.from_simulation_time(10.0), 'W002'),
        WagonRetrofittedEvent(EventId.generate(), Timestamp.from_simulation_time(60.0), 'W001', 'WS001', 60.0),
        WagonRetrofittedEvent(EventId.generate(), Timestamp.from_simulation_time(80.0), 'W002', 'WS001', 70.0),
        WagonRejectedEvent(EventId.generate(), Timestamp.now(), 'W003', 'capacity'),
    ]

    for event in events:
        collector.record_event(event)

    results = collector.get_results()

    assert len(results) == 4
    assert results[0].value.value == 2
    assert results[1].value.value == 2
    assert results[2].value.value == 1
    assert results[3].value.value == 65.0


def test_avg_flow_time_calculation() -> None:
    """Test average flow time calculation."""
    collector = WagonCollector()

    events = [
        WagonDeliveredEvent(EventId.generate(), Timestamp.from_simulation_time(0.0), 'W001'),
        WagonDeliveredEvent(EventId.generate(), Timestamp.from_simulation_time(0.0), 'W002'),
        WagonDeliveredEvent(EventId.generate(), Timestamp.from_simulation_time(0.0), 'W003'),
        WagonRetrofittedEvent(EventId.generate(), Timestamp.from_simulation_time(30.0), 'W001', 'WS001', 30.0),
        WagonRetrofittedEvent(EventId.generate(), Timestamp.from_simulation_time(60.0), 'W002', 'WS001', 60.0),
        WagonRetrofittedEvent(EventId.generate(), Timestamp.from_simulation_time(90.0), 'W003', 'WS001', 90.0),
    ]

    for event in events:
        collector.record_event(event)

    results = collector.get_results()
    avg_flow_time = next(r for r in results if r.name == 'avg_flow_time')

    assert avg_flow_time.value.value == 60.0
    assert avg_flow_time.value.unit == 'minutes'


def test_reset_collector() -> None:
    """Test resetting collector state."""
    collector = WagonCollector()

    events = [
        WagonDeliveredEvent(EventId.generate(), Timestamp.from_simulation_time(10.0), 'W001'),
        WagonRetrofittedEvent(EventId.generate(), Timestamp.from_simulation_time(50.0), 'W001', 'WS001', 40.0),
        WagonRejectedEvent(EventId.generate(), Timestamp.now(), 'W002', 'capacity'),
    ]

    for event in events:
        collector.record_event(event)

    collector.reset()

    assert collector.wagons_delivered == 0
    assert collector.wagons_retrofitted == 0
    assert collector.wagons_rejected == 0
    assert collector.total_flow_time == 0.0
    assert len(collector.wagon_start_times) == 0


def test_unknown_event_type() -> None:
    """Test handling unknown event types."""
    from analytics.domain.events.base_event import DomainEvent

    collector = WagonCollector()

    unknown_event = DomainEvent(EventId.generate(), Timestamp.now())
    collector.record_event(unknown_event)

    results = collector.get_results()
    assert all(r.value.value == 0 or r.value.value == 0.0 for r in results)


def test_wagon_retrofitted_without_delivery() -> None:
    """Test retrofitted event without prior delivery event."""
    collector = WagonCollector()

    event = WagonRetrofittedEvent(EventId.generate(), Timestamp.from_simulation_time(50.0), 'W001', 'WS001', 50.0)
    collector.record_event(event)

    assert collector.wagons_retrofitted == 1
    assert collector.total_flow_time == 0.0


def test_metric_result_categories() -> None:
    """Test that all metrics have correct category."""
    collector = WagonCollector()
    event = WagonDeliveredEvent(EventId.generate(), Timestamp.from_simulation_time(0.0), 'W001')
    collector.record_event(event)

    results = collector.get_results()

    assert all(r.category == 'wagon' for r in results)


def test_metric_result_units() -> None:
    """Test that metrics have correct units."""
    collector = WagonCollector()

    results = collector.get_results()

    assert results[0].value.unit == 'count'
    assert results[1].value.unit == 'count'
    assert results[2].value.unit == 'count'
    assert results[3].value.unit == 'minutes'
