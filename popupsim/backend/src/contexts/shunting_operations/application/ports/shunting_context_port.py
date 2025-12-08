"""Shunting Operations Context port definition."""

from abc import ABC, abstractmethod

from contexts.shunting_operations.domain.entities.shunting_locomotive import (
    ShuntingLocomotive,
)


class ShuntingContextPort(ABC):
    """Port for Shunting Operations Context."""

    @abstractmethod
    def allocate_locomotive(self, requester: str) -> ShuntingLocomotive | None:
        """Allocate an available locomotive."""

    @abstractmethod
    def release_locomotive(self, locomotive_id: str) -> bool:
        """Release an allocated locomotive."""

    @abstractmethod
    def get_locomotive_count(self) -> int:
        """Get total number of locomotives."""

    @abstractmethod
    def get_available_count(self) -> int:
        """Get number of available locomotives."""

    @abstractmethod
    def get_utilization(self) -> float:
        """Get locomotive utilization percentage."""
