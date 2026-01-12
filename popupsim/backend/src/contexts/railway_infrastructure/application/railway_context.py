"""Railway Infrastructure Context with dependency injection."""

from functools import cached_property
from typing import Any

from contexts.configuration.domain.models.scenario import Scenario
from contexts.railway_infrastructure.domain.aggregates.railway_yard import RailwayYard
from contexts.railway_infrastructure.domain.aggregates.track_group import TrackGroup
from contexts.railway_infrastructure.domain.entities.track import Track
from contexts.railway_infrastructure.domain.entities.track import TrackType
from contexts.railway_infrastructure.domain.ports import MetricsPort
from contexts.railway_infrastructure.domain.repositories.track_occupancy_repository import TrackOccupancyRepository
from contexts.railway_infrastructure.domain.services.topology_service import TopologyService
from contexts.railway_infrastructure.domain.services.track_group_service import TrackGroupService


class RailwayInfrastructureContext:
    """Railway Infrastructure Context.

    Manages railway infrastructure domain with dependency injection.

    Parameters
    ----------
    scenario : Scenario
        Configuration scenario containing tracks, routes, workshops
    metrics_port : MetricsPort
        Port implementation for metrics collection operations
    occupancy_repository : TrackOccupancyRepository, optional
        Repository for track occupancy state, creates new if None
    """

    def __init__(
        self,
        scenario: Scenario,
        metrics_port: MetricsPort,
        occupancy_repository: TrackOccupancyRepository | None = None,
    ) -> None:
        """Initialize with injected port implementations.

        Parameters
        ----------
        scenario : Scenario
            Configuration scenario containing tracks, routes, workshops
        metrics_port : MetricsPort
            Port implementation for metrics collection operations
        occupancy_repository : TrackOccupancyRepository, optional
            Repository for track occupancy state, creates new if None
        """
        self._scenario = scenario
        self._metrics_port = metrics_port
        self._occupancy_repository = occupancy_repository or TrackOccupancyRepository()

    @cached_property
    def _topology_service(self) -> TopologyService:
        """Get topology service (cached)."""
        return TopologyService(self._build_topology_data())

    @cached_property
    def _track_group_service(self) -> TrackGroupService:
        """Get track group service (cached)."""
        return TrackGroupService(self._occupancy_repository)

    @cached_property
    def _tracks(self) -> dict[str, Track]:
        """Get tracks dictionary (cached)."""
        return self._build_tracks()

    @cached_property
    def _track_groups(self) -> dict[str, TrackGroup]:
        """Get track groups dictionary (cached)."""
        return self._build_track_groups()

    @cached_property
    def _railway_yard(self) -> RailwayYard:
        """Get railway yard aggregate (cached)."""
        return self._build_railway_yard()

    def get_topology_service(self) -> TopologyService:
        """Get topology service.

        Returns
        -------
        TopologyService
            Service for topology operations
        """
        return self._topology_service

    def get_track_group_service(self) -> TrackGroupService:
        """Get track group service.

        Returns
        -------
        TrackGroupService
            Service for track group operations
        """
        return self._track_group_service

    def get_railway_yard(self) -> RailwayYard:
        """Get railway yard aggregate.

        Returns
        -------
        RailwayYard
            Railway yard aggregate managing all tracks
        """
        return self._railway_yard

    def get_track_groups(self) -> dict[str, TrackGroup]:
        """Get all track groups.

        Returns
        -------
        dict[str, TrackGroup]
            Copy of track groups dictionary
        """
        return self._track_groups.copy()

    def get_occupancy_repository(self) -> TrackOccupancyRepository:
        """Get track occupancy repository.

        Returns
        -------
        TrackOccupancyRepository
            Repository for track occupancy management
        """
        return self._occupancy_repository

    def get_metrics(self) -> dict[str, Any]:
        """Get metrics through injected port.

        Returns
        -------
        dict[str, Any]
            Combined metrics from tracks, occupancy, and groups
        """
        track_metrics = self._metrics_port.collect_track_metrics(self._tracks)
        occupancy_metrics = self._metrics_port.collect_occupancy_metrics(self._occupancy_repository)

        return {
            **track_metrics,
            **occupancy_metrics,
            'track_groups_count': len(self._track_groups),
        }

    def cleanup(self) -> None:
        """Cleanup context resources."""

    def initialize(self, infrastructure: Any, scenario: Scenario) -> None:
        """Initialize context."""

    def start_processes(self) -> None:
        """Start context processes."""

    def get_status(self) -> dict[str, Any]:
        """Get context status."""
        return {
            'tracks_count': len(self._tracks),
            'track_groups_count': len(self._track_groups),
        }

    def get_track_capacity(self, track_id: str) -> float:
        """Get track capacity in meters."""
        if track_id not in self._tracks:
            return 0.0
        track = self._tracks[track_id]
        return track.total_length * track.fill_factor

    def get_track(self, track_id: str) -> Track | None:
        """Get track by ID.

        Parameters
        ----------
        track_id : str
            Track identifier

        Returns
        -------
        Track | None
            Track if found, None otherwise
        """
        return self._tracks.get(track_id)

    def get_total_capacity(self, track_id: str) -> float:
        """Get total capacity in meters."""
        if track_id not in self._tracks:
            return 0.0
        track = self._tracks[track_id]
        return track.total_length * track.fill_factor

    def get_available_capacity(self, track_id: str) -> float:
        """Get available capacity in meters."""
        if track_id not in self._tracks:
            return 0.0
        track = self._tracks[track_id]
        total_capacity = track.total_length * track.fill_factor
        try:
            occupancy = self._occupancy_repository.get(track_id)
            if occupancy:
                occupied_meters = occupancy.get_current_occupancy_meters()
                return max(0.0, total_capacity - occupied_meters)
        except (ValueError, TypeError):
            pass
        return total_capacity

    def on_simulation_started(self, event: Any) -> None:
        """Handle simulation started event."""

    def on_simulation_failed(self, event: Any) -> None:
        """Handle simulation failed event."""

    def on_simulation_ended(self, event: Any) -> None:
        """Handle simulation ended event."""

    def on_simulation_completed(self, event: Any) -> None:
        """Handle simulation completed event."""

    def _build_topology_data(self) -> dict[str, Any]:
        """Build topology data from scenario.

        Returns
        -------
        dict[str, Any]
            Topology data dictionary
        """
        return {
            'tracks': [self._track_to_dict(t) for t in (self._scenario.tracks or [])],
            'routes': [self._route_to_dict(r) for r in (self._scenario.routes or [])],
            'workshops': [self._workshop_to_dict(w) for w in (self._scenario.workshops or [])],
        }

    def _map_track_type(self, track_type_str: str) -> TrackType:
        """Map scenario track type strings to TrackType enum.

        Parameters
        ----------
        track_type_str : str
            Track type string from scenario

        Returns
        -------
        TrackType
            Mapped track type enum value
        """
        type_mapping = {
            'parking': TrackType.PARKING,
            'parking_area': TrackType.PARKING,
            'rescource_parking': TrackType.LOCOPARKING,
            'loco_parking': TrackType.LOCOPARKING,
            'collection': TrackType.COLLECTION,
            'mainline': TrackType.MAINLINE,
            'retrofit': TrackType.RETROFIT,
            'workshop': TrackType.WORKSHOP,
            'workshop_area': TrackType.WORKSHOP,
        }
        return type_mapping.get(track_type_str.lower(), TrackType.COLLECTION)

    def _build_tracks(self) -> dict[str, Track]:
        """Build tracks from scenario.

        Returns
        -------
        dict[str, Track]
            Dictionary of tracks by name
        """
        tracks = {}
        for track_config in self._scenario.tracks or []:
            track_type = track_config.type
            if track_type is not None and hasattr(track_type, 'value'):
                type_str = track_type.value
            elif track_type is not None:
                type_str = str(track_type)
            else:
                type_str = 'collection'

            track_id = track_config.id

            track = Track(
                id=track_id,
                name=track_config.id,  # Use ID as name
                type=self._map_track_type(type_str),
                total_length=track_config.length,
                fill_factor=track_config.fillfactor,
                max_wagons=getattr(track_config, 'max_wagons', None),
            )
            tracks[track.name] = track
        return tracks

    def _build_track_groups(self) -> dict[str, TrackGroup]:
        """Build track groups from tracks.

        Returns
        -------
        dict[str, TrackGroup]
            Dictionary of track groups by type
        """
        groups = {}
        for track in self._tracks.values():
            group_id = f'{track.type.value}_group'
            if group_id not in groups:
                groups[group_id] = TrackGroup(group_id, track.type)
            groups[group_id].add_track(track)
        return groups

    def _build_railway_yard(self) -> RailwayYard:
        """Build railway yard from tracks.

        Returns
        -------
        RailwayYard
            Railway yard aggregate containing all tracks
        """
        yard = RailwayYard('main_yard', 'Main Railway Yard')
        for track in self._tracks.values():
            yard.add_track(track)
        return yard

    def _track_to_dict(self, track: Any) -> dict[str, Any]:
        """Convert track to dictionary.

        Parameters
        ----------
        track : Any
            Track configuration object

        Returns
        -------
        dict[str, Any]
            Track dictionary
        """
        track_type = track.type
        if track_type is not None and hasattr(track_type, 'value'):
            type_value = track_type.value
        else:
            type_value = str(track_type or 'unknown')

        return {
            'id': track.id,
            'type': type_value,
            'length': track.length,
        }

    def _route_to_dict(self, route: Any) -> dict[str, Any]:
        """Convert route to dictionary.

        Parameters
        ----------
        route : Any
            Route configuration object

        Returns
        -------
        dict[str, Any]
            Route dictionary
        """
        return {
            'from': route.from_track,
            'to': route.to_track,
            'duration': route.duration,
        }

    def _workshop_to_dict(self, workshop: Any) -> dict[str, Any]:
        """Convert workshop to dictionary.

        Parameters
        ----------
        workshop : Any
            Workshop configuration object

        Returns
        -------
        dict[str, Any]
            Workshop dictionary
        """
        return {
            'id': workshop.id,
            'track': workshop.track,
            'stations': workshop.retrofit_stations,
        }
