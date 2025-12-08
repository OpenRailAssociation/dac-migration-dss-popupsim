"""Rake type enumeration."""

from enum import Enum


class RakeType(Enum):
    """Types of rakes in railway operations."""

    WORKSHOP_RAKE = "workshop"  # For retrofit processing
    COLLECTION_RAKE = "collection"  # Assembled on collection tracks
    TRANSPORT_RAKE = "transport"  # For movement between tracks
    RETROFITTED_RAKE = "retrofitted"  # Reassembled after retrofit completion
    DEPARTURE_RAKE = "departure"  # Ready for outbound trains
    PARKING_RAKE = "parking"  # For parking operations
