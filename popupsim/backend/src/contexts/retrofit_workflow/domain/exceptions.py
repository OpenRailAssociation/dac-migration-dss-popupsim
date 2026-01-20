"""Exceptions for retrofit workflow context."""

from typing import Any


class SimulationDeadlockError(Exception):
    """Raised when simulation detects a deadlock condition.

    This occurs when resources cannot proceed due to capacity constraints
    that cannot be resolved (e.g., parking full, no available tracks).
    """

    def __init__(self, message: str, context: dict[str, Any] | None = None) -> None:
        """Initialize deadlock error.

        Args:
            message: Human-readable error description
            context: Additional context about the deadlock state
        """
        super().__init__(message)
        self.context = context or {}
