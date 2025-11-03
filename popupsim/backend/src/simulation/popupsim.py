"""Simulate popupsim scenarios.

This module keeps the simulation framework isolated from the domain logic.
It provides adapters to different simulation backends (e.g., SimPy).
It also provides builders for constructing simulation scenarios in a fluent manner.
It provides a small concurrency mode : a pool of workers executing tasks in parallel.
in a workshop which has multiple retrofit stations going on concurrently.

All waiting and scheduling is expressed via the adapter interface, so the domain logic
remains agnostic of the underlying simulation framework.
"""

from typing import Any

from .sim_adapter import SimulationAdapter


class PopupSim:  # pylint: disable=too-few-public-methods
    """High-level simulation orchestrator for PopUp-Sim.

    This facade coordinates simulation execution using a SimulationAdapter and a
    scenario object. Domain code should interact with this class rather than
    the simulation backend directly, keeping business logic backend-agnostic.
    """

    def __init__(self, adapter: SimulationAdapter, scenario: Any) -> None:
        """Initialize the PopupSim orchestrator.

        Parameters
        ----------
        adapter : SimulationAdapter
            SimulationAdapter instance used to drive the underlying
            simulation environment (e.g., SimPy).
        scenario : Any
            Domain scenario object containing routes, wagons and other
            configuration consumed by the simulation.
        """
        self.name: str = 'PopUpSim'
        self.adapter: SimulationAdapter = adapter
        self.scenario: Any = scenario

    def run(self, until: float | None = None) -> None:
        """Run the simulation until an optional time.

        The method delegates execution to the configured SimulationAdapter.

        Parameters
        ----------
        until : float or None, optional
            Simulation time indicating when to stop the simulation.
            If None, the adapter runs until its own completion.
        """
        print(f'Starting {self.name} for: {self.scenario}')
        self.adapter.run(until)
        print('Simulation completed.')
