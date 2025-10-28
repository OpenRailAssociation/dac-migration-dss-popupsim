import sys
from pathlib import Path
from typing import List

import pytest

# Ensure src is on path for imports when tests are executed from repository root
ROOT: Path = Path(__file__).resolve().parents[4]  # repo root
SRC: Path = ROOT / 'popupsim' / 'backend' / 'src'
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from simulation.scenariosim import Scenario, ScenarioBuilder  # type: ignore


class FakeRoute:
    def __init__(self, route_id: str) -> None:
        self.route_id: str = route_id

    def __repr__(self) -> str:  # pragma: no cover - tiny helper
        return f'<FakeRoute {self.route_id}>'


class FakeWagon:
    def __init__(self, wagon_id: str) -> None:
        self.wagon_id: str = wagon_id

    def __repr__(self) -> str:  # pragma: no cover - tiny helper
        return f'<FakeWagon {self.wagon_id}>'


class FakeRoutes:
    def __init__(self) -> None:
        self._routes: List[FakeRoute] = []

    def append(self, route: FakeRoute) -> None:
        self._routes.append(route)

    @property
    def length(self) -> int:
        return len(self._routes)

    def __len__(self) -> int:
        return len(self._routes)


@pytest.mark.unit
def test_scenario_str_with_routes_and_wagons() -> None:
    routes: FakeRoutes = FakeRoutes()
    routes.append(FakeRoute('r1'))
    routes.append(FakeRoute('r2'))
    wagons: List[FakeWagon] = [FakeWagon('w1')]

    scenario: Scenario = Scenario(routes=routes, wagons=wagons)
    result: str = str(scenario)

    assert 'Scenario with' in result
    assert 'Routes' in result
    assert 'Wagons' in result
    assert f'{routes.length!s}' in result
    assert f'{len(wagons)!s}' in result


@pytest.mark.unit
def test_scenario_default_routes_and_wagons_are_empty() -> None:
    scenario: Scenario = Scenario()
    # default constructor currently sets routes to [] and wagons to []
    assert isinstance(scenario.routes, list)
    assert scenario.routes == []
    assert scenario.wagons == []


@pytest.mark.unit
def test_scenario_builder_chain_and_modifications() -> None:
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
