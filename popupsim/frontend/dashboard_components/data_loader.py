"""Data loader for PopUpSim dashboard - handles all file I/O operations."""

import json
from pathlib import Path
from typing import Any

import pandas as pd


class DataLoader:  # pylint: disable=too-few-public-methods
    """Loads simulation data from output directory.

    Note: Single public method is sufficient for this utility class.
    """

    def __init__(self, output_dir: Path) -> None:
        """Initialize data loader with output directory."""
        self.output_dir = output_dir
        self.scenario_dir = output_dir / 'scenario'

    def load_all(self) -> dict[str, Any]:
        """Load all available data files."""
        data: dict[str, Any] = {}

        # Load simulation results
        data['metrics'] = self._load_json('summary_metrics.json')
        data['wagon_journey'] = self._load_csv('wagon_journey.csv')
        data['rejected_wagons'] = self._load_csv('rejected_wagons.csv')
        data['locomotive_movements'] = self._load_csv('locomotive_movements.csv')
        data['locomotive_journey'] = self._load_csv('locomotive_journey.csv')
        data['track_capacity'] = self._load_csv('track_capacity.csv')
        data['workshop_utilization'] = self._load_csv('workshop_utilization.csv')
        data['locomotive_utilization'] = self._load_csv('locomotive_utilization.csv')
        data['timeline'] = self._load_csv('timeline.csv')
        data['workshop_metrics'] = self._load_csv('workshop_metrics.csv')

        # Load scenario configuration
        data['scenario_config'] = self._load_scenario_config()

        return data

    def _load_json(self, filename: str) -> dict[str, Any] | None:
        """Load JSON file from output directory."""
        filepath = self.output_dir / filename
        if filepath.exists():
            with open(filepath, encoding='utf-8') as f:
                return json.load(f)
        return None

    def _load_csv(self, filename: str) -> pd.DataFrame | None:
        """Load CSV file from output directory."""
        filepath = self.output_dir / filename
        if filepath.exists():
            return pd.read_csv(filepath)
        return None

    def _load_scenario_config(self) -> dict[str, Any]:
        """Load scenario configuration files."""
        if not self.scenario_dir.exists():
            return {}

        config: dict[str, Any] = {}

        # Load JSON configuration files
        json_files = [
            'scenario.json',
            'topology.json',
            'tracks.json',
            'workshops.json',
            'locomotive.json',
            'process_times.json',
            'routes.json',
        ]

        for filename in json_files:
            filepath = self.scenario_dir / filename
            if filepath.exists():
                with open(filepath, encoding='utf-8') as f:
                    key = filename.replace('.json', '')
                    config[key] = json.load(f)

        # Load train schedule CSV
        train_schedule_path = self.scenario_dir / 'train_schedule.csv'
        if train_schedule_path.exists():
            config['train_schedule'] = pd.read_csv(train_schedule_path, sep=';')

        return config
