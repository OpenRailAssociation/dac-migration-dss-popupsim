"""Visualization service for Analytics Context."""

from pathlib import Path
from typing import Any

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

from contexts.analytics.domain.value_objects.analytics_config import (
    AnalyticsConfig,
)

mpl.use("Agg")  # Non-interactive backend


class Visualizer:
    """Generate charts from Analytics Context data."""

    def __init__(self, config: AnalyticsConfig | None = None) -> None:
        self.config = config or AnalyticsConfig()
        self.colors = {
            "primary": "#2196F3",
            "success": "#4CAF50",
            "warning": "#FF9800",
            "error": "#F44336",
            "info": "#9C27B0",
            "secondary": "#607D8B",
        }

    def generate_operational_dashboard(
        self, metrics: dict[str, Any], output_path: Path
    ) -> None:
        """Generate comprehensive operational dashboard."""
        fig, (ax1, ax2, ax3) = plt.subplots(
            1, 3, figsize=(15, 5)
        )

        # Throughput metrics
        self._plot_throughput_metrics(ax1, metrics)

        # Locomotive activity breakdown
        self._plot_locomotive_activity(ax2, metrics)

        # Bay utilization
        self._plot_capacity_utilization(ax3, metrics)

        plt.suptitle("PopUpSim Operational Dashboard", fontsize=16, fontweight="bold")
        plt.tight_layout()
        plt.savefig(output_path, dpi=self.config.chart_dpi, bbox_inches="tight")
        plt.close(fig)

    def generate_kpi_status_chart(
        self, kpi_summary: dict[str, Any], output_path: Path
    ) -> None:
        """Generate KPI status visualization."""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=self.config.chart_figsize_kpi)

        # KPI status distribution pie chart
        status_dist = kpi_summary.get("status_distribution", {})
        if status_dist:
            labels = list(status_dist.keys())
            sizes = list(status_dist.values())
            colors = [
                self.colors["success"],
                self.colors["primary"],
                self.colors["warning"],
                self.colors["error"],
            ]

            ax1.pie(
                sizes, labels=labels, colors=colors, autopct="%1.1f%%", startangle=90
            )
            ax1.set_title("KPI Status Distribution")

        # Individual KPI values
        kpis = kpi_summary.get("kpis", [])
        if kpis:
            names = [kpi["name"] for kpi in kpis]
            values = [kpi["value"] for kpi in kpis]
            statuses = [kpi["status"] for kpi in kpis]

            colors_map = {
                "excellent": self.colors["success"],
                "good": self.colors["primary"],
                "warning": self.colors["warning"],
                "critical": self.colors["error"],
            }
            bar_colors = [
                colors_map.get(status, self.colors["secondary"]) for status in statuses
            ]

            bars = ax2.barh(names, values, color=bar_colors, alpha=0.8)
            ax2.set_xlabel("KPI Value")
            ax2.set_title("Individual KPI Performance")
            ax2.grid(axis="x", alpha=0.3)

            # Add value labels
            for bar, value in zip(bars, values, strict=False):
                ax2.text(
                    bar.get_width() + 0.01,
                    bar.get_y() + bar.get_height() / 2,
                    f"{value:.3f}",
                    va="center",
                    fontweight="bold",
                )

        plt.tight_layout()
        plt.savefig(output_path, dpi=self.config.chart_dpi, bbox_inches="tight")
        plt.close(fig)

    def generate_flow_analysis_chart(
        self, cross_context_data: dict[str, Any], output_path: Path
    ) -> None:
        """Generate track occupancy line chart."""
        fig, ax = plt.subplots(1, 1, figsize=(14, 6))
        
        track_history = cross_context_data.get("track_occupancy_history", {})
        
        # All tracks to display
        key_tracks = ["collection", "WS1", "WS2", "parking", "retrofit", "retrofitted", "locoparking"]
        colors_map = {
            "collection": "#9C27B0",
            "WS1": self.colors["primary"],
            "WS2": self.colors["error"],
            "parking": self.colors["secondary"],
            "retrofit": self.colors["warning"],
            "retrofitted": self.colors["success"],
            "locoparking": "#795548",
        }
        
        if track_history:
            for track in key_tracks:
                if track in track_history:
                    history = track_history[track]
                    if history:
                        times = [t for t, _ in history]
                        counts = [c for _, c in history]
                        ax.plot(times, counts, label=track, color=colors_map.get(track, self.colors["secondary"]), 
                               linewidth=2, marker='o', markersize=3)
            
            ax.set_xlabel("Time (minutes)")
            ax.set_ylabel("Wagon Count")
            ax.set_title("Track Occupancy Over Time")
            ax.legend()
            ax.grid(alpha=0.3)
        else:
            ax.text(0.5, 0.5, "No track occupancy data available", 
                    ha="center", va="center", transform=ax.transAxes, fontsize=14)
            ax.set_title("Track Occupancy Over Time")
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=self.config.chart_dpi, bbox_inches="tight")
        plt.close(fig)

    def _plot_throughput_metrics(self, ax: plt.Axes, metrics: dict[str, Any]) -> None:
        """Plot throughput metrics."""
        categories = ["Arrived", "Completed", "Rejected"]
        values = [
            metrics.get("wagons_arrived", 0),
            metrics.get("retrofits_completed", 0),
            metrics.get("wagons_rejected", 0),
        ]
        colors = [self.colors["info"], self.colors["success"], self.colors["error"]]

        bars = ax.bar(categories, values, color=colors, alpha=0.8)
        ax.set_ylabel("Number of Wagons")
        ax.set_title("Wagon Throughput")
        ax.grid(axis="y", alpha=0.3)

        # Add value labels
        for bar, value in zip(bars, values, strict=False):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + max(values) * 0.02,
                str(value),
                ha="center",
                va="bottom",
                fontweight="bold",
            )

    def _plot_workshop_utilization(self, ax: plt.Axes, metrics: dict[str, Any]) -> None:
        """Plot workshop utilization."""
        workshop_stats = metrics.get("workshop_statistics", {})
        workshops = workshop_stats.get("workshops", {})

        if workshops:
            names = list(workshops.keys())
            utilizations = [w["utilization_percent"] for w in workshops.values()]

            bars = ax.bar(names, utilizations, color=self.colors["primary"], alpha=0.8)
            ax.set_ylabel("Utilization (%)")
            ax.set_title("Workshop Utilization")
            ax.set_ylim(0, 100)
            ax.grid(axis="y", alpha=0.3)

            # Add value labels
            for bar, util in zip(bars, utilizations, strict=False):
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 2,
                    f"{util:.1f}%",
                    ha="center",
                    va="bottom",
                    fontweight="bold",
                )
        else:
            ax.text(
                0.5,
                0.5,
                "No workshop data",
                ha="center",
                va="center",
                transform=ax.transAxes,
            )
            ax.set_title("Workshop Utilization")

    def _plot_locomotive_activity(self, ax: plt.Axes, metrics: dict[str, Any]) -> None:
        """Plot locomotive activity breakdown per locomotive."""
        shunting = metrics.get("shunting", {})
        per_loco = shunting.get("per_locomotive_breakdown", {})

        if per_loco:
            locos = list(per_loco.keys())
            statuses = ["MOVING", "PARKING", "COUPLING", "DECOUPLING"]
            colors_map = {
                "MOVING": self.colors["primary"],
                "PARKING": self.colors["secondary"],
                "COUPLING": self.colors["success"],
                "DECOUPLING": self.colors["warning"],
            }
            
            x = range(len(locos))
            width = 0.2
            for i, status in enumerate(statuses):
                values = [per_loco[loco].get(status, 0) for loco in locos]
                ax.bar([xi + i * width for xi in x], values, width, label=status, color=colors_map[status], alpha=0.8)
            
            ax.set_ylabel("Time (%)")
            ax.set_title("Locomotive Activity Breakdown")
            ax.set_xticks([xi + width * 1.5 for xi in x])
            ax.set_xticklabels(locos)
            ax.set_ylim(0, 100)
            ax.legend()
            ax.grid(axis="y", alpha=0.3)
        else:
            ax.text(0.5, 0.5, "No locomotive data", ha="center", va="center", transform=ax.transAxes)
            ax.set_title("Locomotive Activity Breakdown")

    def _plot_capacity_utilization(self, ax: plt.Axes, metrics: dict[str, Any]) -> None:
        """Plot bay utilization."""
        popup = metrics.get("popup", {})
        per_bay = popup.get("per_bay_utilization", {})

        if per_bay:
            bays = list(per_bay.keys())
            utilizations = list(per_bay.values())

            bars = ax.barh(bays, utilizations, color=self.colors["success"], alpha=0.8)
            ax.set_xlabel("Utilization (%)")
            ax.set_title("Bay Utilization")
            ax.set_xlim(0, 100)
            ax.grid(axis="x", alpha=0.3)

            for i, util in enumerate(utilizations):
                ax.text(util + 2, i, f"{util:.1f}%", va="center", fontweight="bold")
        else:
            ax.text(0.5, 0.5, "No bay data", ha="center", va="center", transform=ax.transAxes)
            ax.set_title("Bay Utilization")

    def generate_all_charts(
        self, analytics_context: Any, output_dir: Path, context_metrics: dict[str, Any] | None = None
    ) -> list[Path]:
        """Generate all charts."""
        output_dir.mkdir(parents=True, exist_ok=True)
        chart_paths = []

        # Get data from analytics context
        metrics = analytics_context.get_metrics()
        
        # Merge with context metrics if provided
        if context_metrics:
            metrics.update(context_metrics)
        
        kpi_summary = analytics_context.get_kpis()
        cross_context_data = analytics_context.get_context_analysis()
        
        # Add track occupancy history
        track_history = {}
        for track in analytics_context.event_stream.track_occupancy.get_all_tracks():
            track_history[track] = analytics_context.event_stream.track_occupancy.get_track_history(track)
        cross_context_data["track_occupancy_history"] = track_history

        # Generate dashboard
        dashboard_path = output_dir / "operational_dashboard.png"
        self.generate_operational_dashboard(metrics, dashboard_path)
        chart_paths.append(dashboard_path)

        # Generate KPI status chart
        kpi_path = output_dir / "kpi_status.png"
        self.generate_kpi_status_chart(kpi_summary, kpi_path)
        chart_paths.append(kpi_path)

        # Generate flow analysis
        flow_path = output_dir / "flow_analysis.png"
        self.generate_flow_analysis_chart(cross_context_data, flow_path)
        chart_paths.append(flow_path)

        return chart_paths
