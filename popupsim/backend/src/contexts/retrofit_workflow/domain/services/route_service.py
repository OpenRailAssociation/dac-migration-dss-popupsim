"""Route service for transportation time calculations in railway operations.

This module provides services for looking up and calculating transport durations
between different locations in the DAC migration simulation system. It manages
route configurations and provides standardized access to timing information.
"""

from shared.infrastructure.simpy_time_converters import timedelta_to_sim_ticks


class RouteService:
    """Service for managing route durations and transportation time calculations.

    This service provides centralized access to route timing information used
    throughout the DAC migration simulation. It handles route configuration
    parsing and provides convenient methods for common route queries.

    Attributes
    ----------
    route_durations : dict[tuple[str, str], float]
        Dictionary mapping (from_location, to_location) tuples to duration values

    Route Types Supported
    ---------------------
    - Collection to retrofit track transport
    - Retrofit track to workshop transport
    - Workshop to retrofitted track transport
    - Retrofitted track to parking transport
    - Custom location-to-location routes

    Notes
    -----
    All durations are normalized to simulation time units (minutes by default).
    Missing routes default to 1.0 minute for system resilience.

    Examples
    --------
    >>> routes = [route1, route2, route3]  # RouteInputDTO objects
    >>> service = RouteService(routes)
    >>> duration = service.get_duration('collection', 'retrofit')
    >>> print(f'Transport time: {duration} minutes')
    """

    def __init__(self, routes: list) -> None:
        """Initialize the route service with scenario route configurations.

        Processes route configuration data and builds internal lookup structures
        for efficient duration queries during simulation execution.

        Parameters
        ----------
        routes : list
            List of RouteInputDTO objects from scenario configuration

        Notes
        -----
        The initialization process:
        1. Extracts start and end locations from route paths
        2. Converts duration values to simulation time units
        3. Builds lookup dictionary for O(1) duration queries
        4. Handles both timedelta and numeric duration formats

        Examples
        --------
        >>> from scenario_config import load_routes
        >>> routes = load_routes('scenario.json')
        >>> service = RouteService(routes)
        """
        # Build lookup dict: (from, to) -> duration
        self.route_durations: dict[tuple[str, str], float] = {}

        for route in routes:
            if len(route.path) >= 2:
                from_location = route.path[0]
                to_location = route.path[-1]
                duration = route.duration
                # Convert timedelta to SimPy ticks (minutes by default)
                if hasattr(duration, 'total_seconds'):
                    duration = timedelta_to_sim_ticks(duration)
                self.route_durations[(from_location, to_location)] = float(duration)

    def get_duration(self, from_location: str, to_location: str) -> float:
        """Get transport duration between two specified locations.

        Looks up the configured transport time between the specified locations,
        providing a default value if the route is not explicitly configured.

        Parameters
        ----------
        from_location : str
            Starting location identifier
        to_location : str
            Destination location identifier

        Returns
        -------
        float
            Transport duration in simulation time units (minutes)

        Notes
        -----
        Returns 1.0 minute as default if route not found, ensuring system
        resilience and preventing simulation failures due to missing routes.

        Examples
        --------
        >>> service = RouteService(routes)
        >>> duration = service.get_duration('TRACK_A', 'WORKSHOP_01')
        >>> print(f'Transport time: {duration} minutes')
        >>> # Unknown route gets default duration
        >>> unknown_duration = service.get_duration('UNKNOWN_A', 'UNKNOWN_B')
        >>> assert unknown_duration == 1.0
        """
        return self.route_durations.get((from_location, to_location), 1.0)

    def get_collection_to_retrofit_time(self) -> float:
        """Get standardized transport time from collection to retrofit track.

        Convenience method for the common collection-to-retrofit transport
        operation in the DAC migration workflow.

        Returns
        -------
        float
            Transport duration in simulation time units (minutes)

        Notes
        -----
        This represents the time required to move wagons from the collection
        area where trains arrive to the retrofit staging area.

        Examples
        --------
        >>> service = RouteService(routes)
        >>> transport_time = service.get_collection_to_retrofit_time()
        >>> print(f'Collection to retrofit: {transport_time} minutes')
        """
        return self.get_duration('collection', 'retrofit')

    def get_retrofit_to_workshop_time(self, workshop_id: str) -> float:
        """Get transport time from retrofit track to specified workshop.

        Calculates the time required to transport wagons from the retrofit
        staging area to a specific workshop for processing.

        Parameters
        ----------
        workshop_id : str
            Target workshop identifier

        Returns
        -------
        float
            Transport duration in simulation time units (minutes)

        Notes
        -----
        Different workshops may have different transport times based on
        their physical location relative to the retrofit track.

        Examples
        --------
        >>> service = RouteService(routes)
        >>> time_to_ws1 = service.get_retrofit_to_workshop_time('WORKSHOP_01')
        >>> time_to_ws2 = service.get_retrofit_to_workshop_time('WORKSHOP_02')
        """
        return self.get_duration('retrofit', workshop_id)

    def get_workshop_to_retrofitted_time(self, workshop_id: str) -> float:
        """Get transport time from specified workshop to retrofitted track.

        Calculates the time required to transport completed wagons from a
        workshop back to the retrofitted staging area.

        Parameters
        ----------
        workshop_id : str
            Source workshop identifier

        Returns
        -------
        float
            Transport duration in simulation time units (minutes)

        Notes
        -----
        This represents the return journey time after wagon processing
        is completed at the workshop.

        Examples
        --------
        >>> service = RouteService(routes)
        >>> return_time = service.get_workshop_to_retrofitted_time('WORKSHOP_01')
        >>> print(f'Workshop return time: {return_time} minutes')
        """
        return self.get_duration(workshop_id, 'retrofitted')

    def get_retrofitted_to_parking_time(self) -> float:
        """Get standardized transport time from retrofitted to parking track.

        Convenience method for the final transport operation in the DAC
        migration workflow, moving completed wagons to long-term parking.

        Returns
        -------
        float
            Transport duration in simulation time units (minutes)

        Notes
        -----
        This represents the final stage of the migration process where
        retrofitted wagons are moved to their parking locations.

        Examples
        --------
        >>> service = RouteService(routes)
        >>> parking_time = service.get_retrofitted_to_parking_time()
        >>> print(f'Final parking transport: {parking_time} minutes')
        """
        return self.get_duration('retrofitted', 'parking')
