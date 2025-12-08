"""Tests for wagon collector."""

from popupsim.backend.src.MVP.analytics.domain.collectors.wagon_collector import (
    WagonCollector,
)
from popupsim.backend.src.MVP.analytics.domain.events.simulation_events import (
    WagonDeliveredEvent,
    WagonRejectedEvent,
    WagonRetrofittedEvent,
)
from popupsim.backend.src.MVP.analytics.domain.value_objects.event_id import EventId
from popupsim.backend.src.MVP.analytics.domain.value_objects.timestamp import Timestamp


def test_wagon_collector_initialization() -> None:
    """Test WagonCollector initialization."""
    collector = WagonCollector()
    assert collector.total_flow_time == 0.0
    assert collector.flow_time_count == 0
    assert len(collector.wagon_start_times) == 0


def test_record_wagon_delivered() -> None:
    """Test recording wagon delivered event."""
    collector = WagonCollector()
    event = WagonDeliveredEvent(
        EventId.generate(), Timestamp.from_simulation_time(10.0), "analytics", "W001"
    )
    collector.record_event(event)
    assert "W001" in collector.wagon_start_times
    assert collector.wagon_start_times["W001"] == 10.0


def test_record_wagon_retrofitted() -> None:
    """Test recording wagon retrofitted event."""
    collector = WagonCollector()
    delivered = WagonDeliveredEvent(
        EventId.generate(), Timestamp.from_simulation_time(10.0), "analytics", "W001"
    )
    retrofitted = WagonRetrofittedEvent(
        EventId.generate(),
        Timestamp.from_simulation_time(50.0),
        "analytics",
        "W001",
        "WS001",
        40.0,
    )
    collector.record_event(delivered)
    collector.record_event(retrofitted)
    assert collector.total_flow_time == 40.0
    assert collector.flow_time_count == 1
    assert "W001" not in collector.wagon_start_times  # Cleaned up


def test_record_wagon_rejected() -> None:
    """Test recording wagon rejected event."""
    collector = WagonCollector()
    delivered = WagonDeliveredEvent(
        EventId.generate(), Timestamp.from_simulation_time(10.0), "analytics", "W001"
    )
    rejected = WagonRejectedEvent(
        EventId.generate(),
        Timestamp.from_simulation_time(20.0),
        "analytics",
        "W001",
        "capacity",
    )
    collector.record_event(delivered)
    collector.record_event(rejected)
    assert "W001" not in collector.wagon_start_times  # Cleaned up


def test_multiple_wagon_flow() -> None:
    """Test tracking multiple wagons."""
    collector = WagonCollector()
    events = [
        WagonDeliveredEvent(
            EventId.generate(), Timestamp.from_simulation_time(0.0), "analytics", "W001"
        ),
        WagonDeliveredEvent(
            EventId.generate(), Timestamp.from_simulation_time(5.0), "analytics", "W002"
        ),
        WagonRetrofittedEvent(
            EventId.generate(),
            Timestamp.from_simulation_time(30.0),
            "analytics",
            "W001",
            "WS001",
            30.0,
        ),
        WagonRetrofittedEvent(
            EventId.generate(),
            Timestamp.from_simulation_time(45.0),
            "analytics",
            "W002",
            "WS001",
            40.0,
        ),
    ]
    for event in events:
        collector.record_event(event)
    assert collector.total_flow_time == 70.0
    assert collector.flow_time_count == 2


def test_get_results() -> None:
    """Test getting results."""
    collector = WagonCollector()
    results = collector.get_results()
    assert len(results) == 2
    assert results[0].name == "avg_flow_time"
    assert results[1].name == "total_flow_time"


def test_avg_flow_time_calculation() -> None:
    """Test average flow time calculation."""
    collector = WagonCollector()
    events = [
        WagonDeliveredEvent(
            EventId.generate(), Timestamp.from_simulation_time(0.0), "analytics", "W001"
        ),
        WagonDeliveredEvent(
            EventId.generate(), Timestamp.from_simulation_time(0.0), "analytics", "W002"
        ),
        WagonRetrofittedEvent(
            EventId.generate(),
            Timestamp.from_simulation_time(30.0),
            "analytics",
            "W001",
            "WS001",
            30.0,
        ),
        WagonRetrofittedEvent(
            EventId.generate(),
            Timestamp.from_simulation_time(60.0),
            "analytics",
            "W002",
            "WS001",
            60.0,
        ),
    ]
    for event in events:
        collector.record_event(event)
    results = collector.get_results()
    avg = next(r for r in results if r.name == "avg_flow_time")
    assert avg.value.value == 45.0


def test_reset_collector() -> None:
    """Test resetting collector."""
    collector = WagonCollector()
    event = WagonDeliveredEvent(
        EventId.generate(), Timestamp.from_simulation_time(10.0), "analytics", "W001"
    )
    collector.record_event(event)
    collector.reset()
    assert collector.total_flow_time == 0.0
    assert collector.flow_time_count == 0
    assert len(collector.wagon_start_times) == 0
