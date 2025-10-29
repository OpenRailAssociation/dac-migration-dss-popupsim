"""Unit tests for Scenario and ScenarioBuilder.

Simple pytest tests validating Scenario string output and builder behavior.
"""

from pathlib import Path
import sys

import pytest

# Ensure src is on path for imports when tests are executed from repository root
ROOT: Path = Path(__file__).resolve().parents[4]  # repo root
SRC: Path = ROOT / 'popupsim' / 'backend' / 'src'
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from simulation.scenario import Scenario, ScenarioBuilder  # type: ignore  # noqa: E402, I001


class FakeRoute:
    """Fake route used in tests.

    Parameters
    ----------
    route_id : str
        Route identifier.
    """

    def __init__(self, route_id: str) -> None:
        """Initialize FakeRoute.

        Parameters
        ----------
        route_id : str
            Route identifier.
        """
        self.route_id: str = route_id

    def __repr__(self) -> str:  # pragma: no cover - tiny helper
        """Return compact representation.

        Returns
        -------
        str
            Short textual representation.
        """
        return f'<FakeRoute {self.route_id}>'


class FakeWagon:
    """Fake wagon used in tests.

    Parameters
    ----------
    wagon_id : str
        Wagon identifier.
    """

    def __init__(self, wagon_id: str) -> None:
        """Initialize FakeWagon.

        Parameters
        ----------
        wagon_id : str
            Wagon identifier.
        """
        self.wagon_id: str = wagon_id

    def __repr__(self) -> str:  # pragma: no cover - tiny helper
        """Return compact representation.

        Returns
        -------
        str
            Short textual representation.
        """
        return f'<FakeWagon {self.wagon_id}>'


class FakeRoutes:
    """Minimal routes container used in tests.

    Provides append and length introspection.
    """

    def __init__(self) -> None:
        """Create empty FakeRoutes container."""
        self._routes: list[FakeRoute] = []

    def append(self, route: FakeRoute) -> None:
        """Append a route.

        Parameters
        ----------
        route : FakeRoute
            Route to append.
        """
        self._routes.append(route)

    @property
    def length(self) -> int:
        """Number of stored routes.

        Returns
        -------
        int
            Count of routes.
        """
        return len(self._routes)

    def __len__(self) -> int:
        """Sequence length.

        Returns
        -------
        int
            Count of routes.
        """
        return len(self._routes)


@pytest.mark.unit
def test_scenario_str_with_routes_and_wagons() -> None:
    """
    Test Scenario string representation with routes and wagons.

    Ensures that the string output of Scenario includes route and wagon information.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    routes: FakeRoutes = FakeRoutes()
    routes.append(FakeRoute('r1'))
    routes.append(FakeRoute('r2'))
    wagons: list[FakeWagon] = [FakeWagon('w1')]

    scenario: Scenario = Scenario(routes=routes, wagons=wagons)
    result: str = str(scenario)

    assert 'Scenario with' in result
    assert 'Routes' in result
    assert 'Wagons' in result
    assert f'{routes.length!s}' in result
    assert f'{len(wagons)!s}' in result


@pytest.mark.unit
def test_scenario_default_routes_and_wagons_are_empty() -> None:
    """
    Test that the Scenario class initializes with empty routes and wagons by default.

    Notes
    -----
    - Verifies that the `routes` and `wagons` attributes of a newly created Scenario instance are empty lists.
    - Ensures correct default behavior for Scenario initialization.
    """
    """Test that Scenario initializes with empty routes and wagons by default."""
    scenario: Scenario = Scenario()
    # default constructor currently sets routes to [] and wagons to []
    assert isinstance(scenario.routes, list)
    assert scenario.routes == []
    assert scenario.wagons == []


@pytest.mark.unit
def test_scenario_builder_chain_and_modifications() -> None:
    """
    Test ScenarioBuilder chaining and modifications.

    Parameters
    ----------
    None

    Returns
    -------
    None

    Notes
    -----
    Verifies that routes and wagons are correctly added and referenced in the built Scenario.
    """
    builder: ScenarioBuilder = ScenarioBuilder()
    # Prepare a FakeRoutes instance and some domain objects
    routes: FakeRoutes = FakeRoutes()
    route_a: FakeRoute = FakeRoute('ra')
    route_b: FakeRoute = FakeRoute('rb')
    wagon_a: FakeWagon = FakeWagon('wa')
    wagon_b: FakeWagon = FakeWagon('wb')

    # Chain add_routes and ensure builder is returned
    returned_builder: ScenarioBuilder = builder.add_routes(routes)
    assert returned_builder is builder

    # add_route should call FakeRoutes.append
    builder.add_route(route_a)
    assert routes.length == 1

    # add_wagon and add_wagons should modify the scenario wagons list
    builder.add_wagon(wagon_a)
    builder.add_wagons([wagon_b])

    # add another route via builder (calls append on FakeRoutes)
    builder.add_route(route_b)
    assert routes.length == 2

    scenario_built: Scenario = builder.build()
    assert scenario_built is builder.scenario
    # Scenario should reference the same routes object assigned above
    assert scenario_built.routes is routes
    # wagons should contain the two wagons added
    assert len(scenario_built.wagons) == 2
    assert scenario_built.wagons[0] is wagon_a
    assert scenario_built.wagons[1] is wagon_b
