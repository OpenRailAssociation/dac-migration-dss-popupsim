# ADR-009: Matplotlib for Visualization

**Status:** IMPLEMENTED - 2025-01-15

## Context

Need visualization for simulation results. Full version will have web interface, but MVP needs simple charts.

## Decision

Use **Matplotlib** for generating static charts (PNG files).

## Rationale

- **Simple**: Easy to use, well-known library
- **Offline**: No web server required
- **Sufficient**: Meets MVP visualization needs
- **Python native**: Integrated in Python ecosystem
- **No frontend developer**: Backend team can handle it
- **Fast development**: Quick to implement basic charts

## Alternatives Considered

- **Matplotlib** ✅ Chosen
- **Plotly**: Interactive but requires web server
- **Bokeh**: Overkill for static charts
- **Seaborn**: Built on Matplotlib, no significant advantage
- **Custom web charts**: Requires frontend development

## Implementation in MVP

### Visualization Components
```python
# analytics/infrastructure/visualization/visualizer.py
class Visualizer:
    def create_throughput_chart(self, kpis: ThroughputKPI) -> Path:
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.bar(['Wagons/Hour', 'Total Processed'], 
               [kpis.wagons_per_hour, kpis.total_wagons])
        plt.savefig('throughput_chart.png')
        return Path('throughput_chart.png')
    
    def create_gantt_chart(self, events: list[Event]) -> Path:
        # Generate Gantt chart for locomotive and wagon activities
        return self._create_gantt_visualization(events)
```

### Chart Types Generated
- **Throughput Charts**: Wagons per hour, total processed
- **Utilization Charts**: Workshop station usage over time
- **Gantt Charts**: Locomotive and wagon activity timelines
- **Bottleneck Analysis**: Resource utilization heatmaps

## Consequences

### Achieved
- ✅ **Fast Implementation**: Charts generated in <1 second
- ✅ **No Web Complexity**: Offline PNG files, no server required
- ✅ **Professional Output**: Publication-ready charts for reports
- ✅ **Multiple Chart Types**: Comprehensive visualization suite
- ✅ **Export Ready**: PNG files easy to include in presentations

### Files Implementing This Decision
- `analytics/infrastructure/visualization/visualizer.py` - Chart generation
- `analytics/application/services/visualization_service.py` - Visualization orchestration