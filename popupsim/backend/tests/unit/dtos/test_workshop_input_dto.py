"""Tests for WorkshopInputDTO."""

from pydantic import ValidationError
import pytest

from configuration.application.dtos.workshop_input_dto import WorkshopInputDTO


class TestWorkshopInputDTO:
    """Test WorkshopInputDTO validation."""

    def test_valid_workshop_dto(self) -> None:
        """Test creating valid WorkshopInputDTO."""
        dto = WorkshopInputDTO(
            workshop_id='WS001',
            track_id='T001',
            retrofit_stations=5,
        )

        assert dto.workshop_id == 'WS001'
        assert dto.track_id == 'T001'
        assert dto.retrofit_stations == 5

    def test_invalid_track_type(self) -> None:
        """Test validation fails for invalid workshop_id."""
        with pytest.raises(ValidationError):
            WorkshopInputDTO(
                workshop_id='',
                track_id='T001',
                retrofit_stations=5,
            )

    def test_invalid_track_id_pattern(self) -> None:
        """Test validation fails for invalid track_id."""
        with pytest.raises(ValidationError):
            WorkshopInputDTO(
                workshop_id='WS001',
                track_id='',
                retrofit_stations=5,
            )

    def test_invalid_capacity(self) -> None:
        """Test validation fails for invalid retrofit_stations."""
        with pytest.raises(ValidationError):
            WorkshopInputDTO(
                workshop_id='WS001',
                track_id='T001',
                retrofit_stations=0,
            )
