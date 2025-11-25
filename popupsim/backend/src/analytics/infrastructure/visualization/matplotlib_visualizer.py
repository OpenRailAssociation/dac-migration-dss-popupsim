"""Visualization service for generating charts from KPI results."""

from pathlib import Path

from analytics.domain.models.kpi_result import KPIResult
import matplotlib
import matplotlib.pyplot as plt

matplotlib.use('Agg')  # Use non-interactive backend for headless environments


class Visualizer:
    """Generate charts from KPI results using Matplotlib."""

    def generate_throughput_chart(self, result: KPIResult, output_path: Path) -> None:
        """Generate bar chart showing wagon throughput metrics.

        Parameters
        ----------
        result : KPIResult
            KPI calculation results containing throughput data.
        output_path : Path
            Path where the chart PNG will be saved.
        """
        fig, ax = plt.subplots(figsize=(10, 6))

        categories = ['Processed', 'Retrofitted', 'Rejected']
        values = [
            result.throughput.total_wagons_processed,
            result.throughput.total_wagons_retrofitted,
            result.throughput.total_wagons_rejected,
        ]
        colors = ['#2196F3', '#4CAF50', '#F44336']

        ax.bar(categories, values, color=colors, alpha=0.8)
        ax.set_ylabel('Number of Wagons')
        ax.set_title('Wagon Throughput Summary')
        ax.grid(axis='y', alpha=0.3)

        # Add value labels on bars
        for i, v in enumerate(values):
            ax.text(i, v + max(values) * 0.02, str(v), ha='center', va='bottom', fontweight='bold')

        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close(fig)

    def generate_utilization_chart(self, result: KPIResult, output_path: Path) -> None:
        """Generate bar chart showing workshop utilization percentages.

        Parameters
        ----------
        result : KPIResult
            KPI calculation results containing utilization data.
        output_path : Path
            Path where the chart PNG will be saved.
        """
        if not result.utilization:
            # Create empty chart with message
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.text(0.5, 0.5, 'No workshop utilization data available', ha='center', va='center', fontsize=14)
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')
            plt.tight_layout()
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            plt.close(fig)
            return

        fig, ax = plt.subplots(figsize=(12, 6))

        workshop_ids = [util.workshop_id for util in result.utilization]
        avg_utilization = [util.average_utilization_percent for util in result.utilization]
        peak_utilization = [util.peak_utilization_percent for util in result.utilization]

        x = range(len(workshop_ids))
        width = 0.35

        ax.bar([i - width / 2 for i in x], avg_utilization, width, label='Average', color='#2196F3', alpha=0.8)
        ax.bar([i + width / 2 for i in x], peak_utilization, width, label='Peak', color='#FF9800', alpha=0.8)

        ax.set_ylabel('Utilization (%)')
        ax.set_title('Workshop Utilization')
        ax.set_xticks(x)
        ax.set_xticklabels(workshop_ids)
        ax.legend()
        ax.grid(axis='y', alpha=0.3)
        ax.set_ylim(0, 110)

        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close(fig)

    def generate_timing_chart(self, result: KPIResult, output_path: Path) -> None:
        """Generate bar chart showing average flow and waiting times.

        Parameters
        ----------
        result : KPIResult
            KPI calculation results containing timing data.
        output_path : Path
            Path where the chart PNG will be saved.
        """
        fig, ax = plt.subplots(figsize=(8, 6))

        categories = ['Flow Time', 'Waiting Time']
        values = [result.avg_flow_time_minutes, result.avg_waiting_time_minutes]
        colors = ['#9C27B0', '#FF5722']

        ax.bar(categories, values, color=colors, alpha=0.8)
        ax.set_ylabel('Time (minutes)')
        ax.set_title('Average Wagon Timing')
        ax.grid(axis='y', alpha=0.3)

        # Add value labels on bars
        for i, v in enumerate(values):
            ax.text(i, v + max(values) * 0.02, f'{v:.1f}', ha='center', va='bottom', fontweight='bold')

        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close(fig)

    def generate_all_charts(self, result: KPIResult, output_dir: Path) -> list[Path]:
        """Generate all available charts and save to output directory.

        Parameters
        ----------
        result : KPIResult
            KPI calculation results.
        output_dir : Path
            Directory where charts will be saved.

        Returns
        -------
        list[Path]
            List of paths to generated chart files.
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        chart_paths = []

        throughput_path = output_dir / 'throughput.png'
        self.generate_throughput_chart(result, throughput_path)
        chart_paths.append(throughput_path)

        utilization_path = output_dir / 'utilization.png'
        self.generate_utilization_chart(result, utilization_path)
        chart_paths.append(utilization_path)

        timing_path = output_dir / 'timing.png'
        self.generate_timing_chart(result, timing_path)
        chart_paths.append(timing_path)

        return chart_paths
