"""Base Coordinator - Common functionality for refactored coordinators."""

from abc import ABC
from abc import abstractmethod
from collections.abc import Generator
from typing import Any

from shared.infrastructure.simpy_time_converters import timedelta_to_sim_ticks
import simpy


class BaseCoordinator(ABC):
    """Base class for refactored coordinators.

    Provides common functionality for SimPy orchestration while ensuring
    all business logic is delegated to application services.
    """

    def __init__(self, env: simpy.Environment):
        """Initialize base coordinator."""
        self.env = env

    @abstractmethod
    def start(self) -> None:
        """Start coordinator processes."""

    def _execute_with_timing(self, operation_result: Any) -> Generator[Any, Any]:
        """Execute operation with proper SimPy timing.

        Parameters
        ----------
        operation_result : Any
            Result from application service containing timing information

        Yields
        ------
        Generator[Any, Any]
            SimPy timeout for operation duration
        """
        if operation_result and operation_result.operation:
            # Convert timedelta to simulation ticks if needed
            total_time = operation_result.operation.total_time
            if hasattr(total_time, 'total_seconds'):
                # Use centralized time converter
                timeout_duration = timedelta_to_sim_ticks(total_time)
            else:
                timeout_duration = float(total_time)

            yield self.env.timeout(timeout_duration)
        else:
            # No timing information, immediate completion
            yield self.env.timeout(0)

    def _handle_operation_failure(self, operation_result: Any, fallback_action: Any = None) -> None:
        """Handle operation failure with optional fallback.

        Parameters
        ----------
        operation_result : Any
            Failed operation result
        fallback_action : Any, optional
            Fallback action to execute on failure
        """
        if operation_result and operation_result.error_message:
            # Log error (simplified - could use proper logging)
            print(f'Operation failed: {operation_result.error_message}')

        if fallback_action:
            fallback_action()

    def _create_simpy_event(self) -> simpy.Event:
        """Create a SimPy event for coordination."""
        return self.env.event()

    def _timeout(self, duration: float) -> Generator[Any, Any]:
        """Create a SimPy timeout.

        Parameters
        ----------
        duration : float
            Timeout duration in simulation time units

        Yields
        ------
        Generator[Any, Any]
            SimPy timeout
        """
        yield self.env.timeout(duration)
