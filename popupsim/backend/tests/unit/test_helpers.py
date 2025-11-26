"""Test helpers for creating scenarios with DTOs."""

from datetime import UTC
from datetime import datetime
from datetime import timedelta

from workshop_operations.domain.aggregates.train import Train
from workshop_operations.domain.entities.track import Track
from workshop_operations.domain.entities.track import TrackType
from workshop_operations.domain.entities.wagon import Wagon

from configuration.application.dtos.locomotive_input_dto import LocomotiveInputDTO
from configuration.application.dtos.route_input_dto import RouteInputDTO
from configuration.application.dtos.workshop_input_dto import WorkshopInputDTO
from configuration.domain.models.process_times import ProcessTimes
from configuration.domain.models.scenario import Scenario
from configuration.domain.models.scenario import TrackSelectionStrategy
from configuration.domain.models.topology import Topology


def create_minimal_scenario_with_dtos(
    num_wagons: int,
    num_stations: int,
    retrofit_time: float = 10.0,
    num_workshops: int = 1,
) -> Scenario:
    """Create minimal scenario using DTOs."""
    start_time = datetime(2025, 1, 1, 0, 0, 0, tzinfo=UTC)

    tracks = [
        Track(id='parking', type=TrackType.PARKING, edges=['e1']),
        Track(id='collection', type=TrackType.COLLECTION, edges=['e2']),
        Track(id='retrofit', type=TrackType.RETROFIT, edges=['e3']),
        Track(id='retrofitted', type=TrackType.RETROFITTED, edges=['e4']),
    ]

    routes = [
        RouteInputDTO(route_id='r1', track_sequence=['parking', 'collection'], duration=1.0),
        RouteInputDTO(route_id='r2', track_sequence=['collection', 'retrofit'], duration=1.0),
        RouteInputDTO(route_id='r3', track_sequence=['retrofit', 'parking'], duration=1.0),
        RouteInputDTO(route_id='r7', track_sequence=['retrofitted', 'parking'], duration=1.0),
        RouteInputDTO(route_id='r8', track_sequence=['parking', 'retrofit'], duration=1.0),
    ]

    workshops = []
    edges = [
        {'id': 'e1', 'length': 100.0},
        {'id': 'e2', 'length': 100.0},
        {'id': 'e3', 'length': 100.0},
        {'id': 'e4', 'length': 100.0},
    ]

    for i in range(1, num_workshops + 1):
        ws_id = f'WS{i}'
        edge_id = f'e{4 + i}'
        tracks.append(Track(id=ws_id, type=TrackType.WORKSHOP, edges=[edge_id]))
        edges.append({'id': edge_id, 'length': 100.0})
        routes.extend(
            [
                RouteInputDTO(route_id=f'r_ret_to_{ws_id}', track_sequence=['retrofit', ws_id], duration=1.0),
                RouteInputDTO(route_id=f'r_park_to_{ws_id}', track_sequence=['parking', ws_id], duration=1.0),
                RouteInputDTO(route_id=f'r_{ws_id}_to_ret', track_sequence=[ws_id, 'retrofitted'], duration=1.0),
                RouteInputDTO(route_id=f'r_{ws_id}_to_park', track_sequence=[ws_id, 'parking'], duration=1.0),
            ]
        )
        workshops.append(
            WorkshopInputDTO(
                workshop_id=ws_id,
                track_id=ws_id,
                retrofit_stations=num_stations,
            )
        )

    wagons = [
        Wagon(wagon_id=f'W{i:02d}', length=10.0, needs_retrofit=True, is_loaded=False) for i in range(1, num_wagons + 1)
    ]
    train = Train(train_id='T1', arrival_time=start_time, wagons=wagons)

    return Scenario(
        scenario_id='validation',
        start_date=start_time,
        end_date=start_time + timedelta(days=1),
        track_selection_strategy=TrackSelectionStrategy.LEAST_OCCUPIED,
        retrofit_selection_strategy=TrackSelectionStrategy.LEAST_OCCUPIED,
        locomotives=[
            LocomotiveInputDTO(
                locomotive_id='L1',
                track_id='parking',
                status='AVAILABLE',
            )
        ],
        process_times=ProcessTimes(
            train_to_hump_delay=0.0,
            wagon_hump_interval=0.0,
            wagon_coupling_time=0.0,
            wagon_decoupling_time=0.0,
            wagon_move_to_next_station=0.0,
            wagon_coupling_retrofitted_time=0.0,
            wagon_retrofit_time=retrofit_time,
        ),
        routes=routes,
        topology=Topology({'edges': edges}),
        trains=[train],
        tracks=tracks,
        workshops=workshops,
    )
