"""Routes loader module for the simulation.

This module provides functionality to load route configurations from CSV files,
validate them using the Route model, and make them available to the simulation.
"""

from collections.abc import Iterator
import logging
from pathlib import Path

import pandas as pd

from .model_route import Route

# Configure logging
logger = logging.getLogger(__name__)


class Routes:
    """
    Routes configuration manager that loads and provides access to route data.

    This class is responsible for loading route configurations from a CSV file,
    validating them through the Route model, and providing convenient access
    to route information for the simulation.
    """

    def __init__(self, routes_file: str | Path | None = None, routes: list[Route] | None = None) -> None:
        """
        Initialize the routes configuration manager.

        Args:
            routes_file: Path to the CSV file containing route data. If None, no routes are loaded initially.
        """
        if routes is not None and len(routes or []) > 0:
            self.routes = routes
            self.routes_by_id = {route.route_id: route for route in routes}
            return

        if routes_file is None:
            self.routes: list[Route] = []  # type: ignore[no-redef]  # for now: suppress mypy no-redef false positive
            self.routes_by_id: dict[str, Route] = {}  # type: ignore[no-redef]
            return

        if routes_file:
            self.load_routes(routes_file)
            return

    def load_routes(self, csv_path: str | Path) -> None:
        """
        Load routes from a CSV file.

        Args:
            csv_path: Path to the CSV file containing route data

        Raises
        ------
            FileNotFoundError: If the CSV file does not exist
            ValueError: If the CSV file contains invalid route data
        """
        path = Path(csv_path)
        if not path.exists():
            raise FileNotFoundError(f'Routes file not found: {path}')

        try:
            logger.info('Loading routes from CSV file: %s', path)
            df = pd.read_csv(path, sep=';')

            # Validate required columns
            required_columns = ['route_id', 'from_track', 'to_track', 'track_sequence', 'distance_m', 'time_min']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise ValueError(f'Missing required columns in CSV: {", ".join(missing_columns)}')

            # Clear existing routes
            self.routes = []
            self.routes_by_id = {}

            # Convert DataFrame to list of Route objects
            for _, row in df.iterrows():
                try:
                    track_sequence = row['track_sequence']
                    track_sequence = track_sequence.replace('"', '').replace("'", '')
                    track_sequence = [item.strip() for item in track_sequence.split(',')]
                    # Ensure track_sequence is treated as a string for parsing
                    route = Route(
                        route_id=row['route_id'],
                        from_track=row['from_track'],
                        to_track=row['to_track'],
                        track_sequence=track_sequence,
                        distance_m=row['distance_m'],
                        time_min=row['time_min'],
                    )
                    self.routes.append(route)
                    self.routes_by_id[route.route_id] = route
                except Exception as e:
                    route_id = row.get('route_id', 'unknown')
                    logger.error('Error parsing route %s: %s', route_id, str(e))
                    raise ValueError(f'Error parsing route {route_id}: {e!s}') from e

            logger.info('Successfully loaded %d routes from %s', len(self.routes), path)

        except Exception as e:
            if not isinstance(e, (FileNotFoundError, ValueError)):
                logger.error('Failed to load routes from CSV: %s', str(e))
                raise ValueError(f'Failed to load routes from CSV: {e!r}') from e
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
            raise KeyError(f'Route not found: {route_id}')

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
        """
        Append a Route to the collection.

        Args:
            route: Route instance to add

        Raises
        ------
            ValueError: If a route with the same route_id already exists
        """
        if route.route_id in self.routes_by_id:
            raise ValueError(f'Route already exists: {route.route_id}')
        self.routes.append(route)
        self.routes_by_id[route.route_id] = route

    @property
    def length(self) -> int:
        """Return the number of loaded routes."""
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


def load_routes_from_csv(csv_path: str | Path) -> list[Route]:
    """Load routes from a CSV file and return as a list of Route objects.

    This is a convenience function that creates a RoutesConfig instance,
    loads the routes, and returns the list of Route objects.

    Parameters
    ----------
    csv_path : str or Path
        Path to the CSV file containing route data.

    Returns
    -------
    list[Route]
        List of validated Route objects.

    Raises
    ------
    FileNotFoundError
        If the CSV file does not exist.
    ValueError
        If the CSV file contains invalid route data.
    """
    routes = Routes(csv_path)
    return routes.routes
