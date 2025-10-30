"""Scenario builder and container for PopUp-Sim.

Provides a lightweight Scenario value object that groups loaded Routes and Wagons
and a fluent ScenarioBuilder to construct scenarios for simulation tests and
runtime usage.
"""

from __future__ import annotations

# The configuration.* modules are available at runtime but currently ship without
# library stubs / a py.typed marker which makes mypy emit noise. Suppress the
# import-not-found error for now and keep a NOTE for future cleanup.
# for now: missing stubs / py.typed
# pylint: disable=import-error  # local/dev import layout may differ until editable install is used
from configuration.model_route import Route  # type: ignore[import-not-found,import-untyped]
from configuration.model_routes import Routes  # type: ignore[import-not-found,import-untyped]
from configuration.model_wagon import Wagon  # type: ignore[import-not-found,import-untyped]


class Scenario:
    """Container for simulation scenario data.

    Attributes
    ----------
    routes : Routes or None
        A Routes collection (or empty list when not set).
    wagons : list[Wagon]
        A list of Wagon instances.
    """

    def __init__(self, routes: Routes | None = None, wagons: list[Wagon] | None = None) -> None:
        """Create a Scenario.

        Parameters
        ----------
        routes : Routes or None, optional
            Optional Routes collection to use for the scenario.
        wagons : list[Wagon] or None, optional
            Optional list of Wagon instances.
        """
        self.routes: Routes | None = routes or []
        self.wagons: list[Wagon] = wagons or []

    def __str__(self) -> str:
        """Return a short human-readable description of the scenario.

        Returns
        -------
        str
            String representation with route and wagon counts.
        """
        route_count: int = 0 if self.routes is None else self.routes.length
        return f'Scenario with {route_count!s} Routes and {len(self.wagons)!s} Wagons'

    @property
    def route_count(self) -> int:
        """Number of routes in the scenario (public helper to satisfy linters).

        Returns
        -------
        int
            Count of routes in the scenario.
        """
        return 0 if self.routes is None else self.routes.length

    def __len__(self) -> int:
        """Return the number of wagons (makes Scenario usable with len()).

        Returns
        -------
        int
            Number of wagons in the scenario.
        """
        return len(self.wagons)


class ScenarioBuilder:
    """Fluent builder for Scenario instances.

    Examples
    --------
    >>> scenario = ScenarioBuilder().add_routes(routes).add_wagon(wagon).build()
    """

    def __init__(self) -> None:
        """Initialize an empty builder with a default Scenario."""
        self.scenario: Scenario = Scenario()

    def add_routes(self, routes: Routes) -> ScenarioBuilder:
        """Assign a Routes collection to the Scenario and return the builder.

        Parameters
        ----------
        routes : Routes
            Routes collection to assign.

        Returns
        -------
        ScenarioBuilder
            The same ScenarioBuilder instance for chaining.
        """
        self.scenario.routes = routes
        return self

    def add_route(self, route: Route) -> ScenarioBuilder:
        """Append a Route to the Scenario's Routes collection.

        Parameters
        ----------
        route : Route
            Route to append.

        Returns
        -------
        ScenarioBuilder
            The same ScenarioBuilder instance for chaining.
        """
        if self.scenario.routes is None:
            self.scenario.routes = Routes()
        self.scenario.routes.append(route)
        return self

    def add_wagon(self, wagon: Wagon) -> ScenarioBuilder:
        """Append a Wagon to the Scenario's wagon list.

        Parameters
        ----------
        wagon : Wagon
            Wagon to append.

        Returns
        -------
        ScenarioBuilder
            The same ScenarioBuilder instance for chaining.
        """
        self.scenario.wagons.append(wagon)
        return self

    def add_wagons(self, wagons: list[Wagon]) -> ScenarioBuilder:
        """Extend the Scenario's wagon list with multiple wagons.

        Parameters
        ----------
        wagons : list[Wagon]
            List of Wagon instances to add.

        Returns
        -------
        ScenarioBuilder
            The same ScenarioBuilder instance for chaining.
        """
        self.scenario.wagons.extend(wagons)
        return self

    def build(self) -> Scenario:
        """Return the constructed Scenario instance.

        Returns
        -------
        Scenario
            The built Scenario.
        """
        return self.scenario
