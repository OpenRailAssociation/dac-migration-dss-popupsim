"""Retrofit workflow strategy."""

from typing import Any

from contexts.retrofit_workflow.application.retrofit_workflow_context import RetrofitWorkshopContext


class RetrofitWorkflowStrategy:
    """Unified retrofit workflow."""

    def __init__(self, env: Any, scenario: Any, event_bus: Any):
        self.retrofit_workflow = RetrofitWorkshopContext(env, scenario)
        self.event_bus = event_bus
        self.contexts = {'retrofit_workflow': self.retrofit_workflow}

    def initialize(self, infra: Any, scenario: Any) -> None:  # noqa: ARG002
        """Initialize retrofit workflow context.

        Args:
            infra: Simulation infrastructure (unused, for protocol compatibility)
            scenario: Scenario configuration (unused, for protocol compatibility)
        """
        self.retrofit_workflow.initialize()  # type: ignore[call-arg]
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
