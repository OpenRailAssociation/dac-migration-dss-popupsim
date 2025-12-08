"""Yard Operations Port - public interface."""

from typing import Any
from typing import Protocol


class YardOperationsPort(Protocol):
    """Port for yard operations context."""

    def get_parking_capacity(self) -> int:
        """Get available parking capacity."""

    def receive_train(self, train: Any) -> None:
        """Receive incoming train for classification."""
