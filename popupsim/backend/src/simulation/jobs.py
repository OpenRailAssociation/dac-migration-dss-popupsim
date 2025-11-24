"""Job abstractions for simulation tasks."""

from collections.abc import Generator
from dataclasses import dataclass
import logging
from typing import Any

from models.locomotive import LocoStatus
from models.wagon import CouplerType
from models.wagon import Wagon
from models.wagon import WagonStatus

from .services import LocomotiveService

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


def execute_transport_job(popupsim: Any, job: TransportJob, loco_service: LocomotiveService) -> Generator[Any]:
    """Execute a transport job: allocate resource, move, couple, transport, decouple, release.

    Parameters
    ----------
    popupsim : PopupSim
        The PopupSim instance.
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
    resource = yield from loco_service.allocate(popupsim)

    # Travel to pickup location
    logger.info('🚂 ROUTE: %s traveling [%s → %s]', resource.locomotive_id, resource.track_id, job.from_track)
    yield from loco_service.move(popupsim, resource, resource.track_id, job.from_track)

    # Couple wagons (use first wagon's coupler type)
    coupler_type = job.wagons[0].coupler_type if job.wagons else CouplerType.SCREW
    logger.debug('%s coupling %d wagons', resource.locomotive_id, len(job.wagons))
    yield from loco_service.couple_wagons(popupsim, resource, len(job.wagons), coupler_type)

    # Update wagon states - remove from source track
    for wagon in job.wagons:
        popupsim.track_capacity.remove_wagon(job.from_track, wagon.length)
        wagon.status = WagonStatus.MOVING
        wagon.source_track_id = job.from_track
        wagon.destination_track_id = job.to_track
        wagon.track_id = None

    # Travel to destination
    logger.info(
        '🚂 ROUTE: %s traveling [%s → %s] with %d wagons',
        resource.locomotive_id,
        job.from_track,
        job.to_track,
        len(job.wagons),
    )
    yield from loco_service.move(popupsim, resource, job.from_track, job.to_track)

    # Decouple wagons
    logger.debug('%s decoupling %d wagons at %s', resource.locomotive_id, len(job.wagons), job.to_track)
    yield from loco_service.decouple_wagons(popupsim, resource, len(job.wagons))

    # Update wagon states - add to destination track
    for wagon in job.wagons:
        popupsim.track_capacity.add_wagon(job.to_track, wagon.length)
        wagon.track_id = job.to_track
        wagon.source_track_id = None
        wagon.destination_track_id = None
        # Status will be set by calling function

    # Return resource to parking
    parking_track_id = popupsim.parking_tracks[0].id
    logger.debug('%s returning to parking', resource.locomotive_id)
    yield from loco_service.move(popupsim, resource, resource.track_id, parking_track_id)
    resource.record_status_change(popupsim.sim.current_time(), LocoStatus.PARKING)
    yield from loco_service.release(popupsim, resource)
