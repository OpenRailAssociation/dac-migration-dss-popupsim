"""Scenario configuration analyzer - extracts metrics from scenario config."""

from typing import Any

import pandas as pd


class ScenarioAnalyzer:
    """Analyzes scenario configuration and calculates derived metrics."""

    AVG_WAGON_LENGTH_M = 20.0  # Average freight wagon length in meters

    def __init__(self, config: dict[str, Any]) -> None:
        """Initialize analyzer with scenario configuration."""
        self.config = config

    def get_overview_metrics(self) -> dict[str, Any]:
        """Extract high-level scenario metrics."""
        scenario = self.config.get('scenario', {})
        train_schedule = self.config.get('train_schedule')

        metrics = {
            'scenario_id': scenario.get('id', 'N/A'),
            'description': scenario.get('description', 'N/A'),
            'version': scenario.get('version', 'N/A'),
            'start_date': scenario.get('start_date', 'N/A'),
            'end_date': scenario.get('end_date', 'N/A'),
            'workflow_mode': scenario.get('workflow_mode', 'N/A'),
        }

        if train_schedule is not None and not train_schedule.empty:
            metrics['total_trains'] = train_schedule['train_id'].nunique()
            metrics['total_wagons'] = len(train_schedule)
            metrics['loaded_wagons'] = train_schedule['is_loaded'].sum()
            metrics['needs_retrofit'] = train_schedule['needs_retrofit'].sum()
        else:
            metrics.update(
                {
                    'total_trains': 0,
                    'total_wagons': 0,
                    'loaded_wagons': 0,
                    'needs_retrofit': 0,
                }
            )

        return metrics

    def get_strategy_config(self) -> dict[str, str]:
        """Extract strategy configuration."""
        scenario = self.config.get('scenario', {})
        return {
            'Track Selection': scenario.get('track_selection_strategy', 'N/A'),
            'Collection Track': scenario.get('collection_track_strategy', 'N/A'),
            'Workshop Selection': scenario.get('workshop_selection_strategy', 'N/A'),
            'Parking Selection': scenario.get('parking_selection_strategy', 'N/A'),
            'Parking Strategy': scenario.get('parking_strategy', 'N/A'),
            'Parking Normal Threshold': f'{scenario.get("parking_normal_threshold", 0) * 100:.0f}%',
            'Parking Critical Threshold': f'{scenario.get("parking_critical_threshold", 0) * 100:.0f}%',
        }

    def get_track_summary(self) -> dict[str, Any]:
        """Calculate track capacity summary by type."""
        tracks = self.config.get('tracks', {}).get('tracks', [])
        topology = self.config.get('topology', {}).get('edges', {})

        summary: dict[str, dict[str, Any]] = {}

        for track in tracks:
            track_type = track.get('type', 'unknown')
            track_id = track.get('id', '')

            # Get track length from topology
            edges = track.get('edges', [])
            length_m = sum(topology.get(edge, {}).get('length', 0) for edge in edges)
            capacity_wagons = int(length_m / self.AVG_WAGON_LENGTH_M) if length_m > 0 else 0

            if track_type not in summary:
                summary[track_type] = {'count': 0, 'total_length_m': 0, 'total_capacity_wagons': 0, 'tracks': []}

            summary[track_type]['count'] += 1
            summary[track_type]['total_length_m'] += length_m
            summary[track_type]['total_capacity_wagons'] += capacity_wagons
            summary[track_type]['tracks'].append(
                {'id': track_id, 'length_m': length_m, 'capacity_wagons': capacity_wagons}
            )

        return summary

    def get_workshop_summary(self) -> dict[str, Any]:
        """Extract workshop configuration summary."""
        workshops_data = self.config.get('workshops', {})
        workshops = workshops_data.get('workshops', [])

        total_bays = sum(ws.get('retrofit_stations', 0) for ws in workshops)

        return {
            'total_workshops': len(workshops),
            'total_bays': total_bays,
            'workshops': [
                {
                    'id': ws.get('id', 'N/A'),
                    'name': ws.get('name', 'N/A'),
                    'bays': ws.get('retrofit_stations', 0),
                    'track': ws.get('track', 'N/A'),
                }
                for ws in workshops
            ],
        }

    def get_locomotive_summary(self) -> dict[str, Any]:
        """Extract locomotive configuration."""
        loco_data = self.config.get('locomotive', {})
        locomotives = loco_data.get('locomotives', [])

        return {
            'total_locomotives': len(locomotives),
            'locomotives': [
                {
                    'id': loco.get('id', 'N/A'),
                    'name': loco.get('name', 'N/A'),
                    'home_track': loco.get('home track', 'N/A'),
                }
                for loco in locomotives
            ],
        }

    def get_process_times(self) -> dict[str, float]:
        """Extract process time configuration."""
        return self.config.get('process_times', {})

    def get_train_arrival_timeline(self) -> pd.DataFrame | None:
        """Get train arrival timeline for visualization."""
        train_schedule = self.config.get('train_schedule')
        if train_schedule is None or train_schedule.empty:
            return None

        # Group by train and get first arrival time
        train_arrivals = (
            train_schedule.groupby('train_id')
            .agg({'arrival_time': 'first', 'wagon_id': 'count', 'is_loaded': 'sum', 'needs_retrofit': 'sum'})
            .reset_index()
        )

        train_arrivals.columns = ['train_id', 'arrival_time', 'wagon_count', 'loaded_count', 'retrofit_count']
        train_arrivals['arrival_time'] = pd.to_datetime(train_arrivals['arrival_time'])

        return train_arrivals.sort_values('arrival_time')

    def calculate_capacity_analysis(self) -> dict[str, Any]:
        """Calculate capacity vs demand analysis."""
        track_summary = self.get_track_summary()
        workshop_summary = self.get_workshop_summary()
        overview = self.get_overview_metrics()
        process_times = self.get_process_times()

        # Collection track capacity
        collection_tracks = track_summary.get('collection', {})
        collection_capacity = collection_tracks.get('total_capacity_wagons', 0)

        # Retrofit track capacity
        retrofit_tracks = track_summary.get('retrofit', {})
        retrofit_capacity = retrofit_tracks.get('total_capacity_wagons', 0)

        # Workshop capacity
        total_bays = workshop_summary.get('total_bays', 0)
        retrofit_time = process_times.get('wagon_retrofit_time', 60.0)

        # Theoretical minimum duration (minutes)
        wagons_to_retrofit = overview.get('needs_retrofit', 0)
        theoretical_min_duration = (wagons_to_retrofit * retrofit_time) / total_bays if total_bays > 0 else 0

        return {
            'collection_capacity': collection_capacity,
            'retrofit_capacity': retrofit_capacity,
            'workshop_bays': total_bays,
            'wagons_to_process': wagons_to_retrofit,
            'theoretical_min_duration_min': theoretical_min_duration,
            'theoretical_min_duration_hours': theoretical_min_duration / 60,
            'bottleneck_track': 'retrofit' if retrofit_capacity < collection_capacity else 'collection',
            'bottleneck_capacity': min(collection_capacity, retrofit_capacity),
        }
