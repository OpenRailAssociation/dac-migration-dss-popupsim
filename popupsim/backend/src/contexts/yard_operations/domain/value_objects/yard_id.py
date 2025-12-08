"""Yard identifier value object."""

from dataclasses import dataclass


@dataclass(frozen=True)
class YardId:
    """Yard identifier value object."""

    id: str

    def __str__(self) -> str:
        return self.id
