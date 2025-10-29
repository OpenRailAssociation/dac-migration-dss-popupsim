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
    """Abstract adapter for simulation environments.

    Provides a framework-agnostic interface for simulation operations.
    Concrete implementations wrap specific simulation frameworks like SimPy.
    """

    @abstractmethod
    def current_time(self) -> float:
        """Get current simulation time.

        Returns
        -------
        float
            Current time in the simulation.
        """
        raise NotImplementedError

    # NOTE: `schedule_process` removed. Use `run_process` which is the
    # preferred, simulator-agnostic API to schedule domain callables.

    @abstractmethod
    def delay(self, duration: float) -> Any:
        """Create a delay/timeout event.

        Parameters
        ----------
        duration : float
            Duration of the delay in simulation time units.

        Returns
        -------
        Any
            Simulator-specific event or timeout object.
        """
        raise NotImplementedError

    @abstractmethod
    def run(self, until: float | None = None) -> Any:
        """Run the simulation.

        Parameters
        ----------
        until : float | None, optional
            Simulation time to run until. If None, runs until no more events.

        Returns
        -------
        Any
            Simulator-specific result or None.
        """
        raise NotImplementedError

    @abstractmethod
    def run_process(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Schedule and run a domain callable in the simulation context.

        Parameters
        ----------
        fn : Callable[..., Any]
            Callable to execute (generator function, regular function, or generator object).
        *args : Any
            Positional arguments to pass to the callable.
        **kwargs : Any
            Keyword arguments to pass to the callable.

        Returns
        -------
        Any
            Simulator-specific process or event object.
        """
        raise NotImplementedError


class SimPyAdapter(SimulationAdapter):
    """Adapter for SimPy simulation framework.

    Parameters
    ----------
    env : Any
        SimPy environment instance.
    """

    def __init__(self, env: Any) -> None:
        self._env: Any = env
        self.run_until: float = 500.0  # default run time

    @classmethod
    def create_simpy_adapter(cls: type['SimPyAdapter']) -> 'SimPyAdapter':
        """Create a SimPy adapter with a new environment.

        Import is performed lazily to avoid a hard dependency on the simpy package.
        Mypy will complain when simpy isn't installed; suppress that for now because
        simpy is an optional runtime dependency.

        Returns
        -------
        SimPyAdapter
            New adapter instance with a fresh SimPy environment.
        """
        import simpy  # type: ignore[import-not-found]  # pylint: disable=import-error,import-outside-toplevel

        env = simpy.Environment()
        return cls(env)

    def current_time(self) -> float:
        """Get current simulation time.

        Returns
        -------
        float
            Current time in the SimPy environment.
        """
        return float(self._env.now)

    def delay(self, duration: float) -> Any:
        """Create a SimPy timeout event.

        Parameters
        ----------
        duration : float
            Duration of the timeout in simulation time units.

        Returns
        -------
        Any
            SimPy timeout event.
        """
        return self._env.timeout(duration)

    def run(self, until: float | None = None) -> Any:
        """Run the SimPy simulation.

        Parameters
        ----------
        until : float | None, optional
            Simulation time to run until. If None, runs until no more events.

        Returns
        -------
        Any
            Result from SimPy environment run.
        """
        return self._env.run(until)

    def run_process(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Schedule a callable in the SimPy environment.

        Accepts three types of callables:
        - Generator function (yields): schedules the generator returned by calling it
        - Regular callable: wraps it in a generator for SimPy execution
        - Pre-built generator object: schedules it directly

        This avoids executing the callable outside the simulation environment.

        Parameters
        ----------
        fn : Callable[..., Any]
            Callable to execute (generator function, regular function, or generator object).
        *args : Any
            Positional arguments to pass to the callable.
        **kwargs : Any
            Keyword arguments to pass to the callable.

        Returns
        -------
        Any
            SimPy process object.
        """
        import inspect  # type: ignore[import-not-found]  # pylint: disable=import-error,import-outside-toplevel

        # If a pre-built generator object was passed as `fn`, schedule it directly
        if inspect.isgenerator(fn):
            return self._env.process(fn)

        # If fn is a generator-function, call it inside the sim context and schedule its generator
        if inspect.isgeneratorfunction(fn):
            return self._env.process(fn(*args, **kwargs))

        # Otherwise fn is a normal callable; wrap it in a tiny generator so SimPy can schedule it
        def _wrap() -> Generator[None]:
            fn(*args, **kwargs)
            yield from ()

        return self._env.process(_wrap())
