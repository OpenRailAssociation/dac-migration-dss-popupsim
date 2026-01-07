"""Domain exceptions for railway infrastructure context."""


class RailwayInfrastructureError(Exception):
    """Base exception for railway infrastructure domain."""


class TrackNotFoundError(RailwayInfrastructureError):
    """Track with given ID not found."""


class InsufficientCapacityError(RailwayInfrastructureError):
    """Track cannot accommodate the requested capacity."""


class InvalidTrackGroupError(RailwayInfrastructureError):
    """Invalid track group configuration."""
