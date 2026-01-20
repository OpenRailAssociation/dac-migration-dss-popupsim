"""Test BatchAggregate domain aggregate."""

from contexts.retrofit_workflow.domain.aggregates.batch_aggregate import BatchAggregate
from contexts.retrofit_workflow.domain.aggregates.batch_aggregate import BatchStatus
from contexts.retrofit_workflow.domain.aggregates.batch_aggregate import DomainError
from contexts.retrofit_workflow.domain.entities.locomotive import Locomotive
from contexts.retrofit_workflow.domain.entities.wagon import Wagon
from contexts.retrofit_workflow.domain.value_objects.coupler import Coupler
from contexts.retrofit_workflow.domain.value_objects.coupler import CouplerType
import pytest


class TestBatchAggregate:
    """Test BatchAggregate domain aggregate."""

    def test_batch_creation(self) -> None:
        """Test batch aggregate creation."""
        # Create test wagons
        coupler_a = Coupler(CouplerType.SCREW, 'A')
        coupler_b = Coupler(CouplerType.SCREW, 'B')

        wagons = [
            Wagon(id='W1', length=20.0, coupler_a=coupler_a, coupler_b=coupler_b),
            Wagon(id='W2', length=15.0, coupler_a=coupler_a, coupler_b=coupler_b),
        ]

        # Prepare wagons for retrofit
        for wagon in wagons:
            wagon.classify()
            wagon.prepare_for_retrofit()

        # Create batch aggregate
        batch = BatchAggregate(id='BATCH_001', wagons=wagons, destination='WS1', rake_id='BATCH_001_RAKE')

        # Verify properties
        assert batch.id == 'BATCH_001'
        assert batch.destination == 'WS1'
        assert batch.rake_id == 'BATCH_001_RAKE'
        assert batch.status == BatchStatus.FORMED
        assert batch.wagon_count == 2
        assert batch.total_length == 35.0
        assert batch.locomotive is None
        assert batch.can_start_transport()

    def test_batch_transport_lifecycle(self) -> None:
        """Test batch transport lifecycle."""
        coupler_a = Coupler(CouplerType.SCREW, 'A')
        coupler_b = Coupler(CouplerType.SCREW, 'B')

        wagons = [Wagon(id='W1', length=10.0, coupler_a=coupler_a, coupler_b=coupler_b)]
        wagons[0].classify()
        wagons[0].prepare_for_retrofit()

        batch = BatchAggregate(id='BATCH_001', wagons=wagons, destination='WS1', rake_id='BATCH_001_RAKE')

        # Create locomotive with required couplers
        coupler_front = Coupler(CouplerType.SCREW, 'FRONT')
        coupler_back = Coupler(CouplerType.SCREW, 'BACK')
        locomotive = Locomotive(
            id='LOCO_001', home_track='locoparking', coupler_front=coupler_front, coupler_back=coupler_back
        )

        # Start transport
        batch.start_transport(locomotive)
        assert batch.status == BatchStatus.IN_TRANSPORT
        assert batch.locomotive == locomotive
        assert len(batch.events) == 1

        # Arrive at destination
        batch.arrive_at_destination()
        assert batch.status == BatchStatus.AT_WORKSHOP
        assert len(batch.events) == 2

        # Start processing
        batch.start_processing()
        assert batch.status == BatchStatus.PROCESSING

        # Complete processing
        batch.complete_processing()
        assert batch.status == BatchStatus.COMPLETED
        assert len(batch.events) == 3

    def test_batch_invalid_state_transitions(self) -> None:
        """Test invalid state transitions raise errors."""
        coupler_a = Coupler(CouplerType.SCREW, 'A')
        coupler_b = Coupler(CouplerType.SCREW, 'B')

        wagons = [Wagon(id='W1', length=10.0, coupler_a=coupler_a, coupler_b=coupler_b)]
        wagons[0].classify()
        wagons[0].prepare_for_retrofit()

        batch = BatchAggregate(id='BATCH_001', wagons=wagons, destination='WS1', rake_id='BATCH_001_RAKE')

        # Create locomotive with required couplers
        coupler_front = Coupler(CouplerType.SCREW, 'FRONT')
        coupler_back = Coupler(CouplerType.SCREW, 'BACK')
        locomotive = Locomotive(
            id='LOCO_001', home_track='locoparking', coupler_front=coupler_front, coupler_back=coupler_back
        )

        # Try to arrive without starting transport
        with pytest.raises(DomainError, match='not in transport'):
            batch.arrive_at_destination()

        # Try to start transport twice
        batch.start_transport(locomotive)
        with pytest.raises(DomainError, match='not ready for transport'):
            batch.start_transport(locomotive)

    def test_empty_batch_raises_error(self) -> None:
        """Test empty batch raises domain error."""
        with pytest.raises(DomainError, match='cannot be empty'):
            BatchAggregate(id='BATCH_001', wagons=[], destination='WS1', rake_id='BATCH_001_RAKE')

    def test_batch_without_destination_raises_error(self) -> None:
        """Test batch without destination raises error."""
        coupler_a = Coupler(CouplerType.SCREW, 'A')
        coupler_b = Coupler(CouplerType.SCREW, 'B')

        wagons = [Wagon(id='W1', length=10.0, coupler_a=coupler_a, coupler_b=coupler_b)]

        with pytest.raises(DomainError, match='must have destination'):
            BatchAggregate(id='BATCH_001', wagons=wagons, destination='', rake_id='BATCH_001_RAKE')

    def test_event_management(self) -> None:
        """Test domain event management."""
        coupler_a = Coupler(CouplerType.SCREW, 'A')
        coupler_b = Coupler(CouplerType.SCREW, 'B')

        wagons = [Wagon(id='W1', length=10.0, coupler_a=coupler_a, coupler_b=coupler_b)]
        wagons[0].classify()
        wagons[0].prepare_for_retrofit()

        batch = BatchAggregate(id='BATCH_001', wagons=wagons, destination='WS1', rake_id='BATCH_001_RAKE')

        # Create locomotive with required couplers
        coupler_front = Coupler(CouplerType.SCREW, 'FRONT')
        coupler_back = Coupler(CouplerType.SCREW, 'BACK')
        locomotive = Locomotive(
            id='LOCO_001', home_track='locoparking', coupler_front=coupler_front, coupler_back=coupler_back
        )

        # Generate events
        batch.start_transport(locomotive)
        batch.arrive_at_destination()

        # Check events
        events = batch.events
        assert len(events) == 2
        assert events[0]['type'] == 'BatchTransportStarted'
        assert events[1]['type'] == 'BatchArrivedAtDestination'

        # Clear events
        batch.clear_events()
        assert len(batch.events) == 0