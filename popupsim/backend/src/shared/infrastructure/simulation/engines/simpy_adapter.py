"""Enhanced SimPy adapter with monitoring and error handling."""

from collections.abc import Callable
from collections.abc import Generator
from dataclasses import dataclass
from datetime import timedelta
import inspect
import logging
from typing import Any
from typing import Self

from shared.infrastructure.time_converters import to_ticks
import simpy

from .simulation_engine_port import SimulationEnginePort

logger = logging.getLogger(__name__)


@dataclass
class SimulationStats:
    """Simulation engine statistics."""

    processes_scheduled: int = 0
    resources_created: int = 0
    stores_created: int = 0
    events_created: int = 0
    errors_count: int = 0


class SimPyEngineAdapter(SimulationEnginePort):
    """Enhanced SimPy adapter with monitoring, logging, and error handling."""

    def __init__(self, env: simpy.Environment) -> None:
        self._env = env
        self._stats = SimulationStats()
        self._resources: dict[str, Any] = {}
        self._stores: dict[str, Any] = {}
        self._error_handlers: list[Callable[[Exception], None]] = []
        self._pre_run_hooks: list[Callable[[], None]] = []
        self._post_run_hooks: list[Callable[[], None]] = []

    @classmethod
    def create(cls) -> Self:
        """Create Simpy Adapter."""
        logger.info('SIMPY: Creating enhanced SimPy engine adapter')
        return cls(simpy.Environment())

    def current_time(self) -> float:
        """Get current simulation time."""
        return float(self._env.now)

    def delay(self, duration: float | timedelta) -> Generator[Any]:
        """Delay with timedelta support and validation."""
        ticks = to_ticks(duration) if isinstance(duration, timedelta) else float(duration)

        if ticks < 0:
            msg = f'Delay duration must be non-negative: {ticks}'
            raise ValueError(msg)

        logger.debug('SIMPY: Delay %.1f ticks at t=%.1f', ticks, self._env.now)
        yield self._env.timeout(ticks)

    def schedule_process(self, process: Generator[Any] | Callable) -> Any:
        """Schedule process with flexible input and error handling."""
        self._stats.processes_scheduled += 1

        try:
            if inspect.isgenerator(process):
                logger.debug('SIMPY: Scheduling generator %s at t=%.1f', process, self._env.now)
                return self._env.process(process)

            if inspect.isgeneratorfunction(process):
                logger.debug(
                    'SIMPY: Scheduling generator function %s at t=%.1f',
                    process.__name__,
                    self._env.now,
                )
                return self._env.process(process())

            # Wrap non-generator callable
            logger.debug('SIMPY: Wrapping non-generator process at t=%.1f', self._env.now)

            def _wrap() -> Generator[Any]:
                try:
                    process()  # type: ignore[arg-type, operator]
                except (RuntimeError, ValueError, TypeError, AttributeError) as e:
                    self._handle_process_error(e)
                yield from ()

            return self._env.process(_wrap())

        except Exception as e:
            self._stats.errors_count += 1
            logger.exception('SIMPY: Process scheduling error')
            self._handle_process_error(e)
            raise

    def run(self, until: float | None = None) -> None:
        """Run simulation with hooks and error handling."""
        logger.info('SIMPY: Starting simulation run (until=%s)', until if until else 'inf')

        # Execute pre-run hooks
        for hook in self._pre_run_hooks:
            try:
                hook()
            except Exception:  # pylint: disable=broad-exception-caught
                logger.exception('Pre-run hook error')

        try:
            self._env.run(until=until)
            logger.info('SIMPY: Simulation completed at t=%.1f', self._env.now)
        except AttributeError as e:
            self._stats.errors_count += 1
            if 'callbacks' in str(e):
                logger.error("SIMPY: Invalid yield - generator yielded instead of 'yield from'")
            logger.exception('SIMPY: Simulation error')
            self._handle_process_error(e)
            raise
        except Exception as e:
            self._stats.errors_count += 1
            logger.exception('SIMPY: Simulation run error')
            self._handle_process_error(e)
            raise
        finally:
            # Execute post-run hooks
            for hook in self._post_run_hooks:
                try:
                    hook()
                except Exception:  # pylint: disable=broad-exception-caught
                    logger.exception('Post-run hook error')

    def create_resource(self, capacity: int, name: str | None = None) -> simpy.Resource:
        """Create named resource with monitoring."""
        self._stats.resources_created += 1
        resource = simpy.Resource(self._env, capacity=capacity)

        if name:
            self._resources[name] = resource
            logger.debug(
                "SIMPY: Created resource '%s' with capacity=%d at t=%.1f",
                name,
                capacity,
                self._env.now,
            )
        else:
            logger.debug(
                'SIMPY: Created resource with capacity=%d at t=%.1f',
                capacity,
                self._env.now,
            )

        return resource

    def create_store(self, capacity: int | None = None, name: str | None = None) -> Any:
        """Create named store with monitoring."""
        self._stats.stores_created += 1

        store = simpy.Store(self._env) if capacity is None else simpy.Store(self._env, capacity=capacity)

        if name:
            self._stores[name] = store
            logger.debug(
                "SIMPY: Created store '%s' with capacity=%s at t=%.1f",
                name,
                capacity,
                self._env.now,
            )
        else:
            logger.debug(
                'SIMPY: Created store with capacity=%s at t=%.1f',
                capacity,
                self._env.now,
            )

        return store

    def create_event(self) -> Any:
        """Create event for signaling."""
        self._stats.events_created += 1
        logger.debug('SIMPY: Created event at t=%.1f', self._env.now)
        return self._env.event()

    def get_resource_stats(self, resource: Any) -> dict[str, Any]:
        """Get resource utilization statistics."""
        if hasattr(resource, 'capacity') and hasattr(resource, 'count'):
            return {
                'capacity': resource.capacity,
                'in_use': resource.count,
                'available': resource.capacity - resource.count,
                'utilization': resource.count / resource.capacity if resource.capacity > 0 else 0.0,
            }
        return {}

    def get_store_stats(self, store: Any) -> dict[str, Any]:
        """Get store statistics."""
        if hasattr(store, 'capacity') and hasattr(store, 'items'):
            return {
                'capacity': store.capacity if store.capacity != float('inf') else None,
                'items_count': len(store.items),
                'available_space': store.capacity - len(store.items) if store.capacity != float('inf') else None,
            }
        return {}

    def get_simulation_stats(self) -> dict[str, Any]:
        """Get overall simulation statistics."""
        return {
            'current_time': self.current_time(),
            'processes_scheduled': self._stats.processes_scheduled,
            'resources_created': self._stats.resources_created,
            'stores_created': self._stats.stores_created,
            'events_created': self._stats.events_created,
            'errors_count': self._stats.errors_count,
            'named_resources': list(self._resources.keys()),
            'named_stores': list(self._stores.keys()),
        }

    def add_error_handler(self, handler: Callable[[Exception], None]) -> None:
        """Add global error handler."""
        self._error_handlers.append(handler)

    def add_pre_run_hook(self, hook: Callable[[], None]) -> None:
        """Add pre-run hook."""
        self._pre_run_hooks.append(hook)

    def add_post_run_hook(self, hook: Callable[[], None]) -> None:
        """Add post-run hook."""
        self._post_run_hooks.append(hook)

    def get_env(self) -> simpy.Environment:
        """Get the underlying SimPy environment.
        
        Returns
        -------
        simpy.Environment
            SimPy environment instance
        """
        return self._env

    def _handle_process_error(self, error: Exception) -> None:
        """Handle process errors."""
        for handler in self._error_handlers:
            try:
                handler(error)
            except Exception:  # pylint: disable=broad-exception-caught
                logger.exception('Error handler failed')
