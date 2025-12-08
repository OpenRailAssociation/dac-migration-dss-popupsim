"""
Unit tests for ScenarioBuilder class.

Tests for loading and building complete scenarios from JSON configuration files
with references to tracks, trains, and routes data.
"""

from datetime import UTC, datetime
from pathlib import Path

import pytest

from popupsim.backend.src.MVP.configuration.application.scenario_builder import (
    ScenarioBuilder,
)


@pytest.fixture
def fixtures_scenario_json_path(fixtures_path: Path) -> Path:
    """Get path to scenario JSON fixture file.

    Parameters
    ----------
    fixtures_path : Path
        Path to fixtures directory.

    Returns
    -------
    Path
        Path to scenario.json fixture file.
    """
    scenario_file: Path = fixtures_path / "scenario.json"
    return scenario_file


class TestScenarioBuilder:
    """Test suite for ScenarioBuilder class."""

    def test_build_scenario_from_file(self, fixtures_scenario_json_path: Path) -> None:
        """Test building scenario from JSON file with basic validation.

        Parameters
        ----------
        fixtures_scenario_json_path : Path
            Path to scenario JSON fixture.
        """
        scenario = ScenarioBuilder(fixtures_scenario_json_path).build()

        assert scenario.id == "test_scenario_01"
        assert scenario.start_date.date() == datetime(2031, 7, 4, tzinfo=UTC).date()
        assert scenario.end_date.date() == datetime(2031, 7, 5, tzinfo=UTC).date()

    def test_build_scenario_with_refrences_from_file(
        self, fixtures_scenario_json_path: Path
    ) -> None:
        """Test building scenario with references to external data files.

        Parameters
        ----------
        fixtures_scenario_json_path : Path
            Path to scenario JSON fixture.

        Generic test to load scenario and its referenced tracks, trains, routes and workshops.
        """
        scenario = ScenarioBuilder(fixtures_scenario_json_path).build()

        assert scenario.id == "test_scenario_01"
        assert scenario.locomotives is not None
        assert len(scenario.locomotives) >= 1
        assert scenario.routes is not None
        assert len(scenario.routes) > 1
        assert scenario.tracks is not None
        assert len(scenario.tracks) > 1
        assert scenario.trains is not None
        assert len(scenario.trains) > 1
        assert scenario.workshops is not None
        assert len(scenario.workshops) > 1
