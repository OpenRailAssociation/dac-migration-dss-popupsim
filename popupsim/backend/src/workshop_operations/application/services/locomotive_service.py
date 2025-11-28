"""Service interfaces and implementations for simulation operations."""

from abc import ABC
from abc import abstractmethod
from collections.abc import Generator
import logging
from typing import Any
from typing import cast

from analytics.domain.events.locomotive_events import LocomotiveStatusChangeEvent
from analytics.domain.value_objects.timestamp import Timestamp
from workshop_operations.domain.entities.locomotive import Locomotive
from workshop_operations.domain.entities.locomotive import LocoStatus
from workshop_operations.domain.entities.wagon import CouplerType
from workshop_operations.infrastructure.routing.route_finder import find_route

logger = logging.getLogger(__name__)


class LocomotiveService(ABC):
    """Service for locomotive operations."""

    @abstractmethod
    def allocate(self, popupsim: Any) -> Generator[Any, Any, Locomotive]:
        """Allocate locomotive from pool.

        Parameters
        ----------
        popupsim : Any
            The WorkshopOrchestrator instance containing simulation state.

        Returns
        -------
        Generator[Any, Any, Locomotive]
            Generator yielding the allocated locomotive.
        """

    @abstractmethod
    def release(self, popupsim: Any, loco: Locomotive) -> Generator[Any]:
        """Release locomotive to pool.

        Parameters
        ----------
        popupsim : Any
            The WorkshopOrchestrator instance containing simulation state.
        loco : Locomotive
            The locomotive to release.

        Returns
        -------
        Generator[Any]
            Generator yielding SimPy events for the release operation.
        """

    @abstractmethod
    def move(self, popupsim: Any, loco: Locomotive, from_track: str, to_track: str) -> Generator[Any]:
        """Move locomotive between tracks.

        Parameters
        ----------
        popupsim : Any
            The WorkshopOrchestrator instance containing simulation state.
        loco : Locomotive
            The locomotive to move.
        from_track : str
            Source track ID.
        to_track : str
            Destination track ID.

        Returns
        -------
        Generator[Any]
            Generator yielding SimPy events for the movement operation.
        """

    @abstractmethod
    def couple_wagons(
        self, popupsim: Any, loco: Locomotive, wagon_count: int, coupler_type: CouplerType
    ) -> Generator[Any]:
        """Couple wagons to locomotive.

        Parameters
        ----------
        popupsim : Any
            The WorkshopOrchestrator instance containing simulation state.
        loco : Locomotive
            The locomotive to couple wagons to.
        wagon_count : int
            Number of wagons to couple.
        coupler_type : CouplerType
            Type of coupler on the wagons.

        Returns
        -------
        Generator[Any]
            Generator yielding SimPy events for the coupling operation.
        """

    @abstractmethod
    def decouple_wagons(
        self, popupsim: Any, loco: Locomotive, wagon_count: int, coupler_type: CouplerType | None = None
    ) -> Generator[Any]:
        """Decouple wagons from locomotive.

        Parameters
        ----------
        popupsim : Any
            The WorkshopOrchestrator instance containing simulation state.
        loco : Locomotive
            The locomotive to decouple wagons from.
        wagon_count : int
            Number of wagons to decouple.

        Returns
        -------
        Generator[Any]
            Generator yielding SimPy events for the decoupling operation.
        """


