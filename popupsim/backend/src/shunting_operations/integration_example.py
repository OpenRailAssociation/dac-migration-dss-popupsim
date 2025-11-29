"""Example showing how to integrate ShuntingOperationsContext with WorkshopOrchestrator.

This demonstrates the gradual migration approach - existing code continues to work
while we can optionally use the new shunting context.
"""

from workshop_operations.application.orchestrator import WorkshopOrchestrator
from workshop_operations.infrastructure.simulation.simpy_adapter import SimulationAdapter

from configuration.domain.models.scenario import Scenario


def create_orchestrator_with_shunting_context(sim: SimulationAdapter, scenario: Scenario) -> WorkshopOrchestrator:
    """Create WorkshopOrchestrator with enhanced shunting context.

    The orchestrator now always uses the enhanced shunting locomotive service
    for all yard operations (coupling, decoupling, moving wagons).

    Parameters
    ----------
    sim : SimulationAdapter
        Simulation adapter
    scenario : Scenario
        Scenario configuration

    Returns
    -------
    WorkshopOrchestrator
        Orchestrator with enhanced shunting locomotive service
    """
    print('🔧 Using enhanced ShuntingLocomotiveService for all yard operations')
    return WorkshopOrchestrator(sim, scenario)


# Example usage:
# Enhanced shunting locomotive service (capacity validation, better logging)
# orchestrator = create_orchestrator_with_shunting_context(sim, scenario)
# All yard operations now use enhanced shunting locomotives!
# orchestrator.run()
