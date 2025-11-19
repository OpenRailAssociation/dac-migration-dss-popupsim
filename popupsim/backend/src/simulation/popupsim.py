"""Simulate popupsim scenarios.

This module keeps the simulation framework isolated from the domain logic.
It provides adapters to different simulation backends (e.g., SimPy).
It also provides builders for constructing simulation scenarios in a fluent manner.
It provides a small concurrency mode : a pool of workers executing tasks in parallel.
in a workshop which has multiple retrofit stations going on concurrently.

All waiting and scheduling is expressed via the adapter interface, so the domain logic
remains agnostic of the underlying simulation framework.
"""

import logging

from models.scenario import Scenario

from .sim_adapter import SimulationAdapter

logger = logging.getLogger('PopupSim')


class PopupSim:  # pylint: disable=too-few-public-methods
    """High-level simulation orchestrator for PopUp-Sim.

    This facade coordinates simulation execution using a SimulationAdapter and a
    scenario object. Domain code should interact with this class rather than
    the simulation backend directly, keeping business logic backend-agnostic.
    """

    def __init__(self, adapter: SimulationAdapter, scenario: Scenario) -> None:
        """Initialize the PopupSim orchestrator.

        Parameters
        ----------
        adapter : SimulationAdapter
            SimulationAdapter instance used to drive the underlying
            simulation environment (e.g., SimPy).
        scenario : Scenario
            Domain scenario object containing routes, wagons and other
            models consumed by the simulation.
        """
        self.name: str = 'PopUpSim'
        self.adapter: SimulationAdapter = adapter
        self.scenario: Scenario = scenario

    def get_simtime_limit_from_scenario(self) -> float:
        """Determine simulation time limit from scenario configuration.

        Returns
        -------
        float
            Simulation time limit derived from scenario parameters.
        """
        start_datetime = self.scenario.start_date
        end_datetime = self.scenario.end_date
        delta = end_datetime - start_datetime
        return delta.total_seconds() / 60.0  # Convert to minutes

    def run(self, until: float | None = None) -> None:
        """Run the simulation until an optional time.

        The method delegates execution to the configured SimulationAdapter.

        Parameters
        ----------
        until : float or None, optional
            Simulation time indicating when to stop the simulation.
            If None, the adapter runs until its own completion.
        """
        if not until:
            until = self.get_simtime_limit_from_scenario()
        runinfo = f'Starting {self.name} for: {self.scenario}'
        logger.info(runinfo)
        self.adapter.run(until)
        logger.info('Simulation completed.')
