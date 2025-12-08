"""Shared event wrapper for SimPy events."""

from typing import Any

import simpy  # type: ignore[import-not-found]


class EventWrapper:
    """Wrapper for SimPy events to provide consistent interface."""

    def __init__(self, env: Any) -> None:
        self._env = env
        self._event = simpy.Event(env)

    def wait(self) -> Any:
        """Wait for event to be triggered."""
        return self._event

    def succeed(self) -> None:
        """Trigger the event."""
        if not self._event.triggered:
            self._event.succeed()

    def trigger(self) -> None:
        """Trigger the event (alias for succeed)."""
        self.succeed()
