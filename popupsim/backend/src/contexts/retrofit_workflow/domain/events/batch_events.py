"""Domain events for batch operations."""

from dataclasses import dataclass


@dataclass(frozen=True)
class DomainEvent:
    """Base class for domain events."""

    timestamp: float
    event_id: str


@dataclass(frozen=True)
class BatchFormed(DomainEvent):
    """Event published when batch is formed."""

    batch_id: str
    wagon_ids: list[str]
    destination: str
    total_length: float


@dataclass(frozen=True)
class BatchTransportStarted(DomainEvent):
    """Event published when batch transport starts."""

    batch_id: str
    locomotive_id: str
    destination: str
    wagon_count: int


@dataclass(frozen=True)
class BatchArrivedAtDestination(DomainEvent):
    """Event published when batch arrives at destination."""

    batch_id: str
    destination: str
    wagon_count: int


@dataclass(frozen=True)
class WorkshopRetrofitCompleted(DomainEvent):
    """Event published when workshop retrofit is completed."""

    workshop_id: str
    batch_id: str
    completion_time: float
    processed_wagon_count: int


@dataclass(frozen=True)
class BatchProcessingCompleted(DomainEvent):
    """Event published when batch processing is completed."""

    batch_id: str
    workshop_id: str
    wagon_count: int
    processing_duration: float | None = None
