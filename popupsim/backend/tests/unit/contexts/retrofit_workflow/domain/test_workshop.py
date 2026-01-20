"""Tests for Workshop domain entity."""

from contexts.retrofit_workflow.domain.entities.workshop import BayStatus
from contexts.retrofit_workflow.domain.entities.workshop import RetrofitBay
from contexts.retrofit_workflow.domain.entities.workshop import Workshop
from contexts.retrofit_workflow.domain.entities.workshop import create_workshop
import pytest


class TestRetrofitBay:
    """Test RetrofitBay entity."""

    def test_bay_creation(self) -> None:
        """Test bay creation with default state."""
        bay = RetrofitBay(id='bay_1', workshop_id='ws_1')

        assert bay.id == 'bay_1'
        assert bay.workshop_id == 'ws_1'
        assert bay.status == BayStatus.IDLE
        assert bay.current_wagon_id is None
        assert bay.is_available is True

    def test_start_retrofit_success(self) -> None:
        """Test successful retrofit start."""
        bay = RetrofitBay(id='bay_1', workshop_id='ws_1')

        bay.start_retrofit('wagon_1', 10.0)

        assert bay.status == BayStatus.BUSY
        assert bay.current_wagon_id == 'wagon_1'
        assert bay.is_available is False

    def test_start_retrofit_when_busy_raises_error(self) -> None:
        """Test starting retrofit on busy bay raises error."""
        bay = RetrofitBay(id='bay_1', workshop_id='ws_1')
        bay.start_retrofit('wagon_1', 10.0)

        with pytest.raises(ValueError, match='Bay bay_1 is busy with wagon wagon_1'):
            bay.start_retrofit('wagon_2', 15.0)

    def test_complete_retrofit_success(self) -> None:
        """Test successful retrofit completion."""
        bay = RetrofitBay(id='bay_1', workshop_id='ws_1')
        bay.start_retrofit('wagon_1', 10.0)

        wagon_id = bay.complete_retrofit()

        assert wagon_id == 'wagon_1'
        assert bay.status == BayStatus.IDLE
        assert bay.current_wagon_id is None
        assert bay.is_available is True

    def test_complete_retrofit_when_idle_raises_error(self) -> None:
        """Test completing retrofit on idle bay raises error."""
        bay = RetrofitBay(id='bay_1', workshop_id='ws_1')

        with pytest.raises(ValueError, match='Bay bay_1 is idle, no retrofit to complete'):
            bay.complete_retrofit()


class TestWorkshop:
    """Test Workshop aggregate root."""

    def test_workshop_creation(self) -> None:
        """Test workshop creation with bays."""
        bays = [RetrofitBay(id='bay_1', workshop_id='ws_1'), RetrofitBay(id='bay_2', workshop_id='ws_1')]
        workshop = Workshop(id='ws_1', location='track_1', bays=bays)

        assert workshop.id == 'ws_1'
        assert workshop.location == 'track_1'
        assert workshop.capacity == 2
        assert workshop.available_capacity == 2
        assert workshop.queue_length == 0
        assert workshop.utilization == 0.0

    def test_workshop_without_bays_raises_error(self) -> None:
        """Test workshop creation without bays raises error."""
        with pytest.raises(ValueError, match='Workshop ws_1 must have at least one bay'):
            Workshop(id='ws_1', location='track_1', bays=[])

    def test_queue_operations(self) -> None:
        """Test wagon queue operations."""
        workshop = create_workshop('ws_1', 'track_1', 2)

        # Add to queue
        workshop.add_to_queue('wagon_1')
        workshop.add_to_queue('wagon_2')
        assert workshop.queue_length == 2

        # Get next from queue (FIFO)
        wagon_id = workshop.get_next_from_queue()
        assert wagon_id == 'wagon_1'
        assert workshop.queue_length == 1

        # Remove from queue
        workshop.remove_from_queue('wagon_2')
        assert workshop.queue_length == 0

        # Get from empty queue
        wagon_id = workshop.get_next_from_queue()
        assert wagon_id is None

    def test_assign_to_bay_success(self) -> None:
        """Test successful bay assignment."""
        workshop = create_workshop('ws_1', 'track_1', 2)

        bay = workshop.assign_to_bay('wagon_1', 10.0)

        assert bay.current_wagon_id == 'wagon_1'
        assert workshop.available_capacity == 1
        assert workshop.utilization == 50.0

    def test_assign_to_bay_when_full_raises_error(self) -> None:
        """Test bay assignment when workshop full raises error."""
        workshop = create_workshop('ws_1', 'track_1', 1)
        workshop.assign_to_bay('wagon_1', 10.0)

        with pytest.raises(ValueError, match='Workshop ws_1 has no available bays'):
            workshop.assign_to_bay('wagon_2', 15.0)

    def test_complete_retrofit_success(self) -> None:
        """Test successful retrofit completion."""
        workshop = create_workshop('ws_1', 'track_1', 2)
        bay = workshop.assign_to_bay('wagon_1', 10.0)

        wagon_id = workshop.complete_retrofit(bay.id)

        assert wagon_id == 'wagon_1'
        assert workshop.available_capacity == 2
        assert workshop.utilization == 0.0

    def test_complete_retrofit_invalid_bay_raises_error(self) -> None:
        """Test completing retrofit with invalid bay raises error."""
        workshop = create_workshop('ws_1', 'track_1', 2)

        with pytest.raises(ValueError, match='Bay invalid_bay not found in workshop ws_1'):
            workshop.complete_retrofit('invalid_bay')

    def test_get_wagon_bay(self) -> None:
        """Test finding bay by wagon ID."""
        workshop = create_workshop('ws_1', 'track_1', 2)
        bay = workshop.assign_to_bay('wagon_1', 10.0)

        found_bay = workshop.get_wagon_bay('wagon_1')
        assert found_bay == bay

        not_found = workshop.get_wagon_bay('wagon_2')
        assert not_found is None

    def test_available_and_busy_bays(self) -> None:
        """Test available and busy bay properties."""
        workshop = create_workshop('ws_1', 'track_1', 3)

        # Initially all available
        assert len(workshop.available_bays) == 3
        assert len(workshop.busy_bays) == 0

        # Assign one bay
        workshop.assign_to_bay('wagon_1', 10.0)
        assert len(workshop.available_bays) == 2
        assert len(workshop.busy_bays) == 1

        # Assign another bay
        workshop.assign_to_bay('wagon_2', 15.0)
        assert len(workshop.available_bays) == 1
        assert len(workshop.busy_bays) == 2


class TestCreateWorkshop:
    """Test workshop factory function."""

    def test_create_workshop_success(self) -> None:
        """Test successful workshop creation."""
        workshop = create_workshop('ws_1', 'track_1', 3)

        assert workshop.id == 'ws_1'
        assert workshop.location == 'track_1'
        assert workshop.capacity == 3
        assert len(workshop.bays) == 3

        # Check bay IDs
        expected_bay_ids = ['ws_1_bay_0', 'ws_1_bay_1', 'ws_1_bay_2']
        actual_bay_ids = [bay.id for bay in workshop.bays]
        assert actual_bay_ids == expected_bay_ids

        # Check all bays belong to workshop
        for bay in workshop.bays:
            assert bay.workshop_id == 'ws_1'
