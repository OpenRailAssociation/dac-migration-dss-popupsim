"""Utility to find routes between tracks."""

from MVP.workshop_operations.domain.value_objects.route import (
    Route,
)


def find_route(routes: list[Route], from_track: str, to_track: str) -> Route | None:
    """Find route from one track to another by searching route paths.

    Parameters
    ----------
    routes : list[Route]
        List of available routes
    from_track : str
        Starting track ID
    to_track : str
        Destination track ID

    Returns
    -------
    Route | None
        Route if found, None otherwise
    """
    for route in routes:
        if route.from_track == from_track and route.to_track == to_track:
            return route
    return None
