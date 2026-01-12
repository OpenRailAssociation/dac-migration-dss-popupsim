"""Dependency injection setup with hexagonal architecture."""

from contexts.configuration.domain.models.scenario import Scenario
from contexts.railway_infrastructure.application.railway_context import RailwayInfrastructureContext
from contexts.railway_infrastructure.domain.repositories.track_occupancy_repository import TrackOccupancyRepository
from contexts.railway_infrastructure.infrastructure.adapters import StandardMetricsAdapter


class RailwayContextFactory:
    """Factory for creating Railway Infrastructure Context."""

    @staticmethod
    def create_context(scenario: Scenario) -> RailwayInfrastructureContext:
        """Create context with injected port implementations.

        Parameters
        ----------
        scenario : Scenario
            Configuration scenario containing tracks, routes, workshops

        Returns
        -------
        RailwayInfrastructureContext
            Fully configured context with injected port implementations
        """
        # Create repository
        occupancy_repository = TrackOccupancyRepository()

        # Create adapters implementing the ports
        metrics_adapter = StandardMetricsAdapter()

        # Create context with port implementations
        return RailwayInfrastructureContext(
            scenario=scenario,
            metrics_port=metrics_adapter,
            occupancy_repository=occupancy_repository,
        )


def create_railway_context(scenario: Scenario) -> RailwayInfrastructureContext:
    """Create railway context.

    Parameters
    ----------
    scenario : Scenario
        Configuration scenario containing tracks, routes, workshops

    Returns
    -------
    RailwayInfrastructureContext
        Configured railway infrastructure context
    """
    return RailwayContextFactory.create_context(scenario)
