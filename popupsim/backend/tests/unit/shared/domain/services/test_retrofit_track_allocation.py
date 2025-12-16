"""Tests for retrofit track allocation service."""

from shared.domain.services.retrofit_track_allocation_service import RetrofitAllocation
from shared.domain.services.retrofit_track_allocation_service import RetrofitTrackAllocationService


class MockWagon:
    """Mock wagon for testing."""

    def __init__(self, wagon_id: str, length: float = 10.0):
        self.id = wagon_id
        self.length = length


class TestRetrofitTrackAllocationService:
    """Test retrofit track allocation service."""

    def test_allocate_wagons_single_track(self):
        """Test allocation to single retrofit track."""
        service = RetrofitTrackAllocationService()
        wagons = [MockWagon(f'W{i}') for i in range(5)]  # 5 wagons, 50m total
        tracks = {'retrofit_1': 60.0}  # 60m capacity

        allocation = service.allocate_wagons(wagons, tracks)  # type: ignore[arg-type]

        assert len(allocation.track_assignments['retrofit_1']) == 5
        assert len(allocation.overflow_wagons) == 0
        assert allocation.allocation_efficiency == 1.0

    def test_allocate_wagons_multiple_tracks(self):
        """Test allocation to multiple retrofit tracks."""
        service = RetrofitTrackAllocationService()
        wagons = [MockWagon(f'W{i}') for i in range(10)]  # 10 wagons, 100m total
        tracks = {
            'retrofit_1': 60.0,  # Can fit 6 wagons
            'retrofit_2': 30.0,  # Can fit 3 wagons
        }

        allocation = service.allocate_wagons(wagons, tracks)  # type: ignore[arg-type]

        assert len(allocation.track_assignments['retrofit_1']) == 6
        assert len(allocation.track_assignments['retrofit_2']) == 3
        assert len(allocation.overflow_wagons) == 1  # 1 wagon overflow
        assert allocation.allocation_efficiency == 0.9  # 9/10 allocated

    def test_allocate_wagons_with_overflow(self):
        """Test allocation with overflow wagons."""
        service = RetrofitTrackAllocationService()
        wagons = [MockWagon(f'W{i}') for i in range(20)]  # 20 wagons, 200m total
        tracks = {'retrofit_1': 50.0}  # Only 50m capacity

        allocation = service.allocate_wagons(wagons, tracks)  # type: ignore[arg-type]

        assert len(allocation.track_assignments['retrofit_1']) == 5
        assert len(allocation.overflow_wagons) == 15
        assert allocation.allocation_efficiency == 0.25  # 5/20 allocated

    def test_validate_allocation_success(self):
        """Test successful allocation validation."""
        service = RetrofitTrackAllocationService()
        allocation = RetrofitAllocation(
            track_assignments={'retrofit_1': [MockWagon('W1')]},  # type: ignore[list-item]
            overflow_wagons=[],
            total_capacity_used=1.0,
            allocation_efficiency=1.0,
        )

        is_valid, issues = service.validate_allocation(allocation)

        assert is_valid
        assert len(issues) == 0

    def test_validate_allocation_low_efficiency(self):
        """Test allocation validation with low efficiency."""
        service = RetrofitTrackAllocationService()
        allocation = RetrofitAllocation(
            track_assignments={'retrofit_1': [MockWagon('W1')]},  # type: ignore[list-item]
            overflow_wagons=[MockWagon('W2'), MockWagon('W3')],  # type: ignore[list-item]
            total_capacity_used=1.0,
            allocation_efficiency=0.33,  # Below 0.8 threshold
        )

        is_valid, issues = service.validate_allocation(allocation)

        assert not is_valid
        assert len(issues) == 2  # Low efficiency + overflow wagons
