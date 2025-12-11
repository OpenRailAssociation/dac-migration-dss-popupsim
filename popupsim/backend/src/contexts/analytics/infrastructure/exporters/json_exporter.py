"""JSON exporter for Analytics Context data."""

from datetime import UTC
from datetime import datetime
import json
from pathlib import Path
from typing import Any


class JSONExporter:
    """Export analytics data to JSON format for frontend integration."""

    def __init__(self) -> None:
        self.timestamp_format = '%Y-%m-%d %H:%M:%S'

    def export_metrics(self, metrics: dict[str, Any], output_path: Path) -> None:
        """Export metrics data to JSON file."""
        export_data = {
            'export_timestamp': datetime.now(UTC).strftime(self.timestamp_format),
            'export_type': 'metrics',
            'data': self._sanitize_data(metrics),
        }

        self._write_json(export_data, output_path)

    def export_kpi_summary(self, kpi_summary: dict[str, Any], output_path: Path) -> None:
        """Export KPI summary to JSON file."""
        export_data = {
            'export_timestamp': datetime.now(UTC).strftime(self.timestamp_format),
            'export_type': 'kpi_summary',
            'data': self._sanitize_data(kpi_summary),
        }

        self._write_json(export_data, output_path)

    def export_comprehensive_report(self, analytics_context: Any, output_path: Path) -> None:
        """Export comprehensive analytics report to JSON."""
        report_data = {
            'export_timestamp': datetime.now(UTC).strftime(self.timestamp_format),
            'export_type': 'comprehensive_report',
            'data': {
                'metrics': self._sanitize_data(analytics_context.get_metrics()),
                'kpi_summary': self._sanitize_data(analytics_context.get_advanced_kpis()),
                'cross_context_analysis': self._sanitize_data(analytics_context.get_cross_context_analysis()),
                'real_time_status': self._sanitize_data(analytics_context.get_real_time_status()),
            },
        }

        self._write_json(report_data, output_path)

    def export_dashboard_data(self, analytics_context: Any, output_path: Path) -> None:
        """Export dashboard-ready data for frontend consumption."""
        dashboard_data = {
            'timestamp': datetime.now(UTC).strftime(self.timestamp_format),
            'dashboard': {
                'operational_metrics': self._extract_operational_metrics(analytics_context),
                'kpi_status': self._extract_kpi_status(analytics_context),
                'alerts': self._extract_alerts(analytics_context),
                'performance_summary': self._extract_performance_summary(analytics_context),
            },
        }

        self._write_json(dashboard_data, output_path)

    def export_time_series(self, time_series_data: dict[str, list[tuple[float, Any]]], output_path: Path) -> None:
        """Export time-series data to JSON."""
        export_data = {
            'export_timestamp': datetime.now(UTC).strftime(self.timestamp_format),
            'export_type': 'time_series',
            'data': self._sanitize_data(time_series_data),
        }

        self._write_json(export_data, output_path)

    def _extract_operational_metrics(self, analytics_context: Any) -> dict[str, Any]:
        """Extract key operational metrics for dashboard."""
        metrics = analytics_context.get_metrics()
        return {
            'throughput': {
                'wagons_arrived': metrics.get('wagons_arrived', 0),
                'retrofits_completed': metrics.get('retrofits_completed', 0),
                'wagons_rejected': metrics.get('wagons_rejected', 0),
                'completion_rate': metrics.get('completion_rate', 0.0),
                'throughput_rate_per_hour': metrics.get('throughput_rate_per_hour', 0.0),
            },
            'utilization': {
                'workshops': metrics.get('workshop_statistics', {}).get('workshops', {}),
                'locomotives': metrics.get('locomotive_statistics', {}),
                'capacity': metrics.get('capacity_statistics', {}),
            },
        }

    def _extract_kpi_status(self, analytics_context: Any) -> dict[str, Any]:
        """Extract KPI status for dashboard."""
        kpi_summary = analytics_context.get_advanced_kpis()
        return {
            'overall_score': kpi_summary.get('overall_score', 0.0),
            'status_distribution': kpi_summary.get('status_distribution', {}),
            'critical_kpis': [
                kpi for kpi in kpi_summary.get('kpis', []) if kpi.get('status') in ['critical', 'warning']
            ],
        }

    def _extract_alerts(self, analytics_context: Any) -> dict[str, Any]:
        """Extract current alerts for dashboard."""
        status = analytics_context.get_real_time_status()
        return {
            'active_alerts': status.get('active_alerts', []),
            'system_health': status.get('system_health', 'unknown'),
            'alert_summary': status.get('alert_summary', {}),
        }

    def _extract_performance_summary(self, analytics_context: Any) -> dict[str, Any]:
        """Extract performance summary for dashboard."""
        cross_context = analytics_context.get_cross_context_analysis()
        return {
            'bottlenecks': cross_context.get('bottleneck_analysis', {}).get('bottlenecks', []),
            'flow_efficiency': cross_context.get('flow_analysis', {}).get('overall_efficiency', 0.0),
            'system_status': cross_context.get('system_status', 'unknown'),
        }

    def _sanitize_data(self, data: Any) -> Any:
        """Sanitize data for JSON serialization."""
        if isinstance(data, dict):
            return {k: self._sanitize_data(v) for k, v in data.items()}
        if isinstance(data, list):
            return [self._sanitize_data(item) for item in data]
        if isinstance(data, (int, float, str, bool)) or data is None:
            return data
        # Convert non-serializable objects to string
        return str(data)

    def _write_json(self, data: dict[str, Any], output_path: Path) -> None:
        """Write data to JSON file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with output_path.open('w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
