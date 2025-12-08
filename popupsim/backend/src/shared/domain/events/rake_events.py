"""Domain events for rake operations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shared.domain.entities.rake import Rake


@dataclass(frozen=True)
class RakeFormedEvent:
    """Event raised when a rake is formed."""

    rake: Rake


@dataclass(frozen=True)
class RakeTransportedEvent:
    """Event raised when a rake is transported."""

    rake: Rake
    from_track: str
    to_track: str


@dataclass(frozen=True)
class RakeProcessingStartedEvent:
    """Event raised when rake processing starts."""

    rake: Rake


@dataclass(frozen=True)
class RakeProcessingCompletedEvent:
    """Event raised when rake processing is completed."""

    rake: Rake
    processing_time: float


@dataclass(frozen=True)
class RakeTransportRequestedEvent:
    """Event raised when rake transport is requested."""

    rake_id: str
    from_track: str
    to_track: str
    rake_type: str
