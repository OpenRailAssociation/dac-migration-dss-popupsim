"""Minimal scenario builder for validation tests."""

from datetime import UTC
from datetime import datetime

from contexts.configuration.application.dtos.locomotive_input_dto import LocomotiveInputDTO
from contexts.configuration.application.dtos.route_input_dto import RouteInputDTO
from contexts.configuration.application.dtos.topology_input_dto import TopologyInputDTO
from contexts.configuration.application.dtos.track_input_dto import TrackInputDTO
from contexts.configuration.application.dtos.wagon_input_dto import WagonInputDTO
from contexts.configuration.application.dtos.workshop_input_dto import WorkshopInputDTO
from contexts.configuration.domain.models.process_times import ProcessTimes
from contexts.configuration.domain.models.scenario import Scenario


def create_minimal_scenario(
    num_wagons: int = 1,
    num_stations: int = 1,
    retrofit_time: float = 10.0,
    num_workshops: int = 1,
) -> Scenario:
    """Create minimal scenario for validation tests."""
    workshops = [
        WorkshopInputDTO(
            id=f'WS{i + 1}',
            track=f'WS{i + 1}',
            retrofit_stations=num_stations,
        )
        for i in range(num_workshops)
    ]

    # Create topology with edges
    edges = {
        'parking': {'nodes': [1, 2], 'length': 300.0},
        'collection': {'nodes': [1, 2], 'length': 300.0},
        'retrofit': {'nodes': [1, 2], 'length': 300.0},
        'retrofitted': {'nodes': [1, 2], 'length': 200.0},
    }
    for i in range(num_workshops):
        edges[f'WS{i + 1}'] = {'nodes': [1, 2], 'length': 100.0}

    topology = TopologyInputDTO(nodes=[1, 2], edges=edges)

    # Create tracks with type field and length
    tracks = [
        TrackInputDTO(id='parking', edges=['parking'], type='parking', length=300.0),
        TrackInputDTO(id='collection', edges=['collection'], type='collection', length=300.0),
        TrackInputDTO(id='retrofit', edges=['retrofit'], type='retrofit', length=300.0),
        TrackInputDTO(id='retrofitted', edges=['retrofitted'], type='retrofitted', length=200.0),
    ]
    for i in range(num_workshops):
        tracks.append(TrackInputDTO(id=f'WS{i + 1}', edges=[f'WS{i + 1}'], type='workshop', length=100.0))

    # Create routes with path arrays and durations
    routes = [
        RouteInputDTO(id='parking_collection', path=['parking', 'collection'], duration=1.0),
        RouteInputDTO(id='collection_retrofit', path=['collection', 'retrofit'], duration=1.0),
        RouteInputDTO(id='retrofit_parking', path=['retrofit', 'parking'], duration=1.0),
        RouteInputDTO(id='parking_retrofit', path=['parking', 'retrofit'], duration=1.0),
        RouteInputDTO(id='parking_retrofitted', path=['parking', 'retrofitted'], duration=1.0),
        RouteInputDTO(id='retrofitted_parking', path=['retrofitted', 'parking'], duration=1.0),
    ]

    for i in range(num_workshops):
        ws_id = f'WS{i + 1}'
        routes.extend(
            [
                RouteInputDTO(id=f'retrofit_{ws_id}', path=['retrofit', ws_id], duration=1.0),
                RouteInputDTO(id=f'{ws_id}_parking', path=[ws_id, 'parking'], duration=1.0),
                RouteInputDTO(id=f'{ws_id}_retrofitted', path=[ws_id, 'retrofitted'], duration=1.0),
                RouteInputDTO(id=f'parking_{ws_id}', path=['parking', ws_id], duration=1.0),
            ]
        )

    locomotives = [LocomotiveInputDTO(id='L1', track='parking')]
    process_times = ProcessTimes(
        wagon_retrofit_time=retrofit_time,
        train_to_hump_delay=0.0,
        wagon_hump_interval=0.0,
        screw_coupling_time=0.0,
        screw_decoupling_time=0.0,
        dac_coupling_time=0.0,
        dac_decoupling_time=0.0,
        wagon_move_to_next_station=0.0,
        wagon_coupling_time=0.0,
        wagon_decoupling_time=0.0,
        wagon_coupling_retrofitted_time=0.0,
        loco_parking_delay=0.0,
    )

    # Create train with wagons
    from contexts.configuration.application.dtos.train_input_dto import TrainInputDTO

    wagons = [WagonInputDTO(id=f'W{i + 1:02d}', length=15.0) for i in range(num_wagons)]
    trains = [
        TrainInputDTO(
            train_id='T1',
            arrival_time=datetime(2024, 1, 1, tzinfo=UTC),
            arrival_track='collection',
            wagons=wagons,
        )
    ]

    return Scenario(
        id='validation_test',
        start_date=datetime(2024, 1, 1, tzinfo=UTC),
        end_date=datetime(2024, 1, 2, tzinfo=UTC),
        locomotives=locomotives,
        process_times=process_times,
        routes=routes,
        workshops=workshops,
        trains=trains,
        tracks=tracks,
        topology=topology,
    )
