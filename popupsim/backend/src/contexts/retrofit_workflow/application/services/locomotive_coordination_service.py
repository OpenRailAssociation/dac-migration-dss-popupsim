"""Locomotive coordination service for managing locomotive availability."""

from collections.abc import Generator
from typing import Any


class LocomotiveCoordinationService:  # pylint: disable=too-few-public-methods
    """Application service for locomotive coordination and availability management.

    Note: Single-purpose service with focused responsibility.
    """

    def __init__(self, config: Any):
        """Initialize locomotive coordination service."""
        self.config = config

    def wait_for_idle_locomotive(self) -> Generator[Any, Any]:
        """Wait until locomotive pool has idle locomotives.

        Yields
        ------
            SimPy events until locomotive becomes available
        """
        while not self._has_idle_locomotive():
            yield self.config.env.event()

    def _has_idle_locomotive(self) -> bool:
        """Check if locomotive pool has idle locomotives.

        Returns
        -------
            True if idle locomotives are available
        """
        return len(self.config.locomotive_manager.pool.items) > 0
