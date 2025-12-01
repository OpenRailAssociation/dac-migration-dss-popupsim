"""Adapters for simulation backends.

This module defines a SimulationAdapter abstract base class and a SimPy-specific
implementation. The adapter API keeps domain simulation code independent of the
underlying simulation framework (e.g., SimPy). Use SimPyAdapter.create_simpy_adapter()
to obtain an adapter when SimPy is available; the import is performed lazily to
avoid a hard dependency.
"""

from abc import ABC
from abc import abstractmethod
from collections.abc import Callable
from collections.abc import Generator
from typing import Any


class SimulationAdapter(ABC):  # pylint: disable=duplicate-code
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

    @abstractmethod
    def create_resource(self, capacity: int) -> Any:
        """Create a resource with limited capacity.

        Parameters
        ----------
        capacity : int
            Maximum number of concurrent users.

        Returns
        -------
        Any
            Simulator-specific resource object.
        """
        raise NotImplementedError

    @abstractmethod
    def create_store(self, capacity: int | None = None) -> Any:
        """Create a store with optional capacity limit.

        Parameters
        ----------
        capacity : int | None, optional
            Maximum capacity of the store. If None, unlimited capacity.

        Returns
        -------
        Any
            Simulator-specific store object.
        """
        raise NotImplementedError

    @abstractmethod
    def create_event(self) -> Any:
        """Create an event for signaling.

        Returns
        -------
        Any
            Simulator-specific event object.
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

    @classmethod
    def create_simpy_resource(cls, environment: Any, capacity: int) -> Any:
        """Create SimPy Resource with specified capacity."""
        import simpy  # type: ignore[import-not-found]  # pylint: disable=import-error,import-outside-toplevel

        return simpy.Resource(environment, capacity)

    def create_store(self, capacity: int | None = None) -> Any:
        """Create a SimPy Store for resource pooling.

        Parameters
        ----------
        capacity : int | None, optional
            Maximum capacity of the store. If None, unlimited capacity.

        Returns
        -------
        Any
            SimPy Store instance.
        """
        import simpy  # type: ignore[import-not-found]  # pylint: disable=import-error,import-outside-toplevel

        if capacity is None:
            return simpy.Store(self._env)  # Unlimited capacity
        return simpy.Store(self._env, capacity=capacity)

    def current_time(self) -> float:
        """Get current simulation time as float (minutes since start).

        Returns
        -------
        float
            Current time in the SimPy environment in minutes.
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
        if until is None:
            until = self.run_until

        try:
            return self._env.run(until)
        except TypeError as e:
            # Handle Pydantic ValidationError constructor issue with SimPy
            if 'ValidationError.__new__() missing' in str(e):
                # This is likely a Pydantic ValidationError that SimPy can't recreate properly
                # Convert it to a more generic RuntimeError that SimPy can handle
                raise RuntimeError(
                    'Simulation failed due to validation error. '
                    'This is likely caused by invalid data in the simulation model. '
                    f'Original error: {e}'
                ) from e
            # Re-raise other TypeErrors
            raise

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
        import inspect  # pylint: disable=import-outside-toplevel

        # If a pre-built generator object was passed as `fn`, schedule it directly
        if inspect.isgenerator(fn):
            return self._env.process(fn)

        # If fn is a generator-function, call it inside the sim context and schedule its generator
        if inspect.isgeneratorfunction(fn):
            return self._env.process(fn(*args, **kwargs))

        # Otherwise fn is a normal callable; wrap it in a tiny generator so SimPy can schedule it
        def _wrap() -> Generator[Any]:
            fn(*args, **kwargs)
            yield from ()

        return self._env.process(_wrap())

    def create_resource(self, capacity: int) -> Any:
        """Create a SimPy Resource with limited capacity.

        Parameters
        ----------
        capacity : int
            Maximum number of concurrent users.

        Returns
        -------
        Any
            SimPy Resource object.
        """
        import simpy  # type: ignore[import-not-found]  # pylint: disable=import-error,import-outside-toplevel

        return simpy.Resource(self._env, capacity=capacity)

    def create_event(self) -> Any:
        """Create a SimPy Event for signaling.

        Returns
        -------
        Any
            SimPy Event wrapper with wait() and trigger() methods.
        """
        import simpy  # type: ignore[import-not-found]  # pylint: disable=import-error,import-outside-toplevel

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

        return EventWrapper(self._env)
