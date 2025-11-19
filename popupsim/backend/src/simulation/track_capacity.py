"""Track capacity management for simulation."""

from models.track import Track, TrackType
from models.topology import Topology


class TrackCapacityManager:
    """Manages track capacity based on length and fill factor."""
    
    def __init__(self, tracks: list[Track], topology: Topology, fill_factor: float = 0.75) -> None:
        self.managed_track_types = {TrackType.COLLECTION, TrackType.RETROFIT, TrackType.RETROFITTED, TrackType.PARKING}
        self.fill_factor = fill_factor
        self.track_capacities: dict[str, float] = {}
        self.current_occupancy: dict[str, float] = {}
        
        self._calculate_capacities(tracks, topology)
        
    def _calculate_capacities(self, tracks: list[Track], topology: Topology) -> None:
        """Calculate capacity for managed tracks."""
        for track in tracks:
            if track.type in self.managed_track_types:
                total_length = sum(topology.get_edge_length(edge_id) for edge_id in track.edges)
                self.track_capacities[track.id] = total_length * self.fill_factor
                self.current_occupancy[track.id] = 0.0
                
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