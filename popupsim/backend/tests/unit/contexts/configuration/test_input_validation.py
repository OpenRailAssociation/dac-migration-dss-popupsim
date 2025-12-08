"""Test input validation for zero-length edges and wagons."""

import pytest
from pydantic import ValidationError


from contexts.configuration.application.dtos.wagon_input_dto import WagonInputDTO

from contexts.configuration.domain.models.topology import Topology


def test_wagon_zero_length_rejected() -> None:
    """Test that wagon with zero length is rejected."""
    with pytest.raises(ValidationError, match="greater than 0"):
        WagonInputDTO(id="W1", length=0.0, is_loaded=False, needs_retrofit=True)


def test_wagon_negative_length_rejected() -> None:
    """Test that wagon with negative length is rejected."""
    with pytest.raises(ValidationError, match="greater than 0"):
        WagonInputDTO(id="W1", length=-5.0, is_loaded=False, needs_retrofit=True)


def test_wagon_positive_length_accepted() -> None:
    """Test that wagon with positive length is accepted."""
    wagon = WagonInputDTO(id="W1", length=15.5, is_loaded=False, needs_retrofit=True)
    assert wagon.length == 15.5


def test_topology_zero_edge_length_rejected_from_dict() -> None:
    """Test that topology with zero edge length is rejected when loading from dict."""
    topology_data = {"edges": [{"edge_id": "E1", "length": 0.0}]}

    with pytest.raises(ValueError, match="Edge 'E1' has invalid length 0.0"):
        Topology(topology_data)


def test_topology_negative_edge_length_rejected_from_dict() -> None:
    """Test that topology with negative edge length is rejected when loading from dict."""
    topology_data = {"edges": [{"edge_id": "E1", "length": -10.0}]}

    with pytest.raises(ValueError, match="Edge 'E1' has invalid length -10.0"):
        Topology(topology_data)


def test_topology_positive_edge_length_accepted_from_dict() -> None:
    """Test that topology with positive edge length is accepted when loading from dict."""
    topology_data = {"edges": [{"edge_id": "E1", "length": 100.0}]}
    topology = Topology(topology_data)

    assert topology.get_edge_length("E1") == 100.0


def test_topology_multiple_edges_one_invalid() -> None:
    """Test that topology rejects data if any edge has invalid length."""
    topology_data = {
        "edges": [
            {"edge_id": "E1", "length": 100.0},
            {"edge_id": "E2", "length": 0.0},  # Invalid
            {"edge_id": "E3", "length": 50.0},
        ]
    }

    with pytest.raises(ValueError, match="Edge 'E2' has invalid length 0.0"):
        Topology(topology_data)
