"""Unit tests for EventCollector."""

from datetime import UTC
from datetime import datetime
from pathlib import Path

from contexts.retrofit_workflow.application.event_collector import EventCollector
from contexts.retrofit_workflow.domain.events import LocomotiveMovementEvent
from contexts.retrofit_workflow.domain.events import ResourceStateChangeEvent
from contexts.retrofit_workflow.domain.events import WagonJourneyEvent
from contexts.retrofit_workflow.domain.events.batch_events import BatchFormed
import pytest


@pytest.fixture
def event_collector() -> EventCollector:
    """Create EventCollector instance."""
    return EventCollector(start_datetime='2024-01-01T00:00:00Z')


@pytest.fixture
def wagon_event() -> WagonJourneyEvent:
    """Create sample wagon event."""
    return WagonJourneyEvent(
        timestamp=60.0,
        wagon_id='W001',
        train_id='T001',
        event_type='ARRIVED',
        location='collection',
        status='WAITING',
    )


@pytest.fixture
def locomotive_event() -> LocomotiveMovementEvent:
    """Create sample locomotive event."""
    return LocomotiveMovementEvent(
        timestamp=120.0, locomotive_id='L001', event_type='MOVING', from_location='parking', to_location='collection'
    )


@pytest.fixture
def resource_event() -> ResourceStateChangeEvent:
    """Create sample resource event."""
    return ResourceStateChangeEvent(
        timestamp=180.0,
        resource_type='workshop',
        resource_id='WS001',
        change_type='bay_occupied',
        total_bays=2,
        busy_bays_before=0,
        busy_bays_after=1,
    )


@pytest.fixture
def batch_formed_event() -> BatchFormed:
    """Create sample batch formed event."""
    return BatchFormed(
        timestamp=240.0,
        event_id='E001',
        batch_id='B001',
        wagon_ids=['W001', 'W002'],
        destination='retrofit',
        total_length=30.0,
    )


class TestEventCollectorInitialization:
    """Test EventCollector initialization."""

    def test_init_with_start_datetime(self) -> None:
        """Test initialization with start datetime."""
        collector = EventCollector(start_datetime='2024-01-01T00:00:00Z')
        assert collector.start_datetime == '2024-01-01T00:00:00Z'
        assert collector.wagon_events == []
        assert collector.locomotive_events == []
        assert collector.resource_events == []
        assert collector.batch_events == []

    def test_init_without_start_datetime(self) -> None:
        """Test initialization without start datetime."""
        collector = EventCollector()
        assert collector.start_datetime is None
        assert collector.wagon_events == []


class TestEventCollection:
    """Test event collection methods."""

    def test_add_wagon_event(self, event_collector: EventCollector, wagon_event: WagonJourneyEvent) -> None:
        """Test adding wagon event."""
        event_collector.add_wagon_event(wagon_event)
        assert len(event_collector.wagon_events) == 1
        assert event_collector.wagon_events[0] == wagon_event

    def test_add_multiple_wagon_events(self, event_collector: EventCollector) -> None:
        """Test adding multiple wagon events."""
        events = [
            WagonJourneyEvent(
                timestamp=float(i * 60),
                wagon_id=f'W{i:03d}',
                event_type='ARRIVED',
                location='collection',
                status='WAITING',
            )
            for i in range(5)
        ]
        for event in events:
            event_collector.add_wagon_event(event)
        assert len(event_collector.wagon_events) == 5

    def test_add_locomotive_event(
        self, event_collector: EventCollector, locomotive_event: LocomotiveMovementEvent
    ) -> None:
        """Test adding locomotive event."""
        event_collector.add_locomotive_event(locomotive_event)
        assert len(event_collector.locomotive_events) == 1
        assert event_collector.locomotive_events[0] == locomotive_event

    def test_add_resource_event(
        self, event_collector: EventCollector, resource_event: ResourceStateChangeEvent
    ) -> None:
        """Test adding resource event."""
        event_collector.add_resource_event(resource_event)
        assert len(event_collector.resource_events) == 1
        assert event_collector.resource_events[0] == resource_event

    def test_add_batch_event(self, event_collector: EventCollector, batch_formed_event: BatchFormed) -> None:
        """Test adding batch event."""
        event_collector.add_batch_event(batch_formed_event)
        assert len(event_collector.batch_events) == 1
        assert event_collector.batch_events[0] == batch_formed_event


