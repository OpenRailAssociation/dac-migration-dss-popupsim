"""Topology Input DTO for configuration validation."""

from pydantic import BaseModel


class TopologyInputDTO(BaseModel):
    """DTO for topology input validation."""

    nodes: list[int]
    edges: dict[str, dict[str, float | list[int]]]
