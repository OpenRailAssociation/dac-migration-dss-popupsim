"""Railway Infrastructure Context - application layer."""

from typing import Any

from contexts.configuration.domain.models.scenario import Scenario
from contexts.railway_infrastructure.domain.services.topology_service import TopologyService


class RailwayInfrastructureContext:
    """Railway Infrastructure bounded context - track capacity management with SimPy."""

    def __init__(self, scenario: Scenario) -> None:
        # Convert scenario data to topology format
        topology_data = {
            'tracks': [self._track_to_dict(t) for t in (scenario.tracks or [])],
            'routes': [self._route_to_dict(r) for r in (scenario.routes or [])],
            'workshops': [self._workshop_to_dict(w) for w in (scenario.workshops or [])],
        }
        self.topology_service = TopologyService(topology_data)
        self.scenario = scenario
        self.infra = None
        # SimPy track resources for capacity management
        self.track_resources: dict[str, Any] = {}

    def get_topology_service(self) -> TopologyService:
        """Get topology service for other contexts."""
        return self.topology_service

    def initialize(self, infrastructure: Any, scenario: Any) -> None:  # pylint: disable=unused-argument
        """Initialize with infrastructure and create SimPy track resources.

        Notes
        -----
            Currently scenario is here necessary due to the call in the
            context registry
        """
        self.infra = infrastructure

        # Create SimPy resources for track capacity management
        for track in self.scenario.tracks:
            # Store track length with fill factor applied (in meters)
            fill_factor = track.fillfactor
            track_length = getattr(track, 'length', 200.0)
            # Store effective capacity in meters
            effective_capacity_m = track_length * fill_factor

            # For SimPy resource, use wagon count approximation
            # Todo: This is an assumption and needs to be improved!
            avg_wagon_length = 20.0
            wagon_capacity = max(1, int(effective_capacity_m / avg_wagon_length))

            self.track_resources[track.id] = infrastructure.engine.create_resource(wagon_capacity)

    def start_processes(self) -> None:
        """No processes needed - this provides infrastructure services."""

    def request_track_capacity(self, track_id: str) -> Any:
        """Request capacity on a track (returns SimPy resource request)."""
        if track_id in self.track_resources:
            print('REQUEST', track_id, self.get_track_capacity(track_id))
            return self.track_resources[track_id].request()
        return None

    def get_track_capacity(self, track_id: str) -> float:
        """Get total capacity of a track in meters (with fill factor applied)."""
        if self.scenario.tracks:
            for track in self.scenario.tracks:
                if track.id == track_id:
                    fill_factor = track.fillfactor
                    track_length = getattr(track, 'length', 200.0)
                    return track_length * fill_factor
        return 0.0

    def get_total_capacity(self, track_id: str) -> float:
        """Alias for get_track_capacity for compatibility with RailwayCapacityPort."""
        return self.get_track_capacity(track_id)

    def get_available_capacity(self, track_id: str) -> float:
        """Get available capacity on a track in meters."""
        if track_id in self.track_resources:
            resource = self.track_resources[track_id]
            available_wagons = resource.capacity - resource.count
            # Convert wagon count to meters
            avg_wagon_length = 20.0
            return available_wagons * avg_wagon_length
        return 0.0

    def get_metrics(self) -> dict[str, Any]:
        """Get railway infrastructure metrics."""
        # Get current capacity of all tracks
        capacity = {}
        for track in self.track_resources:
            capacity[track] = self.get_track_capacity(track) - self.get_available_capacity(track)
        return {
            'tracks_count': len(self.track_resources),
            'routes_count': len(self.scenario.routes or []),
            'workshops_count': len(self.scenario.workshops or []),
            'track occupancy': capacity,
        }

    def get_status(self) -> dict[str, Any]:
        """Get status."""
        return {'status': 'ready'}

    def cleanup(self) -> None:
        """Cleanup."""

    def on_simulation_started(self, event: Any) -> None:
        """Handle simulation started."""

    def on_simulation_ended(self, event: Any) -> None:
        """Handle simulation ended."""

    def on_simulation_failed(self, event: Any) -> None:
        """Handle simulation failed."""

    def _track_to_dict(self, track: Any) -> dict[str, Any]:
        """Convert track DTO to dict."""
        return {
            'id': track.id,
            'type': track.type.value if hasattr(track.type, 'value') else str(track.type),
            'capacity': getattr(track, 'capacity', 0),
            'length': getattr(track, 'length', 0),
        }

    def _route_to_dict(self, route: Any) -> dict[str, Any]:
        """Convert route DTO to dict."""
        return {
            'from': route.from_track,
            'to': route.to_track,
            'duration': route.duration,
        }

    def _workshop_to_dict(self, workshop: Any) -> dict[str, Any]:
        """Convert workshop DTO to dict."""
        return {
            'id': workshop.id,
            'track': workshop.track,
            'stations': workshop.retrofit_stations,
        }
