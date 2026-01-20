"""Test track occupancy management with specific capacity scenarios."""

from contexts.retrofit_workflow.domain.entities.wagon import Wagon
from contexts.retrofit_workflow.domain.value_objects.coupler import Coupler
from contexts.retrofit_workflow.domain.value_objects.coupler import CouplerType
from contexts.retrofit_workflow.infrastructure.resources.track_capacity_manager import TrackCapacityManager
import pytest
import simpy


class TestTrackOccupancyScenario:
    """Test specific track occupancy scenario: 100m track, 75% fill, 4x20m wagons."""

    @pytest.fixture
    def env(self) -> simpy.Environment:
        """Create SimPy environment."""
        return simpy.Environment()

    @pytest.fixture
    def wagons_20m(self) -> list[Wagon]:
        """Create 4 wagons of 20 meters each."""
        return [
            Wagon(
                id=f'wagon_{i}',
                length=20.0,
                coupler_a=Coupler(CouplerType.SCREW, 'A'),
                coupler_b=Coupler(CouplerType.SCREW, 'B'),
            )
            for i in range(1, 5)
        ]

    def test_track_capacity_with_fill_factor(self, env: simpy.Environment, wagons_20m: list[Wagon]) -> None:
        """Test track with 100m length, 75% fill factor, 4 wagons of 20m each.

        Expected: 3 wagons should fit (60m), 4th wagon should not fit.
        """
        # Track: 100m total, 75% fill factor = 75m usable capacity
        track = TrackCapacityManager(env, 'test_track', 75.0)

        # Initial state
        assert track.get_available_capacity() == 75.0
        assert track.get_occupied_capacity() == 0.0
        assert track.get_utilization() == 0.0

        # Test if 3 wagons can fit (60m total)
        first_three = wagons_20m[:3]
        assert track.can_fit_wagons(first_three) is True

        # Test if all 4 wagons can fit (80m total) - should not fit
        assert track.can_fit_wagons(wagons_20m) is False

        # Add first 3 wagons
        def add_first_three() -> None:
            yield from track.add_wagons(first_three)

        env.process(add_first_three())
        env.run()

        # Verify state after adding 3 wagons
        assert track.get_occupied_capacity() == 60.0
        assert track.get_available_capacity() == 15.0
        assert track.get_utilization() == 80.0  # 60/75 * 100
        assert track.get_wagon_count() == 3

        # Try to add 4th wagon (20m) - should not fit in remaining 15m
        fourth_wagon = [wagons_20m[3]]
        assert track.can_fit_wagons(fourth_wagon) is False

    def test_track_blocking_behavior(self, env: simpy.Environment, wagons_20m: list[Wagon]) -> None:
        """Test that track blocks when trying to add wagons that don't fit."""
        track = TrackCapacityManager(env, 'test_track', 75.0)

        results = []

        def try_add_all_wagons() -> None:
            """Try to add all 4 wagons - should block after 3."""
            yield from track.add_wagons(wagons_20m)
            results.append('all_added')  # Should not reach this

        def check_after_timeout() -> None:
            """Check state after timeout."""
            yield env.timeout(1.0)
            results.append(f'occupied: {track.get_occupied_capacity()}')
            results.append(f'wagons: {track.get_wagon_count()}')

        env.process(try_add_all_wagons())
        env.process(check_after_timeout())
        env.run(until=2.0)

        # Should have blocked - only partial addition or timeout
        assert 'all_added' not in results
        assert len(results) >= 2  # Timeout results should be present

    def test_exact_capacity_fit(self, env: simpy.Environment) -> None:
        """Test wagons that exactly fit the capacity."""
        track = TrackCapacityManager(env, 'test_track', 60.0)  # Exactly 60m

        # Create 3 wagons of 20m each = exactly 60m
        wagons = [
            Wagon(
                id=f'wagon_{i}',
                length=20.0,
                coupler_a=Coupler(CouplerType.SCREW, 'A'),
                coupler_b=Coupler(CouplerType.SCREW, 'B'),
            )
            for i in range(3)
        ]

        # Should fit exactly
        assert track.can_fit_wagons(wagons) is True

        def add_wagons() -> None:
            yield from track.add_wagons(wagons)

        env.process(add_wagons())
        env.run()

        # Should be exactly full
        assert track.get_occupied_capacity() == 60.0
        assert track.get_available_capacity() == 0.0
        assert track.get_utilization() == 100.0

    def test_partial_wagon_addition(self, env: simpy.Environment, wagons_20m: list[Wagon]) -> None:
        """Test adding wagons one by one until capacity reached."""
        track = TrackCapacityManager(env, 'test_track', 75.0)

        # Add wagons one by one
        for i, wagon in enumerate(wagons_20m):
            if track.can_fit_wagons([wagon]):

                def add_single_wagon(w: Wagon) -> None:
                    yield from track.add_wagons([w])

                env.process(add_single_wagon(wagon))
                env.run()

                expected_occupied = (i + 1) * 20.0
                assert track.get_occupied_capacity() == expected_occupied
                assert track.get_wagon_count() == i + 1
            else:
                # Should not fit - we've reached capacity
                break

        # Should have added exactly 3 wagons (60m in 75m capacity)
        assert track.get_wagon_count() == 3
        assert track.get_occupied_capacity() == 60.0

        # 4th wagon should not fit
        assert track.can_fit_wagons([wagons_20m[3]]) is False

    def test_remove_wagons_frees_capacity(self, env: simpy.Environment, wagons_20m: list[Wagon]) -> None:
        """Test that removing wagons frees up capacity for new ones."""
        track = TrackCapacityManager(env, 'test_track', 75.0)

        # Add first 3 wagons
        first_three = wagons_20m[:3]

        def add_wagons() -> None:
            yield from track.add_wagons(first_three)

        env.process(add_wagons())
        env.run()

        assert track.get_wagon_count() == 3
        assert track.get_occupied_capacity() == 60.0

        # Remove one wagon (20m)
        def remove_one() -> None:
            yield from track.remove_wagons([first_three[0]])

        env.process(remove_one())
        env.run()

        assert track.get_wagon_count() == 2
        assert track.get_occupied_capacity() == 40.0
        assert track.get_available_capacity() == 35.0

        # Now 4th wagon should fit
        fourth_wagon = [wagons_20m[3]]
        assert track.can_fit_wagons(fourth_wagon) is True

        def add_fourth() -> None:
            yield from track.add_wagons(fourth_wagon)

        env.process(add_fourth())
        env.run()

        assert track.get_wagon_count() == 3
        assert track.get_occupied_capacity() == 60.0
