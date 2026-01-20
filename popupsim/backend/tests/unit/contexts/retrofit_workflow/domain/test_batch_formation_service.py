"""Tests for BatchFormationService domain service."""

from contexts.retrofit_workflow.domain.entities.wagon import Wagon
from contexts.retrofit_workflow.domain.entities.workshop import create_workshop
from contexts.retrofit_workflow.domain.services.batch_formation_service import BatchFormationService
from contexts.retrofit_workflow.domain.value_objects.coupler import Coupler
from contexts.retrofit_workflow.domain.value_objects.coupler import CouplerType
import pytest


class TestBatchFormationService:
    """Test BatchFormationService domain service."""

    @pytest.fixture
    def service(self) -> BatchFormationService:
        """Create service instance."""
        return BatchFormationService()

    @pytest.fixture
    def wagons(self) -> list[Wagon]:
        """Create test wagons."""
        return [
            Wagon(
                id=f'wagon_{i}',
                length=15.0,
                coupler_a=Coupler(CouplerType.SCREW, 'A'),
                coupler_b=Coupler(CouplerType.SCREW, 'B'),
            )
            for i in range(5)
        ]

    def test_form_batch_for_retrofit_track_fits_all(self, service: BatchFormationService, wagons: list[Wagon]) -> None:
        """Test batch formation when all wagons fit."""
        batch = service.form_batch_for_retrofit_track(wagons, 100.0)

        assert len(batch) == 5
        assert batch == wagons

    def test_form_batch_for_retrofit_track_partial_fit(
        self, service: BatchFormationService, wagons: list[Wagon]
    ) -> None:
        """Test batch formation when only some wagons fit."""
        batch = service.form_batch_for_retrofit_track(wagons, 35.0)  # Fits 2 wagons (30m)

        assert len(batch) == 2
        assert batch == wagons[:2]

    def test_form_batch_for_retrofit_track_none_fit(self, service: BatchFormationService, wagons: list[Wagon]) -> None:
        """Test batch formation when no wagons fit."""
        batch = service.form_batch_for_retrofit_track(wagons, 10.0)

        assert len(batch) == 0

    def test_form_batch_for_retrofit_track_empty_wagons(self, service: BatchFormationService) -> None:
        """Test batch formation with empty wagon list."""
        batch = service.form_batch_for_retrofit_track([], 100.0)

        assert len(batch) == 0

    def test_form_batch_for_workshop_available_bays(self, service: BatchFormationService, wagons: list[Wagon]) -> None:
        """Test batch formation based on available workshop bays."""
        workshop = create_workshop('ws_1', 'track_1', 3)

        batch = service.form_batch_for_workshop(wagons, workshop)

        assert len(batch) == 3  # Limited by available bays
        assert batch == wagons[:3]

    def test_form_batch_for_workshop_fewer_wagons(self, service: BatchFormationService) -> None:
        """Test batch formation when fewer wagons than bays."""
        workshop = create_workshop('ws_1', 'track_1', 5)
        wagons = [
            Wagon(
                id='wagon_1',
                length=15.0,
                coupler_a=Coupler(CouplerType.SCREW, 'A'),
                coupler_b=Coupler(CouplerType.SCREW, 'B'),
            ),
            Wagon(
                id='wagon_2',
                length=15.0,
                coupler_a=Coupler(CouplerType.SCREW, 'A'),
                coupler_b=Coupler(CouplerType.SCREW, 'B'),
            ),
        ]

        batch = service.form_batch_for_workshop(wagons, workshop)

        assert len(batch) == 2  # Limited by available wagons
        assert batch == wagons

    def test_form_batch_for_workshop_no_available_bays(
        self, service: BatchFormationService, wagons: list[Wagon]
    ) -> None:
        """Test batch formation when no bays available."""
        workshop = create_workshop('ws_1', 'track_1', 2)
        # Occupy all bays
        workshop.assign_to_bay('existing_1', 10.0)
        workshop.assign_to_bay('existing_2', 10.0)

        batch = service.form_batch_for_workshop(wagons, workshop)

        assert len(batch) == 0

    def test_form_batch_for_parking_track_fits_all(self, service: BatchFormationService, wagons: list[Wagon]) -> None:
        """Test parking batch formation when all wagons fit."""
        batch = service.form_batch_for_parking_track(wagons, 100.0)

        assert len(batch) == 5
        assert batch == wagons

    def test_form_batch_for_parking_track_partial_fit(
        self, service: BatchFormationService, wagons: list[Wagon]
    ) -> None:
        """Test parking batch formation when only some wagons fit."""
        batch = service.form_batch_for_parking_track(wagons, 50.0)  # Fits 3 wagons (45m)

        assert len(batch) == 3
        assert batch == wagons[:3]

    def test_calculate_batch_size_for_workshop(self, service: BatchFormationService) -> None:
        """Test batch size calculation for workshop."""
        workshop = create_workshop('ws_1', 'track_1', 3)

        # More wagons than bays
        size = service.calculate_batch_size_for_workshop(workshop, 5)
        assert size == 3

        # Fewer wagons than bays
        size = service.calculate_batch_size_for_workshop(workshop, 2)
        assert size == 2

        # Equal wagons and bays
        size = service.calculate_batch_size_for_workshop(workshop, 3)
        assert size == 3

    def test_can_form_batch_success(self, service: BatchFormationService, wagons: list[Wagon]) -> None:
        """Test successful batch formation check."""
        assert service.can_form_batch(wagons, 1) is True
        assert service.can_form_batch(wagons, 5) is True
        assert service.can_form_batch(wagons[:2], 2) is True

    def test_can_form_batch_failure(self, service: BatchFormationService, wagons: list[Wagon]) -> None:
        """Test failed batch formation check."""
        assert service.can_form_batch(wagons, 6) is False
        assert service.can_form_batch([], 1) is False
        assert service.can_form_batch(wagons[:2], 3) is False
