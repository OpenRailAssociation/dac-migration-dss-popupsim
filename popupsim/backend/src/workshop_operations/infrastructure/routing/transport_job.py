"""Job abstractions for simulation tasks."""

from collections.abc import Generator
from dataclasses import dataclass
import logging
from typing import Any

from workshop_operations.application.services.locomotive_service import LocomotiveService
from workshop_operations.domain.entities.locomotive import LocoStatus
from workshop_operations.domain.entities.wagon import CouplerType
from workshop_operations.domain.entities.wagon import Wagon
from workshop_operations.domain.entities.wagon import WagonStatus

logger = logging.getLogger('Jobs')


@dataclass
class TransportJob:
    """Generic transport job for moving wagons between tracks.

    Attributes
    ----------
    wagons : list[Wagon]
        Wagons to transport.
    from_track : str
        Source track ID.
    to_track : str
        Destination track ID.
    resource_pool_name : str
        Name of resource pool to use ('locomotives', 'cranes', etc.).
    """

    wagons: list[Wagon]
    from_track: str
    to_track: str
    resource_pool_name: str = 'locomotives'


def execute_transport_job(popupsim: Any, job: TransportJob, loco_service: LocomotiveService) -> Generator[Any, Any]:
    """Execute a transport job: allocate resource, move, couple, transport, decouple, release.

    Parameters
    ----------
    popupsim : WorkshopOrchestrator
        The WorkshopOrchestrator instance.
    job : TransportJob
        The transport job to execute.
    loco_service : LocomotiveService
        Service for locomotive operations.

    Yields
    ------
    Any
        SimPy events.
    """
    # Allocate resource
    resource = yield from loco_service.allocate(popupsim)  # type: ignore[assignment,func-returns-value]

    # Travel to pickup location
    logger.info(
        '🚂 ROUTE: %s traveling [%s → %s]',
        resource.id,  # type: ignore[attr-defined]
        resource.track,  # type: ignore[attr-defined]
        job.from_track,
    )
    yield from loco_service.move(
        popupsim,
        resource,
        resource.track,
        job.from_track,  # type: ignore[arg-type,attr-defined]
    )

    # Couple wagons (use first wagon's coupler type)
    coupler_type = job.wagons[0].coupler_type if job.wagons else CouplerType.SCREW
    logger.debug('%s coupling %d wagons', resource.id, len(job.wagons))  # type: ignore[attr-defined]
    yield from loco_service.couple_wagons(
        popupsim,
        resource,
        len(job.wagons),
        coupler_type,  # type: ignore[arg-type]
    )

    # Update wagon states - remove from source track
    for wagon in job.wagons:
        popupsim.track_capacity.remove_wagon(job.from_track, wagon.length)
        wagon.status = WagonStatus.MOVING
        wagon.source_track_id = job.from_track
        wagon.destination_track_id = job.to_track
        wagon.track = None

    # Travel to destination
    logger.info(
        '🚂 ROUTE: %s traveling [%s → %s] with %d wagons',
        resource.id,  # type: ignore[attr-defined]
        job.from_track,
        job.to_track,
        len(job.wagons),
    )
    yield from loco_service.move(popupsim, resource, job.from_track, job.to_track)  # type: ignore[arg-type]

    # Decouple wagons
    logger.debug(
        '%s decoupling %d wagons at %s',
        resource.id,  # type: ignore[attr-defined]
        len(job.wagons),
        job.to_track,
    )
    yield from loco_service.decouple_wagons(popupsim, resource, len(job.wagons))  # type: ignore[arg-type]

    # Update wagon states - add to destination track
    for wagon in job.wagons:
        popupsim.track_capacity.add_wagon(job.to_track, wagon.length)
        wagon.track = job.to_track
        wagon.source_track_id = None
        wagon.destination_track_id = None
        # Status will be set by calling function

    # Return resource to parking
    parking_track_id = popupsim.parking_tracks[0].id
    logger.debug('%s returning to parking', resource.id)  # type: ignore[attr-defined]
    yield from loco_service.move(
        popupsim,
        resource,
        resource.track,
        parking_track_id,  # type: ignore[arg-type,attr-defined]
    )
    resource.record_status_change(popupsim.sim.current_time(), LocoStatus.PARKING)  # type: ignore[attr-defined]
    yield from loco_service.release(popupsim, resource)  # type: ignore[arg-type]
