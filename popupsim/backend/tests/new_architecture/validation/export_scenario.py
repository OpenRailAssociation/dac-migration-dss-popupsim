"""Export validation test scenario to JSON files."""

import json
from pathlib import Path
import sys

src_path = Path(__file__).parent.parent.parent.parent / 'src'
sys.path.insert(0, str(src_path))

from scenario_builder import create_minimal_scenario


def export_scenario_to_json(scenario, output_dir: Path) -> None:
    """Export scenario to JSON files."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Workshops
    workshops = [{'id': w.id, 'track': w.track, 'retrofit_stations': w.retrofit_stations} for w in scenario.workshops]
    (output_dir / 'workshops.json').write_text(json.dumps(workshops, indent=2))

    # Routes
    routes = [{'id': r.id, 'duration': r.duration, 'track_sequence': r.track_sequence} for r in scenario.routes]
    (output_dir / 'routes.json').write_text(json.dumps(routes, indent=2))

    # Locomotives
    locomotives = [{'id': l.id, 'track': l.track} for l in scenario.locomotives]
    (output_dir / 'locomotives.json').write_text(json.dumps(locomotives, indent=2))

    # Process times (convert timedelta to seconds)
    pt = scenario.process_times

    def to_seconds(val):
        return val.total_seconds() if hasattr(val, 'total_seconds') else val

    process_times = {
        'wagon_retrofit_time': to_seconds(pt.wagon_retrofit_time),
        'train_to_hump_delay': to_seconds(pt.train_to_hump_delay),
        'wagon_hump_interval': to_seconds(pt.wagon_hump_interval),
        'screw_coupling_time': to_seconds(pt.screw_coupling_time),
        'screw_decoupling_time': to_seconds(pt.screw_decoupling_time),
        'dac_coupling_time': to_seconds(pt.dac_coupling_time),
        'dac_decoupling_time': to_seconds(pt.dac_decoupling_time),
    }
    (output_dir / 'process_times.json').write_text(json.dumps(process_times, indent=2))

    # Trains
    trains = []
    for train in scenario.trains:
        arrival_time = (
            train.arrival_time.isoformat() if hasattr(train.arrival_time, 'isoformat') else train.arrival_time
        )
        trains.append(
            {
                'train_id': train.train_id,
                'arrival_time': arrival_time,
                'arrival_track': train.arrival_track,
                'wagons': [{'id': w.id, 'length': w.length} for w in train.wagons],
            }
        )
    (output_dir / 'trains.json').write_text(json.dumps(trains, indent=2))


if __name__ == '__main__':
    scenario = create_minimal_scenario(num_wagons=7, num_stations=2, retrofit_time=10.0, num_workshops=2)

    output_dir = (
        Path(__file__).parent.parent.parent.parent.parent.parent.parent
        / 'Data'
        / 'examples'
        / 'seven_wagons_two_workshops'
    )
    export_scenario_to_json(scenario, output_dir)
    print(f'Scenario exported to {output_dir}')
    for file in sorted(output_dir.glob('*.json')):
        print(f'  - {file.name}')
