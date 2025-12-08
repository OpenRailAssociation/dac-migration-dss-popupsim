"""Routes loader module for the simulation.

This module provides functionality to load route configurations from CSV files,
validate them using the Route model, and make them available to the simulation.
"""

import json
import logging
from collections.abc import Iterator
from pathlib import Path

from pydantic import BaseModel, Field

from .route import Route

# Configure logging
logger = logging.getLogger(__name__)


class MetaData(BaseModel):
    """Metadata for the routes configuration."""

    description: str = Field(description="Description of the routes configuration")
    version: str = Field(description="Version of the routes configuration")
    topology_reference: str = Field(
        description="Reference to the topology configuration used"
    )
    tracks_reference: str = Field(
        description="Reference to the tracks configuration used"
    )


class Routes:
    """Routes models manager that loads and provides access to route data.

    This class is responsible for loading route configurations from a CSV file,
    validating them through the Route model, and providing convenient access
    to route information for the simulation.
    """

    def __init__(
        self, routes_file: str | Path | None = None, routes: list[Route] | None = None
    ) -> None:
        """Initialize the routes models manager.

        Parameters
        ----------
        routes_file : str or Path or None, optional
            Path to the CSV file containing route data. If None, no routes are loaded initially.
        routes : list[Route] or None, optional
            List of Route objects to initialize with. If provided, takes precedence over routes_file.
        """
        self.metadata: MetaData | None = None
        self.routes: list[Route] = []  # type: ignore[no-redef]  # for now: suppress mypy no-redef false positive
        self.routes_by_id: dict[str, Route] = {}  # type: ignore[no-redef]

        if routes is not None and len(routes or []) > 0:
            self.routes = routes
            self.routes_by_id = {route.route_id: route for route in routes}
            return

        if routes_file:
            self.load_routes(routes_file)
            return

    def load_routes(self, file_path: str | Path) -> None:  # noqa: C901
        """Load routes from a JSON file.

        Parameters
        ----------
        file_path : str | Path
            Path to the JSON file containing route data.

        Raises
        ------
        FileNotFoundError
            If the JSON file does not exist.
        ValueError
            If the JSON file contains invalid route data or missing 'routes' key.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Routes file not found: {path}")

        if not path.is_file():
            path = path / "routes.json"
            if not path.exists():
                raise FileNotFoundError(f"Routes file not found: {path}")

        try:
            logger.info("Loading routes from JSON file: %s", path)

            with path.open("r", encoding="utf-8") as f:
                data: dict[str, object] = json.load(f)

            if "metadata" not in data:
                raise ValueError('Missing "metadata" key in JSON file')
            self.metadata = MetaData(**data["metadata"])  # type: ignore[arg-type]

            if "routes" not in data:
                raise ValueError('Missing "routes" key in JSON file')

            routes_data: list[dict[str, object]] = data.get("routes")  # type: ignore[assignment]

            # Clear existing routes
            self.routes = []
            self.routes_by_id = {}

            # Convert JSON data to Route objects
            for route_dict in routes_data:
                try:
                    route: Route = Route(**route_dict)  # type: ignore[arg-type]
                    self.routes.append(route)
                    self.routes_by_id[route.route_id] = route
                except Exception as e:
                    route_id: str = str(route_dict.get("id", "unknown"))
                    raise ValueError(f"Error parsing route {route_id}: {e!s}") from e

            logger.info("Successfully loaded %d routes from %s", len(self.routes), path)

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format in {path}: {e!s}") from e
        except Exception as e:
            if not isinstance(e, (FileNotFoundError, ValueError)):
                raise ValueError(f"Failed to load routes from JSON: {e!r}") from e
            raise

    def get_route(self, route_id: str) -> Route:
        """Get a route by its ID.

        Parameters
        ----------
        route_id : str
            The ID of the route to retrieve.

        Returns
        -------
        Route
            The Route object with the specified ID.

        Raises
        ------
        KeyError
            If no route with the specified ID exists.
        """
        if route_id not in self.routes_by_id:
            raise KeyError(f"Route not found: {route_id}")

        return self.routes_by_id[route_id]

    def get_route_between_tracks(self, from_track: str, to_track: str) -> Route | None:
        """Find a route between two tracks.

        Parameters
        ----------
        from_track : str
            The starting track ID.
        to_track : str
            The destination track ID.

        Returns
        -------
        Route or None
            The Route object connecting the tracks, or None if no route exists.
        """
        for route in self.routes:
            if route.from_track == from_track and route.to_track == to_track:
                return route

        return None

    def append(self, route: Route) -> None:
        """Append a Route to the collection.

        Parameters
        ----------
        route : Route
            Route instance to add.

        Raises
        ------
        ValueError
            If a route with the same route_id already exists.
        """
        if route.route_id in self.routes_by_id:
            raise ValueError(f"Route already exists: {route.route_id}")
        self.routes.append(route)
        self.routes_by_id[route.route_id] = route

    @property
    def length(self) -> int:
        """Return the number of loaded routes.

        Returns
        -------
        int
            Number of loaded routes.
        """
        return len(self.routes)

    def __len__(self) -> int:
        """Return the number of loaded routes.

        Returns
        -------
        int
            Number of loaded routes.
        """
        return len(self.routes)

    def __iter__(self) -> Iterator[Route]:
        """Iterate through all routes.

        Returns
        -------
        Iterator[Route]
            Iterator over all loaded routes.
        """
        return iter(self.routes)
