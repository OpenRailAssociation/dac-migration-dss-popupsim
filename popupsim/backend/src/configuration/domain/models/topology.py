"""Minimal topology model for edge lengths."""

import json
from pathlib import Path


class Topology:
    """Loads edge lengths from topology.json."""

    def __init__(self, topology_file: str | Path | dict | None = None) -> None:
        self.edge_lengths: dict[str, float] = {}
        if topology_file:
            if isinstance(topology_file, dict):
                self._load_from_dict(topology_file)
            else:
                self.load_topology(topology_file)

    def _load_from_dict(self, data: dict) -> None:
        """Load edge lengths from dict."""
        if 'edges' in data:
            for edge in data['edges']:
                edge_id = edge.get('edge_id') or edge.get('id')
                if edge_id and 'length' in edge:
                    length = float(edge['length'])
                    if length <= 0:
                        raise ValueError(f"Edge '{edge_id}' has invalid length {length}. Length must be > 0.")
                    self.edge_lengths[edge_id] = length

    def load_topology(self, file_path: str | Path) -> None:
        """Load edge lengths from topology JSON file."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f'Topology file not found: {path}')

        with path.open('r', encoding='utf-8') as f:
            data = json.load(f)

        if 'edges' in data:
            for edge_id, edge_data in data['edges'].items():
                if 'length' in edge_data:
                    length = float(edge_data['length'])
                    if length <= 0:
                        raise ValueError(f"Edge '{edge_id}' has invalid length {length}. Length must be > 0.")
                    self.edge_lengths[edge_id] = length

    def get_edge_length(self, edge_id: str) -> float:
        """Get length of an edge."""
        if edge_id not in self.edge_lengths:
            raise KeyError(f'Edge not found: {edge_id}')
        return self.edge_lengths[edge_id]
