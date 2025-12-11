"""Visualization service for Analytics Context."""

from pathlib import Path
from typing import Any

from contexts.analytics.domain.value_objects.analytics_config import AnalyticsConfig
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

mpl.use('Agg')  # Non-interactive backend


class Visualizer:
    """Generate charts from Analytics Context data."""

    def __init__(self, config: AnalyticsConfig | None = None) -> None:
        self.config = config or AnalyticsConfig()
        self.colors = {
            'primary': '#2196F3',
            'success': '#4CAF50',
            'warning': '#FF9800',
            'error': '#F44336',
            'info': '#9C27B0',
            'secondary': '#607D8B',
        }

    def generate_operational_dashboard(self, metrics: dict[str, Any], output_path: Path) -> None:
        """Generate comprehensive operational dashboard with high-quality graphs."""
        fig = plt.figure(figsize=(18, 6))
        gs = fig.add_gridspec(1, 3, hspace=0.3, wspace=0.3)
        ax1 = fig.add_subplot(gs[0, 0])
        ax2 = fig.add_subplot(gs[0, 1])
        ax3 = fig.add_subplot(gs[0, 2])

        # Wagon flow metrics
        self._plot_wagon_flow(ax1, metrics)

        # Locomotive activity breakdown per locomotive
        self._plot_locomotive_breakdown(ax2, metrics)

        # Workshop bay utilization
        self._plot_bay_utilization(ax3, metrics)

        plt.suptitle('PopUpSim Operational Dashboard', fontsize=18, fontweight='bold', y=0.98)
        plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close(fig)

    def generate_kpi_status_chart(self, kpi_summary: dict[str, Any], output_path: Path) -> None:
        """Generate KPI status visualization."""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=self.config.chart_figsize_kpi)

        # KPI status distribution pie chart
        status_dist = kpi_summary.get('status_distribution', {})
        if status_dist:
            labels = list(status_dist.keys())
            sizes = list(status_dist.values())
            colors = [
                self.colors['success'],
                self.colors['primary'],
                self.colors['warning'],
                self.colors['error'],
            ]

            ax1.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
            ax1.set_title('KPI Status Distribution')

        # Individual KPI values
        kpis = kpi_summary.get('kpis', [])
        if kpis:
            names = [kpi['name'] for kpi in kpis]
            values = [kpi['value'] for kpi in kpis]
            statuses = [kpi['status'] for kpi in kpis]

            colors_map = {
                'excellent': self.colors['success'],
                'good': self.colors['primary'],
                'warning': self.colors['warning'],
                'critical': self.colors['error'],
            }
            bar_colors = [colors_map.get(status, self.colors['secondary']) for status in statuses]

            bars = ax2.barh(names, values, color=bar_colors, alpha=0.8)
            ax2.set_xlabel('KPI Value')
            ax2.set_title('Individual KPI Performance')
            ax2.grid(axis='x', alpha=0.3)

            # Add value labels
            for bar, value in zip(bars, values, strict=False):
                ax2.text(
                    bar.get_width() + 0.01,
                    bar.get_y() + bar.get_height() / 2,
                    f'{value:.3f}',
                    va='center',
                    fontweight='bold',
                )

        plt.tight_layout()
        plt.savefig(output_path, dpi=self.config.chart_dpi, bbox_inches='tight')
        plt.close(fig)

    def generate_flow_analysis_chart(self, cross_context_data: dict[str, Any], output_path: Path) -> None:
        """Generate track occupancy line chart."""
        fig, ax = plt.subplots(1, 1, figsize=(14, 6))

        track_history = cross_context_data.get('track_occupancy_history', {})

        # All tracks to display
        key_tracks = ['collection', 'WS1', 'WS2', 'parking', 'retrofit', 'retrofitted', 'locoparking']
        colors_map = {
            'collection': '#9C27B0',
            'WS1': self.colors['primary'],
            'WS2': self.colors['error'],
            'parking': self.colors['secondary'],
            'retrofit': self.colors['warning'],
            'retrofitted': self.colors['success'],
            'locoparking': '#795548',
        }

        if track_history:
            for track in key_tracks:
                if track in track_history:
                    history = track_history[track]
                    if history:
                        times = [t for t, _ in history]
                        counts = [c for _, c in history]
                        ax.plot(
                            times,
                            counts,
                            label=track,
                            color=colors_map.get(track, self.colors['secondary']),
                            linewidth=2,
                            marker='o',
                            markersize=3,
                        )

            ax.set_xlabel('Time (minutes)')
            ax.set_ylabel('Wagon Count')
            ax.set_title('Track Occupancy Over Time')
            ax.legend()
            ax.grid(alpha=0.3)
        else:
            ax.text(
                0.5,
                0.5,
                'No track occupancy data available',
                ha='center',
                va='center',
                transform=ax.transAxes,
                fontsize=14,
            )
            ax.set_title('Track Occupancy Over Time')

        plt.tight_layout()
        plt.savefig(output_path, dpi=self.config.chart_dpi, bbox_inches='tight')
        plt.close(fig)

    def _plot_wagon_flow(self, ax: plt.Axes, metrics: dict[str, Any]) -> None:
        """Plot wagon flow with arrived, retrofitted, parking, and rejected."""
        categories = ['Arrived', 'Retrofitted', 'Parking', 'Rejected']
        values = [
            metrics.get('wagons_arrived', 0),
            metrics.get('retrofits_completed', 0),
            metrics.get('wagons_parked', 0),
            metrics.get('wagons_rejected', 0),
        ]
        colors = ['#3498db', '#2ecc71', '#f39c12', '#e74c3c']

        bars = ax.bar(categories, values, color=colors, edgecolor='black', linewidth=0.8, alpha=0.85)
        ax.set_ylabel('Number of Wagons', fontsize=11, fontweight='bold')
        ax.set_title('Wagon Flow', fontsize=13, fontweight='bold', pad=15)
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        ax.set_axisbelow(True)

        # Add value labels on top of bars
        for bar, value in zip(bars, values, strict=False):
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                height + max(values) * 0.02,
                f'{int(value)}',
                ha='center',
                va='bottom',
                fontsize=10,
                fontweight='bold',
            )

    def _plot_workshop_utilization(self, ax: plt.Axes, metrics: dict[str, Any]) -> None:
        """Plot workshop utilization."""
        workshop_stats = metrics.get('workshop_statistics', {})
        workshops = workshop_stats.get('workshops', {})

        if workshops:
            names = list(workshops.keys())
            utilizations = [w['utilization_percent'] for w in workshops.values()]

            bars = ax.bar(names, utilizations, color=self.colors['primary'], alpha=0.8)
            ax.set_ylabel('Utilization (%)')
            ax.set_title('Workshop Utilization')
            ax.set_ylim(0, 100)
            ax.grid(axis='y', alpha=0.3)

            # Add value labels
            for bar, util in zip(bars, utilizations, strict=False):
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 2,
                    f'{util:.1f}%',
                    ha='center',
                    va='bottom',
                    fontweight='bold',
                )
        else:
            ax.text(
                0.5,
                0.5,
                'No workshop data',
                ha='center',
                va='center',
                transform=ax.transAxes,
            )
            ax.set_title('Workshop Utilization')

    def _plot_locomotive_breakdown(self, ax: plt.Axes, metrics: dict[str, Any]) -> None:
        """Plot locomotive activity breakdown with grouped bars per locomotive."""
        shunting = metrics.get('shunting', {})
        per_loco = shunting.get('per_locomotive_breakdown', {})

        if per_loco:
            locos = sorted(per_loco.keys())
            activities = ['MOVING', 'PARKING', 'COUPLING', 'DECOUPLING']
            colors_map = {
                'MOVING': '#3498db',
                'PARKING': '#95a5a6',
                'COUPLING': '#2ecc71',
                'DECOUPLING': '#f39c12',
            }

            # Create grouped bar chart
            x = np.arange(len(locos))
            width = 0.2

            for i, activity in enumerate(activities):
                values = [per_loco[loco].get(activity, 0) for loco in locos]
                offset = (i - 1.5) * width
                ax.bar(
                    x + offset,
                    values,
                    width,
                    label=activity,
                    color=colors_map[activity],
                    edgecolor='black',
                    linewidth=0.8,
                    alpha=0.85,
                )

            ax.set_ylabel('Utilization (%)', fontsize=11, fontweight='bold')
            ax.set_title('Locomotive Activity Breakdown', fontsize=13, fontweight='bold', pad=15)
            ax.set_xticks(x)
            ax.set_xticklabels(locos, fontsize=10)
            ax.set_ylim(0, 105)
            ax.legend(loc='upper right', fontsize=9, framealpha=0.9)
            ax.grid(axis='y', alpha=0.3, linestyle='--')
            ax.set_axisbelow(True)
        else:
            ax.text(0.5, 0.5, 'No locomotive data', ha='center', va='center', transform=ax.transAxes, fontsize=12)
            ax.set_title('Locomotive Activity Breakdown', fontsize=13, fontweight='bold', pad=15)

    def _plot_bay_utilization(self, ax: plt.Axes, metrics: dict[str, Any]) -> None:
        """Plot workshop bay utilization with horizontal bars."""
        popup = metrics.get('popup', {})
        per_bay = popup.get('per_bay_utilization', {})

        if per_bay:
            bays = sorted(per_bay.keys())
            utilizations = [per_bay[bay] for bay in bays]

            # Color bars based on utilization level
            colors = []
            for util in utilizations:
                if util >= 80:
                    colors.append('#2ecc71')  # Green for high utilization
                elif util >= 50:
                    colors.append('#f39c12')  # Orange for medium
                else:
                    colors.append('#e74c3c')  # Red for low

            ax.set_xlabel('Utilization (%)', fontsize=11, fontweight='bold')
            ax.set_title('Workshop Bay Utilization', fontsize=13, fontweight='bold', pad=15)
            ax.set_xlim(0, 105)
            ax.grid(axis='x', alpha=0.3, linestyle='--')
            ax.set_axisbelow(True)

            # Add value labels at the end of bars
            for i, util in enumerate(utilizations):
                ax.text(util + 2, i, f'{util:.1f}%', va='center', fontsize=10, fontweight='bold')
        else:
            ax.text(0.5, 0.5, 'No bay data', ha='center', va='center', transform=ax.transAxes, fontsize=12)
            ax.set_title('Workshop Bay Utilization', fontsize=13, fontweight='bold', pad=15)

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
        cross_context_data['track_occupancy_history'] = track_history

        # Generate dashboard
        dashboard_path = output_dir / 'operational_dashboard.png'
        self.generate_operational_dashboard(metrics, dashboard_path)
        chart_paths.append(dashboard_path)

        # Generate KPI status chart
        kpi_path = output_dir / 'kpi_status.png'
        self.generate_kpi_status_chart(kpi_summary, kpi_path)
        chart_paths.append(kpi_path)

        # Generate flow analysis
        flow_path = output_dir / 'flow_analysis.png'
        self.generate_flow_analysis_chart(cross_context_data, flow_path)
        chart_paths.append(flow_path)

        return chart_paths
