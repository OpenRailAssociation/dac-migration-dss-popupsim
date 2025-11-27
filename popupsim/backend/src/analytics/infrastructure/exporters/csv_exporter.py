"""CSV export for analytics results."""

from pathlib import Path
from typing import Any

from analytics.domain.models.kpi_result import KPIResult
import pandas as pd


class CSVExporter:
    """Export analytics results to CSV files."""

    def export_kpis(self, kpi_result: KPIResult, output_dir: Path) -> None:
        """Export KPI results to CSV files.

        Parameters
        ----------
        kpi_result : KPIResult
            KPI results to export.
        output_dir : Path
            Output directory for CSV files.
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        self._export_throughput(kpi_result, output_dir)
        self._export_utilization(kpi_result, output_dir)
        self._export_bottlenecks(kpi_result, output_dir)

    def export_time_series(self, metrics: dict[str, list[dict[str, Any]]], output_dir: Path) -> None:
        """Export time-series metrics to CSV.

        Parameters
        ----------
        metrics : dict[str, list[dict[str, Any]]]
            Metrics grouped by category.
        output_dir : Path
            Output directory for CSV files.
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        for category, metric_list in metrics.items():
            if metric_list:
                df = pd.DataFrame(metric_list)
                output_file = output_dir / f'{category}_metrics.csv'
                df.to_csv(output_file, index=False)

    def _export_throughput(self, kpi_result: KPIResult, output_dir: Path) -> None:
        """Export throughput KPIs."""
        data = {
            'metric': [
                'total_wagons_processed',
                'total_wagons_retrofitted',
                'total_wagons_rejected',
                'simulation_duration_hours',
                'wagons_per_hour',
                'wagons_per_day',
            ],
            'value': [
                kpi_result.throughput.total_wagons_processed,
                kpi_result.throughput.total_wagons_retrofitted,
                kpi_result.throughput.total_wagons_rejected,
                kpi_result.throughput.simulation_duration_hours,
                kpi_result.throughput.wagons_per_hour,
                kpi_result.throughput.wagons_per_day,
            ],
        }
        df = pd.DataFrame(data)
        df.to_csv(output_dir / 'throughput_kpis.csv', index=False)

    def _export_utilization(self, kpi_result: KPIResult, output_dir: Path) -> None:
        """Export utilization KPIs."""
        if not kpi_result.utilization:
            return

        data = {
            'workshop_id': [u.id for u in kpi_result.utilization],
            'total_capacity': [u.total_capacity for u in kpi_result.utilization],
            'average_utilization_percent': [u.average_utilization_percent for u in kpi_result.utilization],
            'peak_utilization_percent': [u.peak_utilization_percent for u in kpi_result.utilization],
            'idle_time_percent': [u.idle_time_percent for u in kpi_result.utilization],
        }
        df = pd.DataFrame(data)
        df.to_csv(output_dir / 'utilization_kpis.csv', index=False)

    def _export_bottlenecks(self, kpi_result: KPIResult, output_dir: Path) -> None:
        """Export bottleneck information."""
        if not kpi_result.bottlenecks:
            return

        data = {
            'location': [b.location for b in kpi_result.bottlenecks],
            'type': [b.type for b in kpi_result.bottlenecks],
            'severity': [b.severity for b in kpi_result.bottlenecks],
            'description': [b.description for b in kpi_result.bottlenecks],
            'impact_wagons_per_hour': [b.impact_wagons_per_hour for b in kpi_result.bottlenecks],
        }
        df = pd.DataFrame(data)
        df.to_csv(output_dir / 'bottlenecks.csv', index=False)

    def export_all(self, kpi_result: KPIResult, output_dir: Path) -> list[Path]:
        """Export all KPI results to CSV files.

        Parameters
        ----------
        kpi_result : KPIResult
            KPI results to export.
        output_dir : Path
            Output directory for CSV files.

        Returns
        -------
        list[Path]
            List of paths to generated CSV files.
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        csv_files = []

        # Export throughput
        throughput_path = output_dir / 'throughput_kpis.csv'
        self._export_throughput(kpi_result, output_dir)
        csv_files.append(throughput_path)

        # Export utilization
        if kpi_result.utilization:
            utilization_path = output_dir / 'utilization_kpis.csv'
            self._export_utilization(kpi_result, output_dir)
            csv_files.append(utilization_path)

        # Export bottlenecks
        if kpi_result.bottlenecks:
            bottlenecks_path = output_dir / 'bottlenecks.csv'
            self._export_bottlenecks(kpi_result, output_dir)
            csv_files.append(bottlenecks_path)

        return csv_files
