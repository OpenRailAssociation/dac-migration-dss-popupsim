"""CSV exporter for time-series data."""

import csv
from pathlib import Path
from typing import Any


class CSVExporter:
    """Export time-series data to CSV format."""

    def export_time_series(self, time_series_data: dict[str, list[tuple[float, Any]]], output_path: Path) -> None:
        """Export time-series data to CSV."""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)

            # Write header
            writer.writerow(['timestamp', 'metric', 'value'])

            # Write data
            for metric_name, time_series in time_series_data.items():
                for timestamp, value in time_series:
                    if isinstance(value, dict):
                        for sub_key, sub_value in value.items():
                            writer.writerow([timestamp, f'{metric_name}_{sub_key}', sub_value])
                    else:
                        writer.writerow([timestamp, metric_name, value])

    def export_utilization_breakdown(self, breakdown_data: dict[str, Any], output_path: Path) -> None:
        """Export utilization breakdown to CSV."""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)

            # Write header
            writer.writerow(['resource_type', 'resource_id', 'action', 'time_hours', 'percentage'])

            # Write locomotive data
            if 'locomotive_breakdown' in breakdown_data:
                loco = breakdown_data['locomotive_breakdown']
                for action, time_val in loco.action_times.items():
                    percentage = loco.action_percentages.get(action, 0)
                    writer.writerow(['locomotive', 'fleet', action, time_val, percentage])

            # Write wagon data
            if 'wagon_breakdown' in breakdown_data:
                wagon = breakdown_data['wagon_breakdown']
                for action, time_val in wagon.action_times.items():
                    percentage = wagon.action_percentages.get(action, 0)
                    writer.writerow(['wagon', 'fleet', action, time_val, percentage])

            # Write workshop data
            if 'workshop_breakdowns' in breakdown_data:
                for workshop_id, workshop in breakdown_data['workshop_breakdowns'].items():
                    for action, time_val in workshop.action_times.items():
                        percentage = workshop.action_percentages.get(action, 0)
                        writer.writerow(['workshop', workshop_id, action, time_val, percentage])