class TestTimeConversion:
    """Test simulation time to datetime conversion."""

    def test_sim_time_to_datetime_with_start_time(self) -> None:
        """Test conversion with start datetime."""
        collector = EventCollector(start_datetime='2024-01-01T00:00:00Z')
        result = collector._sim_time_to_datetime(60.0)  # 60 minutes
        assert '2024-01-01T01:00:00' in result

    def test_sim_time_to_datetime_without_start_time(self) -> None:
        """Test conversion without start datetime."""
        collector = EventCollector()
        result = collector._sim_time_to_datetime(60.0)
        assert result == ''

    def test_sim_time_to_datetime_with_datetime_object(self) -> None:
        """Test conversion with datetime object."""
        start_dt = datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC)
        collector = EventCollector(start_datetime=start_dt)  # type: ignore[arg-type]
        result = collector._sim_time_to_datetime(120.0)  # 120 minutes
        assert '2024-01-01T02:00:00' in result


class TestExportWagonJourney:
    """Test wagon journey export."""

    def test_export_wagon_journey_creates_file(self, event_collector: EventCollector, tmp_path: Path) -> None:
        """Test that export creates CSV file."""
        event_collector.add_wagon_event(
            WagonJourneyEvent(
                timestamp=60.0, wagon_id='W001', event_type='ARRIVED', location='collection', status='WAITING'
            )
        )
        filepath = tmp_path / 'wagon_journey.csv'
        event_collector.export_wagon_journey(str(filepath))
        assert filepath.exists()

    def test_export_wagon_journey_content(self, event_collector: EventCollector, tmp_path: Path) -> None:
        """Test wagon journey CSV content."""
        event_collector.add_wagon_event(
            WagonJourneyEvent(
                timestamp=60.0,
                wagon_id='W001',
                train_id='T001',
                event_type='ARRIVED',
                location='collection',
                status='WAITING',
            )
        )
        filepath = tmp_path / 'wagon_journey.csv'
        event_collector.export_wagon_journey(str(filepath))

        content = filepath.read_text()
        assert 'timestamp' in content
        assert 'wagon_id' in content
        assert 'W001' in content
        assert 'ARRIVED' in content


class TestExportRejectedWagons:
    """Test rejected wagons export."""

    def test_export_rejected_wagons_filters_correctly(self, event_collector: EventCollector, tmp_path: Path) -> None:
        """Test that only rejected wagons are exported."""
        event_collector.add_wagon_event(
            WagonJourneyEvent(
                timestamp=60.0, wagon_id='W001', event_type='ARRIVED', location='collection', status='WAITING'
            )
        )
        event_collector.add_wagon_event(
            WagonJourneyEvent(
                timestamp=120.0,
                wagon_id='W002',
                event_type='REJECTED',
                location='REJECTED',
                status='REJECTED',
                rejection_reason='WAGON_LOADED',
            )
        )

        filepath = tmp_path / 'rejected.csv'
        event_collector.export_rejected_wagons(str(filepath))

        content = filepath.read_text()
        assert 'W002' in content
        assert 'W001' not in content


class TestExportLocomotiveMovements:
    """Test locomotive movements export."""

    def test_export_locomotive_movements(self, event_collector: EventCollector, tmp_path: Path) -> None:
        """Test locomotive movements export."""
        event_collector.add_locomotive_event(
            LocomotiveMovementEvent(
                timestamp=60.0,
                locomotive_id='L001',
                event_type='MOVING',
                from_location='parking',
                to_location='collection',
            )
        )

        filepath = tmp_path / 'loco_movements.csv'
        event_collector.export_locomotive_movements(str(filepath))

        content = filepath.read_text()
        assert 'L001' in content
        assert 'MOVING' in content


