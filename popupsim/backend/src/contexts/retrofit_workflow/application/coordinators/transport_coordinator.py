"""Transport Coordinator - orchestrates all transport operations."""

from collections.abc import Generator
from typing import Any

from contexts.retrofit_workflow.application.config.coordinator_config import TransportCoordinatorConfig
from contexts.retrofit_workflow.application.interfaces.transport_interfaces import TransportPort
from contexts.retrofit_workflow.domain.aggregates.rake_aggregate import Rake
from contexts.retrofit_workflow.domain.entities.locomotive import Locomotive


class TransportCoordinator:  # pylint: disable=too-few-public-methods
    """Coordinates all transport operations using SimPy.

     Coordinator for ALL transport:
    - Rake transport between tracks
    - Locomotive allocation/release
    - Coupling/decoupling
    - Track capacity management
    """

    def __init__(self, config: TransportCoordinatorConfig, transport_port: TransportPort):
        """Initialize coordinator.

        Args:
            config: Coordinator configuration
            transport_port: Transport operations interface
        """
        self.env = config.env
        self.transport_port = transport_port
        self.move_time = config.move_time
        self.coupling_time = config.coupling_time

    def transport_rake(self, rake: Rake, from_track: str, to_track: str) -> Generator[Any, Any]:
        """Transport rake between tracks.

        Args:
            rake: Rake to transport
            from_track: Source track
            to_track: Destination track
        """
        loco: Locomotive = yield from self.transport_port.allocate_locomotive()

        try:
            # Note: Rake stores wagon_ids, but transport_port expects Wagon objects
            # This is a design issue that needs to be resolved
            yield from self.transport_port.remove_from_track(from_track, rake.wagon_ids)  # type: ignore[arg-type]
            yield from self._move_locomotive(loco, from_track)
            yield from self._couple_rake(loco, rake)
            yield from self._move_locomotive(loco, to_track)
            yield from self._decouple_rake(loco, rake)
            yield from self.transport_port.add_to_track(to_track, rake.wagon_ids)  # type: ignore[arg-type]
            yield from self._move_locomotive(loco, loco.home_track)
        finally:
            yield from self.transport_port.release_locomotive(loco)

    def _move_locomotive(self, loco: Locomotive, to_track: str) -> Generator[Any, Any]:
        """Move locomotive between tracks.

        Parameters
        ----------
        loco : Locomotive
            Locomotive to move
        to_track : str
            Destination track

        Yields
        ------
        Generator[Any, Any]
            SimPy process for locomotive movement
        """
        loco.start_movement(to_track)
        yield self.env.timeout(self.move_time)
        loco.arrive_at(to_track)

    def _couple_rake(self, loco: Locomotive, rake: Rake) -> Generator[Any, Any]:
        """Couple locomotive to rake.

        Args:
            loco: Locomotive
            rake: Rake to couple
        """
        loco.start_coupling()
        coupling_duration = rake.wagon_count * self.coupling_time
        yield self.env.timeout(coupling_duration)
        loco.couple_rake(rake.id)
        loco.finish_operation()

    def _decouple_rake(self, loco: Locomotive, rake: Rake) -> Generator[Any, Any]:
        """Decouple locomotive from rake.

        Args:
            loco: Locomotive
            rake: Rake to decouple
        """
        loco.start_decoupling()
        decoupling_duration = rake.wagon_count * self.coupling_time
        yield self.env.timeout(decoupling_duration)
        loco.decouple_rake()
        loco.finish_operation()
