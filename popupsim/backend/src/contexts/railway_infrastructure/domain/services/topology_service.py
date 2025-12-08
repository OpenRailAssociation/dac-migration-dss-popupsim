"""Railway topology service - upstream conformist pattern."""

from typing import Any


class TopologyService:
    """Upstream topology service - other contexts copy data from this."""

    def __init__(self, topology_data: dict[str, Any]) -> None:
        self._topology = topology_data

    def get_topology(self) -> dict[str, Any]:
        """Get complete topology data."""
        return self._topology.copy()

    def find_path(self, from_node: str, to_node: str) -> list[str]:
        """Find path between two nodes."""
        # Simple implementation - contexts can copy and enhance
        routes = self._topology.get('routes', [])
        for route in routes:
            if route.get('from') == from_node and route.get('to') == to_node:
                return [from_node, to_node]
        return []

    def get_track_info(self, track_id: str) -> dict[str, Any] | None:
        """Get track information."""
        tracks = self._topology.get('tracks', [])
        for track in tracks:
            if track.get('id') == track_id:
                return dict(track).copy()
        return None