class TestExportSummaryMetrics:
    """Test summary metrics export."""

    def test_export_summary_metrics_creates_json(self, event_collector: EventCollector, tmp_path: Path) -> None:
        """Test that summary metrics creates JSON file."""
        event_collector.add_wagon_event(
            WagonJourneyEvent(
                timestamp=60.0, wagon_id='W001', event_type='ARRIVED', location='collection', status='WAITING'
            )
        )

        filepath = tmp_path / 'summary.json'
        event_collector.export_summary_metrics(str(filepath))

        assert filepath.exists()
        content = filepath.read_text()
        assert 'total_events' in content
        assert 'wagons_arrived' in content

    def test_export_summary_metrics_calculates_correctly(self, event_collector: EventCollector, tmp_path: Path) -> None:
        """Test summary metrics calculations."""
        # Add various events
        event_collector.add_wagon_event(
            WagonJourneyEvent(
                timestamp=60.0,
                wagon_id='W001',
                train_id='T001',
                event_type='ARRIVED',
                location='collection',
                status='WAITING',
            )
        )
        event_collector.add_wagon_event(
            WagonJourneyEvent(
                timestamp=120.0, wagon_id='W001', event_type='PARKED', location='parking', status='PARKED'
            )
        )
        event_collector.add_wagon_event(
            WagonJourneyEvent(
                timestamp=180.0,
                wagon_id='W002',
                event_type='REJECTED',
                location='REJECTED',
                status='REJECTED',
                rejection_reason='WAGON_LOADED',
            )
        )

        filepath = tmp_path / 'summary.json'
        event_collector.export_summary_metrics(str(filepath))

        import json

        with open(filepath) as f:
            metrics = json.load(f)

        assert metrics['wagons_arrived'] == 1  # Only W001 arrived
        assert metrics['wagons_parked'] == 1
        assert metrics['wagons_rejected'] == 1
        assert metrics['trains_arrived'] == 1


class TestExportAll:
    """Test export_all method."""

    def test_export_all_creates_directory(self, event_collector: EventCollector, tmp_path: Path) -> None:
        """Test that export_all creates output directory."""
        output_dir = tmp_path / 'output'
        event_collector.export_all(str(output_dir))
        assert output_dir.exists()

    def test_export_all_creates_all_files(self, event_collector: EventCollector, tmp_path: Path) -> None:
        """Test that export_all creates all expected files."""
        # Add sample events
        event_collector.add_wagon_event(
            WagonJourneyEvent(
                timestamp=60.0, wagon_id='W001', event_type='ARRIVED', location='collection', status='WAITING'
            )
        )

        output_dir = tmp_path / 'output'
        event_collector.export_all(str(output_dir))

        expected_files = [
            'wagon_journey.csv',
            'rejected_wagons.csv',
            'locomotive_movements.csv',
            'track_capacity.csv',
            'locomotive_utilization.csv',
            'locomotive_util.csv',
            'workshop_utilization.csv',
            'summary_metrics.json',
            'events.csv',
            'timeline.csv',
            'workshop_metrics.csv',
        ]

        for filename in expected_files:
            assert (output_dir / filename).exists(), f'{filename} not created'


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_export_with_empty_events(self, event_collector: EventCollector, tmp_path: Path) -> None:
        """Test export with no events."""
        filepath = tmp_path / 'empty.csv'
        event_collector.export_wagon_journey(str(filepath))
        assert filepath.exists()

    def test_export_with_missing_optional_fields(self, event_collector: EventCollector, tmp_path: Path) -> None:
        """Test export with events missing optional fields."""
        event_collector.add_wagon_event(
            WagonJourneyEvent(
                timestamp=60.0,
                wagon_id='W001',
                event_type='ARRIVED',
                location='collection',
                status='WAITING',
                train_id=None,  # Optional field
            )
        )

        filepath = tmp_path / 'wagon_journey.csv'
        event_collector.export_wagon_journey(str(filepath))
        assert filepath.exists()
