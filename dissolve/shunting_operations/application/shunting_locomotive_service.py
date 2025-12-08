"""Shunting locomotive service implementing LocomotiveService interface."""

from collections.abc import Generator
from typing import Any

from analytics.domain.events import ResourceAllocatedEvent, ResourceReleasedEvent
from analytics.domain.value_objects.timestamp import Timestamp
from workshop_operations.application.services.locomotive_service import (
    LocomotiveService,
)
from workshop_operations.domain.entities.locomotive import Locomotive
from workshop_operations.domain.entities.wagon import CouplerType

from shunting_operations.application.shunting_service import (
    DefaultShuntingService,
    ShuntingService,
)
from shunting_operations.domain.entities.shunting_locomotive import ShuntingLocomotive


class ShuntingLocomotiveService(LocomotiveService):
    """Service for shunting locomotive operations within workshop yards.

    This service handles yard shunting operations (coupling, decoupling, moving wagons)
    as opposed to long-distance transport locomotives that move between yards.

    Parameters
    ----------
    shunting_service : ShuntingService, optional
        Underlying shunting service implementation. If None, uses DefaultShuntingService.
    """

    def __init__(self, shunting_service: ShuntingService | None = None) -> None:
        self.shunting_service = shunting_service or DefaultShuntingService()
        self._shunting_locomotives: dict[str, ShuntingLocomotive] = {}

    def allocate(self, popupsim: Any) -> Generator[Any, Any, Locomotive]:
        """Allocate shunting locomotive for yard operations.

        Parameters
        ----------
        popupsim : Any
            Workshop orchestrator instance containing simulation state

        Returns
        -------
        Locomotive
            Base locomotive instance for yard shunting operations

        Yields
        ------
        Any
            SimPy events during locomotive allocation
        """
        shunting_loco = yield from self.shunting_service.allocate_shunting_locomotive(
            popupsim
        )
        self._shunting_locomotives[shunting_loco.id] = shunting_loco

        # Fire resource allocated event
        event = ResourceAllocatedEvent.create(
            timestamp=Timestamp.from_simulation_time(popupsim.sim.current_time()),
            resource_id=shunting_loco.id,
            resource_type="locomotive",
            allocated_to="shunting_operations",
        )
        self._fire_event(popupsim, event)

        return shunting_loco.base_locomotive

    def release(self, popupsim: Any, loco: Locomotive) -> Generator[Any]:
        """Release shunting locomotive back to yard pool.

        Parameters
        ----------
        popupsim : Any
            Workshop orchestrator instance containing simulation state
        loco : Locomotive
            Locomotive to release back to the pool

        Yields
        ------
        Any
            SimPy events during locomotive release
        """
        shunting_loco = self._shunting_locomotives.get(loco.id)
        if shunting_loco:
            # Fire resource released event
            event = ResourceReleasedEvent.create(
                timestamp=Timestamp.from_simulation_time(popupsim.sim.current_time()),
                resource_id=shunting_loco.id,
                resource_type="locomotive",
                released_from="shunting_operations",
            )
            self._fire_event(popupsim, event)

            yield from self.shunting_service.release_shunting_locomotive(
                popupsim, shunting_loco
            )
            del self._shunting_locomotives[loco.id]

    def move(
        self, popupsim: Any, loco: Locomotive, from_track: str, to_track: str
    ) -> Generator[Any]:
        """Move shunting locomotive between yard tracks.

        Parameters
        ----------
        popupsim : Any
            Workshop orchestrator instance containing simulation state
        loco : Locomotive
            Locomotive to move between tracks
        from_track : str
            Source track identifier
        to_track : str
            Destination track identifier

        Yields
        ------
        Any
            SimPy events during locomotive movement
        """
        shunting_loco = self._shunting_locomotives.get(loco.id)
        if shunting_loco:
            yield from self.shunting_service.execute_shunting_move(
                popupsim, shunting_loco, from_track, to_track
            )

    def couple_wagons(
        self,
        popupsim: Any,
        loco: Locomotive,
        wagon_count: int,
        coupler_type: CouplerType,
    ) -> Generator[Any]:
        """Couple wagons using shunting locomotive with capacity validation.

        Parameters
        ----------
        popupsim : Any
            Workshop orchestrator instance containing simulation state
        loco : Locomotive
            Locomotive to couple wagons to
        wagon_count : int
            Number of wagons to couple
        coupler_type : CouplerType
            Type of coupler (SCREW, DAC, or HYBRID)

        Yields
        ------
        Any
            SimPy events during coupling operation
        """
        shunting_loco = self._shunting_locomotives.get(loco.id)
        if shunting_loco:
            yield from self.shunting_service.execute_coupling(
                popupsim, shunting_loco, wagon_count, coupler_type
            )

    def decouple_wagons(
        self,
        popupsim: Any,
        loco: Locomotive,
        wagon_count: int,
        coupler_type: CouplerType | None = None,
    ) -> Generator[Any]:
        """Decouple wagons from shunting locomotive with capacity tracking.

        Parameters
        ----------
        popupsim : Any
            Workshop orchestrator instance containing simulation state
        loco : Locomotive
            Locomotive to decouple wagons from
        wagon_count : int
            Number of wagons to decouple
        coupler_type : CouplerType, optional
            Type of coupler. If None, defaults to SCREW type

        Yields
        ------
        Any
            SimPy events during decoupling operation
        """
        shunting_loco = self._shunting_locomotives.get(loco.id)
        if shunting_loco:
            yield from self.shunting_service.execute_decoupling(
                popupsim, shunting_loco, wagon_count, coupler_type
            )

    def _fire_event(self, popupsim: Any, event: Any) -> None:
        """Fire event if metrics available."""
        if hasattr(popupsim, "metrics") and popupsim.metrics:
            popupsim.metrics.record_event(event)
