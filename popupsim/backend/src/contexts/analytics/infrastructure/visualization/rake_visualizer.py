"""Rake visualization for analytics dashboard."""

from contexts.analytics.domain.services.rake_analytics_service import RakeAnalyticsService
from matplotlib import patches
import matplotlib.pyplot as plt


class RakeVisualizer:
    """Visualizer for rake formations and movements."""

    def __init__(self, analytics_service: RakeAnalyticsService) -> None:
        self.analytics_service = analytics_service

    def plot_rake_formations_timeline(self, save_path: str | None = None) -> None:
        """Plot rake formations over time."""
        formations = self.analytics_service.get_rake_formations_by_time()

        if not formations:
            return

        _fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

        # Plot 1: Rake formations over time
        times = [f.timestamp for f in formations]
        sizes = [f.wagon_count for f in formations]
        strategies = [f.formation_strategy for f in formations]

        # Color by strategy
        strategy_colors = {
            'workshop_capacity': 'blue',
            'fixed_size': 'red',
            'track_capacity': 'green',
        }
        colors = [strategy_colors.get(s, 'gray') for s in strategies]

        ax1.scatter(times, sizes, c=colors, alpha=0.7, s=60)
        ax1.set_xlabel('Time (minutes)')
        ax1.set_ylabel('Rake Size (wagons)')
        ax1.set_title('Rake Formations Over Time')
        ax1.grid(True, alpha=0.3)

        # Add legend
        for strategy, color in strategy_colors.items():
            ax1.scatter([], [], c=color, label=strategy, s=60)
        ax1.legend()

        # Plot 2: Cumulative wagons in rakes
        cumulative_wagons = []
        total = 0
        for formation in formations:
            total += formation.wagon_count
            cumulative_wagons.append(total)

        ax2.plot(times, cumulative_wagons, 'b-', linewidth=2)
        ax2.set_xlabel('Time (minutes)')
        ax2.set_ylabel('Cumulative Wagons in Rakes')
        ax2.set_title('Cumulative Wagon Processing')
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        else:
            plt.show()

    def plot_track_occupancy(self, tracks: list[str], save_path: str | None = None) -> None:
        """Plot track occupancy over time."""
        _fig, ax = plt.subplots(figsize=(12, 6))

        colors = ['blue', 'red', 'green', 'orange', 'purple']

        for i, track in enumerate(tracks):
            occupancy_data = self.analytics_service.get_track_occupancy_timeline(track)
            if occupancy_data:
                times, counts = zip(*occupancy_data, strict=False)
                color = colors[i % len(colors)]
                ax.step(times, counts, where='post', label=track, color=color, linewidth=2)

        ax.set_xlabel('Time (minutes)')
        ax.set_ylabel('Wagon Count')
        ax.set_title('Track Occupancy Over Time')
        ax.legend()
        ax.grid(True, alpha=0.3)

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        else:
            plt.show()

    def plot_rake_gantt_chart(self, save_path: str | None = None) -> None:
        """Plot Gantt chart showing rake lifecycles."""
        snapshots = self.analytics_service.rake_snapshots

        if not snapshots:
            return

        # Group by rake_id
        rake_timelines = {}
        for snapshot in snapshots:
            if snapshot.rake_id not in rake_timelines:
                rake_timelines[snapshot.rake_id] = []
            rake_timelines[snapshot.rake_id].append(snapshot)

        _fig, ax = plt.subplots(figsize=(14, max(6, len(rake_timelines) * 0.5)))

        rake_labels = []
        status_colors = {
            'formed': 'lightblue',
            'transporting': 'yellow',
            'processing': 'orange',
            'completed': 'lightgreen',
        }

        for y_pos, rake_id, timeline in enumerate(rake_timelines.items()):
            timeline.sort(key=lambda x: x.timestamp)
            rake_labels.append(f'{rake_id} ({timeline[0].wagon_count}w)')

            for i in range(len(timeline) - 1):
                start_time = timeline[i].timestamp
                end_time = timeline[i + 1].timestamp
                status = timeline[i].status

                color = status_colors.get(status, 'gray')
                rect = patches.Rectangle(
                    (start_time, y_pos - 0.4),
                    end_time - start_time,
                    0.8,
                    facecolor=color,
                    edgecolor='black',
                    alpha=0.7,
                )
                ax.add_patch(rect)

        ax.set_xlim(0, max(s.timestamp for s in snapshots) * 1.1)
        ax.set_ylim(-0.5, len(rake_timelines) - 0.5)
        ax.set_xlabel('Time (minutes)')
        ax.set_ylabel('Rakes')
        ax.set_title('Rake Lifecycle Gantt Chart')
        ax.set_yticks(range(len(rake_labels)))
        ax.set_yticklabels(rake_labels)
        ax.grid(True, alpha=0.3, axis='x')

        # Add legend
        for status, color in status_colors.items():
            ax.add_patch(patches.Rectangle((0, 0), 0, 0, facecolor=color, label=status))
        ax.legend(loc='upper right')

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        else:
            plt.show()

    def plot_rake_size_distribution(self, save_path: str | None = None) -> None:
        """Plot distribution of rake sizes."""
        size_dist = self.analytics_service.get_rake_size_distribution()

        if not size_dist:
            return

        _fig, ax = plt.subplots(figsize=(10, 6))

        sizes = list(size_dist.keys())
        counts = list(size_dist.values())

        bars = ax.bar(sizes, counts, alpha=0.7, color='skyblue', edgecolor='navy')

        # Add value labels on bars
        for bar, count in zip(bars, counts, strict=False):
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                height + 0.1,
                f'{count}',
                ha='center',
                va='bottom',
            )

        ax.set_xlabel('Rake Size (wagons)')
        ax.set_ylabel('Number of Rakes')
        ax.set_title('Distribution of Rake Sizes')
        ax.grid(True, alpha=0.3, axis='y')

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        else:
            plt.show()

    def create_rake_dashboard(self, tracks: list[str], save_path: str | None = None) -> None:
        """Create comprehensive rake analytics dashboard."""
        fig = plt.figure(figsize=(16, 12))

        # Layout: 2x2 grid
        gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3)

        # 1. Rake formations timeline
        ax1 = fig.add_subplot(gs[0, 0])
        formations = self.analytics_service.get_rake_formations_by_time()
        if formations:
            times = [f.timestamp for f in formations]
            sizes = [f.wagon_count for f in formations]
            ax1.scatter(times, sizes, alpha=0.7, s=60, color='blue')
            ax1.set_xlabel('Time (minutes)')
            ax1.set_ylabel('Rake Size')
            ax1.set_title('Rake Formations')
            ax1.grid(True, alpha=0.3)

        # 2. Track occupancy
        ax2 = fig.add_subplot(gs[0, 1])
        colors = ['blue', 'red', 'green', 'orange']
        for i, track in enumerate(tracks[:4]):  # Limit to 4 tracks
            occupancy_data = self.analytics_service.get_track_occupancy_timeline(track)
            if occupancy_data:
                times, counts = zip(*occupancy_data, strict=False)
                ax2.step(
                    times,
                    counts,
                    where='post',
                    label=track,
                    color=colors[i % len(colors)],
                    linewidth=2,
                )
        ax2.set_xlabel('Time (minutes)')
        ax2.set_ylabel('Wagon Count')
        ax2.set_title('Track Occupancy')
        ax2.legend()
        ax2.grid(True, alpha=0.3)

        # 3. Rake size distribution
        ax3 = fig.add_subplot(gs[1, 0])
        size_dist = self.analytics_service.get_rake_size_distribution()
        if size_dist:
            sizes = list(size_dist.keys())
            counts = list(size_dist.values())
            ax3.bar(sizes, counts, alpha=0.7, color='skyblue')
            ax3.set_xlabel('Rake Size')
            ax3.set_ylabel('Count')
            ax3.set_title('Rake Size Distribution')
            ax3.grid(True, alpha=0.3, axis='y')

        # 4. Strategy statistics
        ax4 = fig.add_subplot(gs[1, 1])
        strategy_stats = self.analytics_service.get_formation_strategy_stats()
        if strategy_stats:
            strategies = list(strategy_stats.keys())
            avg_sizes = [stats['avg_size'] for stats in strategy_stats.values()]
            ax4.bar(strategies, avg_sizes, alpha=0.7, color='lightcoral')
            ax4.set_xlabel('Formation Strategy')
            ax4.set_ylabel('Average Rake Size')
            ax4.set_title('Strategy Performance')
            ax4.grid(True, alpha=0.3, axis='y')
            plt.setp(ax4.get_xticklabels(), rotation=45, ha='right')

        plt.suptitle('Rake Analytics Dashboard', fontsize=16, fontweight='bold')

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        else:
            plt.show()
