"""Tests for WorkshopInputDTO."""

import pytest
from pydantic import ValidationError

from popupsim.backend.src.MVP.configuration.application.dtos.workshop_input_dto import (
    WorkshopInputDTO,
)


class TestWorkshopInputDTO:
    """Test WorkshopInputDTO validation."""

    def test_valid_workshop_dto(self) -> None:
        """Test creating valid WorkshopInputDTO."""
        dto = WorkshopInputDTO(
            id="WS001",
            track="T001",
            retrofit_stations=5,
        )

        assert dto.id == "WS001"
        assert dto.track == "T001"
        assert dto.retrofit_stations == 5

    def test_invalid_track_type(self) -> None:
        """Test validation fails for invalid id."""
        with pytest.raises(ValidationError):
            WorkshopInputDTO(
                id="",
                track="T001",
                retrofit_stations=5,
            )

    def test_invalid_track_pattern(self) -> None:
        """Test validation fails for invalid track."""
        with pytest.raises(ValidationError):
            WorkshopInputDTO(
                id="WS001",
                track="",
                retrofit_stations=5,
            )

    def test_invalid_capacity(self) -> None:
        """Test validation fails for invalid retrofit_stations."""
        with pytest.raises(ValidationError):
            WorkshopInputDTO(
                id="WS001",
                track="T001",
                retrofit_stations=0,
            )
