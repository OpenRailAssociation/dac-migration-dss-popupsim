"""Adapters for simulation backends.

This module defines a SimulationAdapter abstract base class and a SimPy-specific
implementation. The adapter API keeps domain simulation code independent of the
underlying simulation framework (e.g., SimPy). Use SimPyAdapter.create_simpy_adapter()
to obtain an adapter when SimPy is available; the import is performed lazily to
avoid a hard dependency.
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Generator, Optional


class SimulationAdapter(ABC):
    """Abstract adapter for simulation environments"""

    @abstractmethod
    def current_time(self) -> float:
        """Get current simulation time"""
        raise NotImplementedError

    # NOTE: `schedule_process` removed. Use `run_process` which is the
    # preferred, simulator-agnostic API to schedule domain callables.

    @abstractmethod
    def delay(self, duration: float) -> Any:
        """Create a delay/timeout. Return value is simulator-specific (event/timeout)."""
        raise NotImplementedError

    @abstractmethod
    def run(self, until: Optional[float] = None) -> Any:
        """Run the simulation"""
        raise NotImplementedError

    @abstractmethod
    def run_process(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Run/schedule a domain callable without leaking generator semantics"""
        raise NotImplementedError


class SimPyAdapter(SimulationAdapter):
    """Adapter for SimPy framework"""

    def __init__(self, env: Any) -> None:
        self._env: Any = env

    @classmethod
    def create_simpy_adapter(cls: type['SimPyAdapter']) -> 'SimPyAdapter':
        """Factory method to create a SimPy adapter with a new environment.

        Import is performed lazily to avoid a hard dependency on the simpy package.
        Mypy will complain when simpy isn't installed; suppress that for now because
        simpy is an optional runtime dependency.
        """
        import simpy  # type: ignore[import-not-found]  # pylint: disable=import-error,import-outside-toplevel

        env = simpy.Environment()
        return cls(env)

    def current_time(self) -> float:
        return float(self._env.now)

    def delay(self, duration: float) -> Any:
        return self._env.timeout(duration)

    def run(self, until: Optional[float] = None) -> Any:
        return self._env.run(until)

    def run_process(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Accept either:
        - a generator-function (callable that yields) -> schedule the generator returned by calling it
        - a normal callable -> wrap it in a tiny generator so it's executed in the SimPy context
        - a pre-built generator object -> schedule it directly
        This avoids executing the callable outside the simulation environment (no double execution).
        """
        import inspect  # type: ignore[import-not-found]  # pylint: disable=import-error,import-outside-toplevel

        # If a pre-built generator object was passed as `fn`, schedule it directly
        if inspect.isgenerator(fn):
            return self._env.process(fn)

        # If fn is a generator-function, call it inside the sim context and schedule its generator
        if inspect.isgeneratorfunction(fn):
            return self._env.process(fn(*args, **kwargs))

        # Otherwise fn is a normal callable; wrap it in a tiny generator so SimPy can schedule it
        def _wrap() -> Generator[None, None, None]:
            fn(*args, **kwargs)
            yield from ()

        return self._env.process(_wrap())
