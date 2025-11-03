"""Unit tests for Scenario and ScenarioBuilder.

Simple pytest tests validating Scenario string output and builder behavior.
"""

import pytest
from simulation.scenario import Scenario
from simulation.scenario import ScenarioBuilder

from configuration.model_route import Route
from configuration.model_routes import Routes
from configuration.model_wagon import Wagon


@pytest.mark.unit
def test_scenario_str_with_routes_and_wagons(mocker) -> None:
    """
    Test Scenario string representation with routes and wagons.

    Ensures that the string output of Scenario includes route and wagon information.
    """
    routes = mocker.MagicMock(spec=Routes)
    routes.length = 2

    wagon = mocker.MagicMock(spec=Wagon)
    wagons: list[Wagon] = [wagon]

    scenario: Scenario = Scenario(routes=routes, wagons=wagons)
    result: str = str(scenario)

    assert 'Scenario with' in result
    assert 'Routes' in result
    assert 'Wagons' in result
    assert '2' in result
    assert '1' in result


@pytest.mark.unit
def test_scenario_default_routes_and_wagons_are_empty(mocker) -> None:
    """
    Test that the Scenario class initializes with empty wagons by default.

    Notes
    -----
    - Verifies that the `wagons` attribute of a newly created Scenario instance is an empty list.
    - Ensures correct default behavior for Scenario initialization.
    """
    routes = mocker.MagicMock(spec=Routes)
    scenario: Scenario = Scenario(routes)
    # default constructor sets wagons to [] when not provided
    assert scenario.routes is routes
    assert scenario.wagons == []


@pytest.mark.unit
def test_scenario_builder_chain_and_modifications(mocker) -> None:
    """
    Test ScenarioBuilder chaining and modifications.

    Notes
    -----
    Verifies that routes and wagons are correctly added and referenced in the built Scenario.
    """
    builder: ScenarioBuilder = ScenarioBuilder()

    # Create mock objects
    routes = mocker.MagicMock(spec=Routes)
    route_a = mocker.MagicMock(spec=Route)
    route_b = mocker.MagicMock(spec=Route)
    wagon_a = mocker.MagicMock(spec=Wagon)
    wagon_b = mocker.MagicMock(spec=Wagon)

    # Chain add_routes and ensure builder is returned
    returned_builder: ScenarioBuilder = builder.add_routes(routes)
    assert returned_builder is builder

    # add_route should call Routes.append
    builder.add_route(route_a)
    routes.append.assert_called_with(route_a)

    # add_wagon and add_wagons should modify the scenario wagons list
    builder.add_wagon(wagon_a)
    builder.add_wagons([wagon_b])

    # add another route via builder
    builder.add_route(route_b)
    routes.append.assert_called_with(route_b)

    scenario_built: Scenario = builder.build()
    assert scenario_built is builder.scenario
    # Scenario should reference the same routes object assigned above
    assert scenario_built.routes is routes
    # wagons should contain the two wagons added
    assert len(scenario_built.wagons) == 2
    assert scenario_built.wagons[0] is wagon_a
    assert scenario_built.wagons[1] is wagon_b
