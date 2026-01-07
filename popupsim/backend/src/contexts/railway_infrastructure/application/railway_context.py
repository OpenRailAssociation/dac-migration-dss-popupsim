"""Railway Infrastructure Context - application layer."""

from typing import Any
from uuid import uuid4

from contexts.configuration.domain.models.scenario import Scenario
from contexts.railway_infrastructure.domain.aggregates.railway_yard import RailwayYard
from contexts.railway_infrastructure.domain.entities.track import Track
from contexts.railway_infrastructure.domain.entities.track import TrackType
from contexts.railway_infrastructure.domain.exceptions import InsufficientCapacityError
from contexts.railway_infrastructure.domain.exceptions import TrackNotFoundError
from contexts.railway_infrastructure.domain.services.topology_service import TopologyService
from contexts.railway_infrastructure.domain.value_objects.track_selection_strategy import TrackSelectionStrategy


class RailwayInfrastructureContext:
    """Railway Infrastructure bounded context - track capacity management."""

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

        # Railway yard aggregate for capacity management
        self.railway_yard: RailwayYard | None = None
        self._initialize_railway_yard()

    def _initialize_railway_yard(self) -> None:
        """Initialize railway yard aggregate from scenario configuration."""
        if not self.scenario.tracks:
            return

        yard = RailwayYard('main_yard')

        # Group tracks by type for creating track groups
        tracks_by_type: dict[TrackType, list[str]] = {}

        for track_dto in self.scenario.tracks:
            # Convert DTO to domain entity
            track_type = self._map_track_type(track_dto.type)
            track = Track(
                id=uuid4(),
                name=track_dto.id,
                type=track_type,
                total_length=getattr(track_dto, 'length', 200.0),
                fill_factor=getattr(track_dto, 'fillfactor', 0.75),
                max_wagons=self._get_workshop_capacity(track_dto) if track_type == TrackType.WORKSHOP else None,
            )

            # Add track to yard
            yard.add_track(track)

            # Group track IDs by type for creating track groups
            if track_type not in tracks_by_type:
                tracks_by_type[track_type] = []
            tracks_by_type[track_type].append(track.name)

        # Create track groups within the yard
        for track_type, track_ids in tracks_by_type.items():
            if track_ids:  # Only create groups with tracks
                yard.create_track_group(track_type, track_ids)

        self.railway_yard = yard

    def _map_track_type(self, dto_type: Any) -> TrackType:
        """Map DTO track type to domain TrackType."""
        type_str = dto_type.value if hasattr(dto_type, 'value') else str(dto_type)

        mapping = {
            'collection': TrackType.COLLECTION,
            'retrofit': TrackType.RETROFIT,
            'retrofitted': TrackType.RETROFITTED,
            'parking': TrackType.PARKING,
            'parking_area': TrackType.PARKING,
            'workshop': TrackType.WORKSHOP,
            'workshop_area': TrackType.WORKSHOP,
            'loco_parking': TrackType.LOCOPARKING,
            'mainline': TrackType.MAINLINE,
        }

        return mapping.get(type_str.lower(), TrackType.COLLECTION)

    def _get_workshop_capacity(self, track_dto: Any) -> int | None:
        """Get workshop capacity from scenario workshops."""
        if not self.scenario.workshops:
            return None

        for workshop in self.scenario.workshops:
            if workshop.track == track_dto.id:
                return workshop.retrofit_stations
        return None

    def get_topology_service(self) -> TopologyService:
        """Get topology service for other contexts."""
        return self.topology_service

    def initialize(self, infrastructure: Any, scenario: Any) -> None:  # noqa: ARG002
        """Initialize with infrastructure."""
        self.infra = infrastructure

    def start_processes(self) -> None:
        """No processes needed - this provides infrastructure services."""

    # Capacity management methods using RailwayYard aggregate
    def can_track_accommodate(self, track_id: str, wagon_length: float) -> bool:
        """Check if specific track can accommodate wagon."""
        if not self.railway_yard:
            return False
        return self.railway_yard.can_track_accommodate(track_id, wagon_length)

    def select_track_from_group(self, group_type: str, wagon_length: float, strategy: str | None = None) -> str | None:
        """Select track from group that can accommodate wagon."""
        if not self.railway_yard:
            return None

        track_type = self._map_group_type_to_track_type(group_type)
        if not track_type:
            return None

        if strategy:
            strategy_enum = self._map_selection_strategy(strategy)
            self.railway_yard.set_selection_strategy(track_type, strategy_enum)

        return self.railway_yard.select_track_for_type(track_type, wagon_length)

    def add_wagon_to_track(self, track_id: str, wagon_length: float) -> bool:
        """Add wagon to specific track."""
        if not self.railway_yard:
            return False

        try:
            self.railway_yard.add_wagon_to_track(track_id, wagon_length)
            return True
        except (TrackNotFoundError, InsufficientCapacityError):
            return False

    def remove_wagon_from_track(self, track_id: str, wagon_length: float) -> bool:
        """Remove wagon from specific track."""
        if not self.railway_yard:
            return False

        try:
            self.railway_yard.remove_wagon_from_track(track_id, wagon_length)
            return True
        except TrackNotFoundError:
            return False

    def add_wagon_to_group(self, group_type: str, wagon_length: float) -> tuple[str | None, bool]:
        """Add wagon to group using selection strategy."""
        if not self.railway_yard:
            return (None, False)

        track_type = self._map_group_type_to_track_type(group_type)
        if not track_type:
            return (None, False)

        return self.railway_yard.add_wagon_to_group(track_type, wagon_length)

    def remove_wagon_from_group(self, group_type: str, wagon_length: float) -> bool:
        """Remove wagon from group (removes from most occupied track)."""
        if not self.railway_yard:
            return False

        track_type = self._map_group_type_to_track_type(group_type)
        if not track_type:
            return False

        return self.railway_yard.remove_wagon_from_group(track_type, wagon_length)

    def _map_group_type_to_track_type(self, group_type: str) -> TrackType | None:
        """Map string group type to TrackType enum."""
        mapping = {
            'collection': TrackType.COLLECTION,
            'retrofit': TrackType.RETROFIT,
            'retrofitted': TrackType.RETROFITTED,
            'parking': TrackType.PARKING,
            'workshop': TrackType.WORKSHOP,
            'loco_parking': TrackType.LOCOPARKING,
            'mainline': TrackType.MAINLINE,
        }
        return mapping.get(group_type.lower())

    def _map_selection_strategy(self, strategy: str) -> TrackSelectionStrategy:
        """Map string strategy to enum."""
        mapping = {
            'least_occupied': TrackSelectionStrategy.LEAST_OCCUPIED,
            'first_available': TrackSelectionStrategy.FIRST_AVAILABLE,
            'round_robin': TrackSelectionStrategy.ROUND_ROBIN,
            'random': TrackSelectionStrategy.RANDOM,
        }
        return mapping.get(strategy.lower(), TrackSelectionStrategy.LEAST_OCCUPIED)

    def get_track_capacity(self, track_id: str) -> float:
        """Get total capacity of a track in meters (with fill factor applied)."""
        if not self.railway_yard:
            return 0.0
        return self.railway_yard.get_track_capacity(track_id)

    def get_total_capacity(self, track_id: str) -> float:
        """Alias for get_track_capacity for compatibility with RailwayCapacityPort."""
        return self.get_track_capacity(track_id)

    def get_available_capacity(self, track_id: str) -> float:
        """Get available capacity on a track in meters."""
        if not self.railway_yard:
            return 0.0
        return self.railway_yard.get_available_capacity(track_id)

    def get_metrics(self) -> dict[str, Any]:
        """Get railway infrastructure metrics."""
        if not self.railway_yard:
            return {
                'track_groups_count': 0,
                'total_tracks_count': 0,
                'routes_count': len(self.scenario.routes or []) if self.scenario else 0,
                'workshops_count': len(self.scenario.workshops or []) if self.scenario else 0,
                'track_metrics': {},
            }

        yard_metrics = self.railway_yard.get_yard_metrics()

        return {
            'track_groups_count': len(yard_metrics.get('track_groups', {})),
            'total_tracks_count': yard_metrics.get('total_tracks', 0),
            'routes_count': len(self.scenario.routes or []) if self.scenario else 0,
            'workshops_count': len(self.scenario.workshops or []) if self.scenario else 0,
            'track_metrics': yard_metrics.get('track_groups', {}),
            'yard_utilization': yard_metrics.get('utilization_percent', 0.0),
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
