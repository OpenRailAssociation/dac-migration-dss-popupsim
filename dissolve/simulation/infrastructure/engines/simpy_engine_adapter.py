"""SimPy implementation of simulation engine port."""

import inspect
import logging
from collections.abc import Callable, Generator
from datetime import timedelta
from typing import Any

import simpy  # type: ignore[import-not-found]

from shared.infrastructure.time_converters import to_ticks
from simulation.domain.ports.simulation_engine_port import SimulationEnginePort
from simulation.infrastructure.events.event_wrapper import EventWrapper

logger = logging.getLogger(__name__)


class SimPyEngineAdapter(SimulationEnginePort):
    """SimPy implementation of simulation engine port."""

    def __init__(self) -> None:
        self._env = simpy.Environment()

    @classmethod
    def create(cls) -> "SimPyEngineAdapter":
        """Create new SimPy engine adapter."""
        return cls()

    def current_time(self) -> float:
        """Get current simulation time in ticks."""
        return float(self._env.now)

    def current_timestamp(self) -> "Timestamp":
        """Get current time as Timestamp object."""
        from analytics.domain.value_objects.timestamp import Timestamp

        return Timestamp.from_ticks(self._env.now)

    def schedule_process(self, process: Callable[..., Generator[Any, Any, Any]]) -> Any:
        """Schedule a process for execution."""
        if inspect.isgenerator(process):
            logger.debug(
                "⚙️ SIMPY: Scheduling generator process at t=%.1f", self._env.now
            )
            return self._env.process(process)

        if inspect.isgeneratorfunction(process):
            logger.debug(
                "⚙️ SIMPY: Scheduling generator function at t=%.1f", self._env.now
            )
            return self._env.process(process())

        logger.debug("⚙️ SIMPY: Wrapping non-generator process at t=%.1f", self._env.now)

        def _wrap() -> Generator[Any, Any]:
            process()
            yield from ()

        return self._env.process(_wrap())

    def create_resource(self, capacity: int) -> Any:
        """Create resource with capacity."""
        logger.debug(
            "🔧 SIMPY: Creating resource with capacity=%d at t=%.1f",
            capacity,
            self._env.now,
        )
        return simpy.Resource(self._env, capacity=capacity)

    def create_store(self, capacity: int | None = None) -> Any:
        """Create store for items."""
        logger.debug(
            "📦 SIMPY: Creating store with capacity=%s at t=%.1f",
            capacity,
            self._env.now,
        )
        if capacity is None:
            return simpy.Store(self._env)
        return simpy.Store(self._env, capacity=capacity)

    def delay(self, duration: float | timedelta) -> Any:
        """Create delay event.

        Parameters
        ----------
        duration : float | timedelta
            Delay duration (float in simulation ticks or timedelta)
        """
        ticks = (
            to_ticks(duration) if isinstance(duration, timedelta) else float(duration)
        )

        if ticks < 0:
            raise ValueError(f"Delay duration must be non-negative: {ticks}")

        logger.debug("⏱️  SIMPY: Creating delay of %.1f ticks", ticks)
        return self._env.timeout(ticks)

    def run(self, until: float | None = None) -> None:
        """Run simulation until time or completion."""
        logger.info(
            "▶️ SIMPY: Starting simulation run (until=%.1f)",
            until if until else float("inf"),
        )
        self._env.run(until=until)
        logger.info("⏹️ SIMPY: Simulation completed at t=%.1f", self._env.now)

    def create_event(self) -> Any:
        """Create event for signaling."""
        return EventWrapper(self._env)
