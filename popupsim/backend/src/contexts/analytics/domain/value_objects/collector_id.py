"""Collector ID value object."""

from dataclasses import dataclass


@dataclass(frozen=True)
class CollectorId:
    """Unique identifier for metric collector."""

    value: str

    def __post_init__(self) -> None:
        if not self.value or not self.value.strip():
            msg = "Collector ID cannot be empty"
            raise ValueError(msg)
        if len(self.value) > 100:
            msg = "Collector ID too long (max 100 characters)"
            raise ValueError(msg)

    def __str__(self) -> str:
        return self.value
