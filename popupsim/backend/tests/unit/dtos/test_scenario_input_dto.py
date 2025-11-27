"""Tests for ScenarioInputDTO."""

from pydantic import ValidationError
import pytest

from configuration.application.dtos.scenario_input_dto import ScenarioInputDTO


class TestScenarioInputDTO:
    """Test ScenarioInputDTO validation."""

    def test_valid_scenario_dto(self) -> None:
        """Test creating valid ScenarioInputDTO."""
        dto = ScenarioInputDTO(
            id='test_scenario',
            start_date='2025-01-01',
            end_date='2025-01-02',
            train_schedule_file='trains.csv',
            routes_file='routes.csv',
            workshop_tracks_file='tracks.csv',
        )

        assert dto.id == 'test_scenario'
        assert dto.start_date == '2025-01-01'
        assert dto.end_date == '2025-01-02'

    def test_missing_required_fields(self) -> None:
        """Test validation fails for missing required fields."""
        with pytest.raises(ValidationError):
            ScenarioInputDTO()

    def test_empty_scenario_id(self) -> None:
        """Test validation fails for empty scenario_id."""
        with pytest.raises(ValidationError):
            ScenarioInputDTO(
                id='',
                start_date='2025-01-01',
                end_date='2025-01-02',
            )

    def test_invalid_scenario_id_pattern(self) -> None:
        """Test validation fails for invalid scenario_id pattern."""
        with pytest.raises(ValidationError):
            ScenarioInputDTO(
                id='invalid scenario!',
                start_date='2025-01-01',
                end_date='2025-01-02',
            )

    def test_invalid_date_order(self) -> None:
        """Test validation fails when end_date is before start_date."""
        with pytest.raises(ValidationError):
            ScenarioInputDTO(
                id='test',
                start_date='2025-01-02',
                end_date='2025-01-01',
            )

    def test_invalid_strategy_values(self) -> None:
        """Test validation fails for invalid strategy values."""
        with pytest.raises(ValidationError):
            ScenarioInputDTO(
                id='test',
                start_date='2025-01-01',
                end_date='2025-01-02',
                track_selection_strategy='invalid_strategy',
            )
