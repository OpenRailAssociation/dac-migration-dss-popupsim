"""Track capacity management for simulation."""

import random
from models.track import Track, TrackType
from models.topology import Topology
from models.scenario import TrackSelectionStrategy


class TrackCapacityManager:
    """Manages track capacity based on length and fill factor."""
    
    def __init__(self, tracks: list[Track], topology: Topology, fill_factor: float = 0.75, 
                 strategy: TrackSelectionStrategy = TrackSelectionStrategy.LEAST_OCCUPIED) -> None:
        self.managed_track_types = {TrackType.COLLECTION, TrackType.RETROFIT, TrackType.RETROFITTED, TrackType.PARKING}
        self.fill_factor = fill_factor
        self.strategy = strategy
        self.track_capacities: dict[str, float] = {}
        self.current_occupancy: dict[str, float] = {}
        self.collection_tracks: list[str] = []
        self.round_robin_index: int = 0
        
        self._calculate_capacities(tracks, topology)
        
    def _calculate_capacities(self, tracks: list[Track], topology: Topology) -> None:
        """Calculate capacity for managed tracks."""
        for track in tracks:
            if track.type in self.managed_track_types:
                total_length = sum(topology.get_edge_length(edge_id) for edge_id in track.edges)
                self.track_capacities[track.id] = total_length * self.fill_factor
                self.current_occupancy[track.id] = 0.0
                if track.type == TrackType.COLLECTION:
                    self.collection_tracks.append(track.id)
                
    def can_add_wagon(self, track_id: str, wagon_length: float) -> bool:
        """Check if wagon can be added to track."""
        if track_id not in self.track_capacities:
            return False
        return self.current_occupancy[track_id] + wagon_length <= self.track_capacities[track_id]
        
    def add_wagon(self, track_id: str, wagon_length: float) -> bool:
        """Add wagon to track if space available."""
        if self.can_add_wagon(track_id, wagon_length):
            self.current_occupancy[track_id] += wagon_length
            return True
        return False
        
    def remove_wagon(self, track_id: str, wagon_length: float) -> None:
        """Remove wagon from track."""
        if track_id in self.current_occupancy:
            self.current_occupancy[track_id] = max(0.0, self.current_occupancy[track_id] - wagon_length)
    
    def select_collection_track(self, wagon_length: float) -> str | None:
        """Select collection track based on configured strategy."""
        available_tracks = [
            track_id for track_id in self.collection_tracks
            if self.can_add_wagon(track_id, wagon_length)
        ]
        
        if not available_tracks:
            return None
        
        if self.strategy == TrackSelectionStrategy.ROUND_ROBIN:
            track = available_tracks[self.round_robin_index % len(available_tracks)]
            self.round_robin_index += 1
            return track
        
        elif self.strategy == TrackSelectionStrategy.LEAST_OCCUPIED:
            return min(
                available_tracks,
                key=lambda t: self.current_occupancy[t] / self.track_capacities[t]
            )
        
        elif self.strategy == TrackSelectionStrategy.FIRST_AVAILABLE:
            return available_tracks[0]
        
        elif self.strategy == TrackSelectionStrategy.RANDOM:
            return random.choice(available_tracks)
        
        return None