class DefaultLocomotiveService(LocomotiveService):
    """Default implementation of locomotive service."""

    def allocate(self, popupsim: Any) -> Generator[Any, Any, Locomotive]:
        """Allocate locomotive from pool with tracking.

        Parameters
        ----------
        popupsim : Any
            The WorkshopOrchestrator instance containing simulation state.

        Returns
        -------
        Generator[Any, Any, Locomotive]
            Generator yielding the allocated locomotive.
        """
        loco = cast(Locomotive, (yield popupsim.locomotives.get()))
        popupsim.locomotives.track_allocation(loco.id)
        return loco

    def release(self, popupsim: Any, loco: Locomotive) -> Generator[Any]:
        """Release locomotive to pool with tracking.

        Parameters
        ----------
        popupsim : Any
            The WorkshopOrchestrator instance containing simulation state.
        loco : Locomotive
            The locomotive to release.

        Yields
        ------
        Any
            SimPy events for putting locomotive back in pool.
        """
        # Set locomotive to parking status when released
        current_time = popupsim.sim.current_time()
        loco.record_status_change(current_time, LocoStatus.PARKING)
        # Emit locomotive event for metrics collection
        event = LocomotiveStatusChangeEvent.create(
            timestamp=Timestamp.from_simulation_time(current_time),
            locomotive_id=loco.id,
            status=LocoStatus.PARKING.value,
        )
        popupsim.metrics.record_event(event)

        popupsim.locomotives.track_release(loco.id)
        yield popupsim.locomotives.put(loco)

    def move(self, popupsim: Any, loco: Locomotive, from_track: str, to_track: str) -> Generator[Any]:
        """Move locomotive from one track to another via route."""
        start_time = popupsim.sim.current_time()
        loco.record_status_change(start_time, LocoStatus.MOVING)
        # Emit locomotive event for metrics collection
        event = LocomotiveStatusChangeEvent.create(
            timestamp=Timestamp.from_simulation_time(start_time), locomotive_id=loco.id, status=LocoStatus.MOVING.value
        )
        popupsim.metrics.record_event(event)

        route = find_route(popupsim.scenario.routes, from_track, to_track)
        duration = route.duration if route and route.duration else 0.0
        logger.info('🚂 Loco %s starts moving [%s → %s] at t=%.1f', loco.id, from_track, to_track, start_time)

        if duration > 0:
            yield popupsim.sim.delay(duration)
            arrival_time = popupsim.sim.current_time()
            logger.info(
                '✓ Loco %s arrived at %s at t=%.1f (travel time: %.1f min)',
                loco.id,
                to_track,
                arrival_time,
                duration,
            )
        else:
            logger.info('✓ Loco %s at %s (no travel needed)', loco.id, to_track)

        # Set locomotive back to parking status after movement completes
        arrival_time = popupsim.sim.current_time()
        loco.record_status_change(arrival_time, LocoStatus.PARKING)

        # Emit parking event for metrics collection
        parking_event = LocomotiveStatusChangeEvent.create(
            timestamp=Timestamp.from_simulation_time(arrival_time),
            locomotive_id=loco.id,
            status=LocoStatus.PARKING.value,
        )
        popupsim.metrics.record_event(parking_event)

        loco.track = to_track

    def couple_wagons(
        self, popupsim: Any, loco: Locomotive, wagon_count: int, coupler_type: CouplerType
    ) -> Generator[Any]:
        """Couple wagons to locomotive.

        For N wagons, there are N coupling operations:
        - loco ↔ wagon1, wagon1 ↔ wagon2, ..., wagon(N-1) ↔ wagonN
        """
        process_times = popupsim.scenario.process_times
        time_per_coupling = process_times.get_coupling_time(coupler_type.value)
        coupling_time = wagon_count * time_per_coupling

        # Only change state if coupling takes time
        if coupling_time > 0:
            current_time = popupsim.sim.current_time()
            loco.record_status_change(current_time, LocoStatus.COUPLING)
            # Emit locomotive event for metrics collection
            event = LocomotiveStatusChangeEvent.create(
                timestamp=Timestamp.from_simulation_time(current_time),
                locomotive_id=loco.id,
                status=LocoStatus.COUPLING.value,
            )
            popupsim.metrics.record_event(event)

            yield popupsim.sim.delay(coupling_time)

    def decouple_wagons(
        self, popupsim: Any, loco: Locomotive, wagon_count: int, coupler_type: CouplerType | None = None
    ) -> Generator[Any]:
        """Decouple wagons from locomotive.

        For N wagons, there are N decoupling operations:
        - loco ↔ wagon1, wagon1 ↔ wagon2, ..., wagon(N-1) ↔ wagonN
        """
        process_times = popupsim.scenario.process_times
        if coupler_type:
            time_per_coupling = process_times.get_decoupling_time(coupler_type.value)
        else:
            time_per_coupling = process_times.screw_decoupling_time  # Default to screw
        decoupling_time = wagon_count * time_per_coupling

        # Only change state if decoupling takes time
        if decoupling_time > 0:
            current_time = popupsim.sim.current_time()
            loco.record_status_change(current_time, LocoStatus.DECOUPLING)
            # Emit locomotive event for metrics collection
            event = LocomotiveStatusChangeEvent.create(
                timestamp=Timestamp.from_simulation_time(current_time),
                locomotive_id=loco.id,
                status=LocoStatus.DECOUPLING.value,
            )
            popupsim.metrics.record_event(event)

            yield popupsim.sim.delay(decoupling_time)
