"""PopUpSim MVP CLI - Stable MVP implementation."""

import asyncio
from pathlib import Path
from typing import Annotated

import typer
from analytics.application.async_analytics_service import AsyncAnalyticsService
from analytics.domain.models.simulation_data import ContextData, SimulationData
from analytics.infrastructure.exporters.csv_exporter import CSVExporter
from analytics.infrastructure.visualization.matplotlib_visualizer import Visualizer
from configuration.application.scenario_builder import ScenarioBuilder
from simulation.application.simulation_orchestrator import SimulationOrchestrator
from simulation.infrastructure.engines.simpy_engine_adapter import SimPyEngineAdapter
from workshop_operations.application.workshop_context import WorkshopOperationsContext

app = typer.Typer(name="popupsim-mvp", help="PopUpSim MVP - Stable implementation")


@app.command()
def run(
    scenario_path: Annotated[
        Path, typer.Option("--scenario", help="Path to scenario file")
    ],
    output_path: Annotated[Path, typer.Option("--output", help="Output directory")],
    verbose: Annotated[bool, typer.Option("--verbose", help="Verbose output")] = False,
) -> None:
    """Run PopUpSim MVP simulation."""

    if verbose:
        typer.echo(f"Loading scenario: {scenario_path}")

    # Load scenario
    scenario = ScenarioBuilder(scenario_path).build()

    if verbose:
        typer.echo(f"Scenario: {scenario.id} ({len(scenario.trains)} trains)")

    # Run MVP simulation
    engine = SimPyEngineAdapter.create()
    workshop_context = WorkshopOperationsContext(scenario)
    orchestrator = SimulationOrchestrator(engine, scenario)
    orchestrator.register_context(workshop_context)

    until = (scenario.end_date - scenario.start_date).total_seconds() / 60.0
    typer.echo("Running MVP simulation...")
    results = orchestrator.run(until=until)

    # Calculate KPIs
    typer.echo("Calculating KPIs...")
    analytics_service = AsyncAnalyticsService()
    simulation_data = SimulationData(
        metrics=results or {},
        scenario=scenario,
        wagons=workshop_context.wagons,
        rejected_wagons=workshop_context.rejected_wagons,
        workshops=workshop_context.workshops,
    )
    context_data = ContextData(
        popup_context=workshop_context.popup_retrofit,
        yard_context=workshop_context.yard_operations,
        shunting_context=workshop_context.shunting_operations,
    )
    kpi_result = asyncio.run(
        analytics_service.calculate_kpis_async(simulation_data, context_data)
    )

    # Export results
    output_path.mkdir(parents=True, exist_ok=True)
    csv_exporter = CSVExporter()
    visualizer = Visualizer()

    csv_files = csv_exporter.export_all(kpi_result, output_path)
    chart_paths = visualizer.generate_all_charts(kpi_result, output_path)

    typer.echo(f"✅ MVP simulation completed!")
    typer.echo(f"📊 Results saved to: {output_path}")
    typer.echo(f"🚂 Wagons processed: {kpi_result.throughput.total_wagons_retrofitted}")


if __name__ == "__main__":
    app()
