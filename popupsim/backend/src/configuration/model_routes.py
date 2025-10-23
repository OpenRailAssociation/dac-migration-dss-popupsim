"""
Routes loader module for the simulation.

This module provides functionality to load route configurations from CSV files,
validate them using the Route model, and make them available to the simulation.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Union

import pandas as pd

from .model_route import Route

# Configure logging
logger = logging.getLogger(__name__)


class RoutesConfig:
    """
    Routes configuration manager that loads and provides access to route data.

    This class is responsible for loading route configurations from a CSV file,
    validating them through the Route model, and providing convenient access
    to route information for the simulation.
    """

    def __init__(self, routes_file: Optional[Union[str, Path]] = None):
        """
        Initialize the routes configuration manager.

        Args:
            routes_file: Path to the CSV file containing route data. If None, no routes are loaded initially.
        """
        self.routes: List[Route] = []
        self.routes_by_id: Dict[str, Route] = {}

        if routes_file:
            self.load_routes(routes_file)

    def load_routes(self, csv_path: Union[str, Path]) -> None:
        """
        Load routes from a CSV file.

        Args:
            csv_path: Path to the CSV file containing route data

        Raises:
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
        """
        Get a route by its ID.

        Args:
            route_id: The ID of the route to retrieve

        Returns:
            The Route object with the specified ID

        Raises:
            KeyError: If no route with the specified ID exists
        """
        if route_id not in self.routes_by_id:
            raise KeyError(f'Route not found: {route_id}')

        return self.routes_by_id[route_id]

    def get_route_between_tracks(self, from_track: str, to_track: str) -> Optional[Route]:
        """
        Find a route between two tracks.

        Args:
            from_track: The starting track ID
            to_track: The destination track ID

        Returns:
            The Route object connecting the tracks, or None if no route exists
        """
        for route in self.routes:
            if route.from_track == from_track and route.to_track == to_track:
                return route

        return None

    def __len__(self) -> int:
        """Return the number of loaded routes."""
        return len(self.routes)

    def __iter__(self):
        """Iterate through all routes."""
        return iter(self.routes)


def load_routes_from_csv(csv_path: Union[str, Path]) -> List[Route]:
    """
    Load routes from a CSV file and return as a list of Route objects.

    This is a convenience function that creates a RoutesConfig instance,
    loads the routes, and returns the list of Route objects.

    Args:
        csv_path: Path to the CSV file containing route data

    Returns:
        List of validated Route objects

    Raises:
        FileNotFoundError: If the CSV file does not exist
        ValueError: If the CSV file contains invalid route data
    """
    routes_config = RoutesConfig(csv_path)
    return routes_config.routes
