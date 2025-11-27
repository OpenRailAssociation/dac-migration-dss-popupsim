"""Tests for TrainInputDTO."""

from pydantic import ValidationError
import pytest

from configuration.application.dtos.train_input_dto import TrainInputDTO
from configuration.application.dtos.wagon_input_dto import WagonInputDTO


class TestTrainInputDTO:
    """Test TrainInputDTO validation."""

    def test_valid_train_dto(self) -> None:
        """Test creating valid TrainInputDTO."""
        wagon = WagonInputDTO(id='W001', length=15.5, is_loaded=False, needs_retrofit=True)
        dto = TrainInputDTO(
            train_id='T001',
            arrival_time='2025-01-01T08:00:00',
            departure_time='2025-01-01T09:00:00',
            locomotive_id='L001',
            route_id='R001',
            wagons=[wagon],
        )

        assert dto.train_id == 'T001'
        assert len(dto.wagons) == 1
        assert dto.wagons[0].id == 'W001'

    def test_invalid_train_id_pattern(self) -> None:
        """Test validation fails for invalid train_id pattern."""
        wagon = WagonInputDTO(id='W001', length=15.5)
        with pytest.raises(ValidationError):
            TrainInputDTO(
                train_id='invalid train!',
                arrival_time='2025-01-01T08:00:00',
                departure_time='2025-01-01T09:00:00',
                locomotive_id='L001',
                route_id='R001',
                wagons=[wagon],
            )

    def test_invalid_time_order(self) -> None:
        """Test validation fails when departure is before arrival."""
        wagon = WagonInputDTO(id='W001', length=15.5)
        with pytest.raises(ValidationError):
            TrainInputDTO(
                train_id='T001',
                arrival_time='2025-01-01T09:00:00',
                departure_time='2025-01-01T08:00:00',
                locomotive_id='L001',
                route_id='R001',
                wagons=[wagon],
            )

    def test_invalid_wagon_count(self) -> None:
        """Test validation fails for empty wagon list."""
        with pytest.raises(ValidationError):
            TrainInputDTO(
                train_id='T001',
                arrival_time='2025-01-01T08:00:00',
                departure_time='2025-01-01T09:00:00',
                locomotive_id='L001',
                route_id='R001',
                wagons=[],
            )
