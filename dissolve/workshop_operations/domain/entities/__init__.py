"""Workshop operations entities."""

from .locomotive import Locomotive
from .track import Track, TrackType

# Train moved to aggregates
from .wagon import Wagon
from .workshop import Workshop

__all__ = [
    "Locomotive",
    "Track",
    "TrackType",
    # "Train", # moved to aggregates
    "Wagon",
    "Workshop",
]
