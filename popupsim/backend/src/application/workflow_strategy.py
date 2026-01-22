"""Workflow strategy pattern for legacy vs retrofit workflow."""

from typing import Any
from typing import Protocol

from contexts.popup_retrofit.application.popup_context import PopUpRetrofitContext
from contexts.retrofit_workflow.application.retrofit_workflow_context import RetrofitWorkshopContext
from contexts.shunting_operations.application.shunting_context import ShuntingOperationsContext
from contexts.yard_operations.application.yard_context import YardOperationsContext


class WorkflowStrategy(Protocol):
    """Protocol for workflow implementations."""

    contexts: dict[str, Any]

    def initialize(self, infra: Any, scenario: Any) -> None:  # pylint: disable=unused-argument
        """Initialize workflow."""

    def start_processes(self) -> None:
        """Start workflow processes."""

    def get_metrics(self) -> dict[str, Any]:
        """Get workflow metrics."""

    def cleanup(self) -> None:
        """Cleanup workflow resources."""


class LegacyWorkflowStrategy:
    """Legacy three-context workflow."""

    def __init__(self, infra: Any, event_bus: Any, rake_registry: Any):
        self.yard = YardOperationsContext(infra, rake_registry)
        self.popup = PopUpRetrofitContext(event_bus, rake_registry)
        self.shunting = ShuntingOperationsContext(event_bus, rake_registry)
        self.contexts = {'yard': self.yard, 'popup': self.popup, 'shunting': self.shunting}

    def initialize(self, infra: Any, scenario: Any) -> None:
        """Initialize all legacy contexts."""
        for ctx in self.contexts.values():
            ctx.initialize(infra, scenario)  # type: ignore[attr-defined]

    def start_processes(self) -> None:
        """Start all legacy context processes."""
        for ctx in self.contexts.values():
            ctx.start_processes()  # type: ignore[attr-defined]

    def get_metrics(self) -> dict[str, Any]:
        """Get metrics from all legacy contexts."""
        return {name: ctx.get_metrics() for name, ctx in self.contexts.items()}  # type: ignore[attr-defined]

    def cleanup(self) -> None:
        """Cleanup all legacy contexts."""
        for ctx in self.contexts.values():
            ctx.cleanup()  # type: ignore[attr-defined]


class RetrofitWorkflowStrategy:
    """New unified retrofit workflow."""

    def __init__(self, env: Any, scenario: Any, event_bus: Any):
        self.retrofit_workflow = RetrofitWorkshopContext(env, scenario)
        self.event_bus = event_bus
        self.contexts = {'retrofit_workflow': self.retrofit_workflow}

    def initialize(self, infra: Any, scenario: Any) -> None:  # noqa: ARG002  # pylint: disable=unused-argument
        """Initialize retrofit workflow context.

        Args:
            infra: Simulation infrastructure (unused, for protocol compatibility)
            scenario: Scenario configuration (unused, for protocol compatibility)
        """
        # Initialize the context (protocol-compliant)
        self.retrofit_workflow.initialize()  # type: ignore[call-arg]
        # Subscribe to train arrivals from External Trains Context
        self.retrofit_workflow.subscribe_to_train_arrivals(self.event_bus)

    def start_processes(self) -> None:
        """Start retrofit workflow processes."""
        self.retrofit_workflow.start_processes()

    def get_metrics(self) -> dict[str, Any]:
        """Get metrics from retrofit workflow."""
        return {'retrofit_workflow': self.retrofit_workflow.get_metrics()}

    def cleanup(self) -> None:
        """Cleanup retrofit workflow."""
        self.retrofit_workflow.cleanup()
