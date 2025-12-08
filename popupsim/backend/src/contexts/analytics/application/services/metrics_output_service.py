"""Application service for metrics output and reporting."""

import csv
import json
from pathlib import Path
from typing import Any

from contexts.analytics.domain.services.metrics_query_service import (
    MetricsQueryService,
)


class MetricsOutputService:
    """Application service for formatting and outputting metrics."""

    def __init__(self, query_service: MetricsQueryService) -> None:
        self._query = query_service

    def generate_summary_report(self) -> dict[str, Any]:
        """Generate complete metrics summary."""
        return {
            "train_arrivals": self._format_train_arrivals(),
            "wagon_metrics": self._format_wagon_metrics(),
            "locomotive_utilization": self._format_locomotive_utilization(),
            "workshop_metrics": self._format_workshop_metrics(),
            "bottlenecks": self._format_bottlenecks(),
        }

    def _format_train_arrivals(self) -> dict[str, Any]:
        """Format train arrival metrics."""
        metrics = self._query.get_train_arrivals()
        return {
            "total_arrivals": metrics.total_arrivals,
            "total_wagons": metrics.total_wagons,
            "arrivals_by_time": metrics.arrivals_by_time,
        }

    def _format_wagon_metrics(self) -> dict[str, Any]:
        """Format wagon metrics."""
        metrics = self._query.get_wagon_metrics()
        return {
            "retrofitted": metrics.retrofitted_count,
            "rejected": metrics.rejected_count,
            "in_parking": metrics.in_parking_count,
            "retrofitting": metrics.retrofitting_count,
            "on_retrofit_track": metrics.on_retrofit_track_count,
            "on_retrofitted_track": metrics.on_retrofitted_track_count,
        }

    def _format_locomotive_utilization(self) -> dict[str, Any]:
        """Format locomotive utilization metrics."""
        all_locos = self._query.get_all_locomotive_utilizations()
        return {
            loco_id: {
                "parking_time": util.parking_time,
                "moving_time": util.moving_time,
                "coupling_time": util.coupling_time,
                "decoupling_time": util.decoupling_time,
                "total_time": util.total_time,
                "parking_percentage": util.parking_percentage,
                "moving_percentage": util.moving_percentage,
                "coupling_percentage": util.coupling_percentage,
                "decoupling_percentage": util.decoupling_percentage,
            }
            for loco_id, util in all_locos.items()
        }

    def _format_workshop_metrics(self) -> dict[str, Any]:
        """Format workshop metrics."""
        all_workshops = self._query.get_all_workshop_metrics()
        return {
            workshop_id: {
                "completed_retrofits": metrics.completed_retrofits,
                "working_time": metrics.total_working_time,
                "waiting_time": metrics.total_waiting_time,
                "wagons_per_hour": metrics.wagons_per_hour,
                "working_percentage": metrics.working_percentage,
                "waiting_percentage": metrics.waiting_percentage,
            }
            for workshop_id, metrics in all_workshops.items()
        }

    def _format_bottlenecks(self) -> list[dict[str, Any]]:
        """Format bottleneck detection results."""
        bottlenecks = self._query.detect_bottlenecks()
        return [
            {
                "resource_type": b.resource_type,
                "resource_id": b.resource_id,
                "utilization_percentage": b.utilization_percentage,
                "severity": b.severity,
            }
            for b in bottlenecks
        ]

    def export_to_csv(self, output_dir: Path) -> None:
        """Export metrics to CSV files."""
        output_dir.mkdir(parents=True, exist_ok=True)

        # Export locomotive utilization
        loco_file = output_dir / "locomotive_utilization.csv"
        with loco_file.open("w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "locomotive_id",
                    "parking_time",
                    "moving_time",
                    "coupling_time",
                    "decoupling_time",
                    "total_time",
                    "parking_%",
                    "moving_%",
                    "coupling_%",
                    "decoupling_%",
                ]
            )
            for loco_id, util in self._query.get_all_locomotive_utilizations().items():
                writer.writerow(
                    [
                        loco_id,
                        util.parking_time,
                        util.moving_time,
                        util.coupling_time,
                        util.decoupling_time,
                        util.total_time,
                        util.parking_percentage,
                        util.moving_percentage,
                        util.coupling_percentage,
                        util.decoupling_percentage,
                    ]
                )

        # Export workshop metrics
        workshop_file = output_dir / "workshop_metrics.csv"
        with workshop_file.open("w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "workshop_id",
                    "completed_retrofits",
                    "working_time",
                    "waiting_time",
                    "wagons_per_hour",
                    "working_%",
                    "waiting_%",
                ]
            )
            for workshop_id, metrics in self._query.get_all_workshop_metrics().items():
                writer.writerow(
                    [
                        workshop_id,
                        metrics.completed_retrofits,
                        metrics.total_working_time,
                        metrics.total_waiting_time,
                        metrics.wagons_per_hour,
                        metrics.working_percentage,
                        metrics.waiting_percentage,
                    ]
                )

        # Export bottlenecks
        bottleneck_file = output_dir / "bottlenecks.csv"
        with bottleneck_file.open("w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(
                ["resource_type", "resource_id", "utilization_%", "severity"]
            )
            for bottleneck in self._query.detect_bottlenecks():
                writer.writerow(
                    [
                        bottleneck.resource_type,
                        bottleneck.resource_id,
                        bottleneck.utilization_percentage,
                        bottleneck.severity,
                    ]
                )

    def export_to_json(self, output_file: Path) -> None:
        """Export complete metrics summary to JSON."""
        output_file.parent.mkdir(parents=True, exist_ok=True)
        summary = self.generate_summary_report()

        with output_file.open("w") as f:
            json.dump(summary, f, indent=2)
