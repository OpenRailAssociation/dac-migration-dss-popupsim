"""PopUpSim New Architecture CLI - Bounded contexts implementation."""

from dataclasses import dataclass
import logging
from logging import StreamHandler
from pathlib import Path
from typing import Annotated
from typing import Any

from application.simulation_service import SimulationApplicationService
from contexts.analytics.application.analytics_context import AnalyticsContext
from contexts.configuration.domain.configuration_builder import ConfigurationBuilder
from contexts.external_trains.application.external_trains_context import ExternalTrainsContext
from contexts.popup_retrofit.application.popup_context import PopUpRetrofitContext
from contexts.shunting_operations.application.shunting_context import ShuntingOperationsContext
from contexts.yard_operations.application.yard_context import YardOperationsContext
from infrastructure.logging import init_process_logger
import typer

app = typer.Typer(name='popupsim-new', help='PopUpSim New Architecture - Bounded contexts')


@dataclass(frozen=True)
class Contexts:
    """Class containing all contexts."""

    analytics: AnalyticsContext
    external_trains: ExternalTrainsContext
    yard: YardOperationsContext
    popup_workshop: PopUpRetrofitContext
    shunting: ShuntingOperationsContext


def print_wagon_metrics(external_trains: ExternalTrainsContext) -> None:
    """Print metrics of wagons."""
    ext_metrics = external_trains.get_metrics()
    typer.echo('\nWAGON METRICS:')
    typer.echo(f'  Total wagons arrived:     {ext_metrics.get("total_wagons", 0)}')
    typer.echo(f'  Wagons completed:         {ext_metrics.get("completed_wagons", 0)}')


def print_popup_workshop_metrics(popup: PopUpRetrofitContext) -> None:
    """Print metrics of popup workshop."""
    popup_metrics = popup.get_metrics()
    typer.echo('\nWORKSHOP METRICS:')
    typer.echo(f'  Workshops:                {popup_metrics.get("workshops", 0)}')
    typer.echo(f'  Total retrofit bays:      {popup_metrics.get("total_bays", 0)}')
    typer.echo(f'  Overall utilization:      {popup_metrics.get("utilization_percentage", 0):.1f}%')
    per_workshop = popup_metrics.get('per_workshop_utilization', {})
    # Filter out track-based workshop entries
    filtered_workshops = {k: v for k, v in per_workshop.items() if not k.startswith('track_')}
    for workshop_id, util in sorted(filtered_workshops.items()):
        typer.echo(f'    {workshop_id}:             {util:.1f}%')
    per_bay = popup_metrics.get('per_bay_utilization', {})
    typer.echo('  Bay utilization:')
    for bay_id, util in sorted(per_bay.items()):
        typer.echo(f'    {bay_id}:    {util:.1f}%')


def print_yard_metrics(yard: YardOperationsContext) -> None:
    """Print metrics of Yard context."""
    yard_metrics = yard.get_metrics()
    typer.echo('\nYARD METRICS:')
    typer.echo(f'  Wagons classified:        {yard_metrics.get("classified_wagons", 0)}')
    typer.echo(f'  Wagons rejected:          {yard_metrics.get("rejected_wagons", 0)}')
    typer.echo(f'  Wagons parked:            {yard_metrics.get("wagons_parked", 0)}')
    typer.echo(f'  Wagons on collection:     {yard_metrics.get("wagons_on_collection", 0)}')
    typer.echo(f'  Wagons on retrofit:       {yard_metrics.get("wagons_on_retrofit", 0)}')
    typer.echo(f'  Wagons on retrofitted:    {yard_metrics.get("wagons_on_retrofitted", 0)}')
    track_util = yard_metrics.get('track_utilization', {})
    typer.echo('  Track utilization:')
    for track_id, util in sorted(track_util.items()):
        typer.echo(f'    {track_id}:          {util:.1f}%')


def print_shunting_metrics(shunting: ShuntingOperationsContext) -> None:
    """Print metrics of shunting context."""
    shunt_metrics = shunting.get_metrics()
    typer.echo('\nSHUNTING METRICS:')
    typer.echo(f'  Total locomotives:        {shunt_metrics.get("total_locomotives", 0)}')
    typer.echo(f'  Locomotive utilization:   {shunt_metrics.get("utilization_percentage", 0):.1f}%')
    breakdown = shunt_metrics.get('utilization_breakdown', {})
    typer.echo('  Utilization breakdown:')
    for status, pct in sorted(breakdown.items()):
        typer.echo(f'    {status}:          {pct:.1f}%')
    per_loco = shunt_metrics.get('per_locomotive_breakdown', {})
    typer.echo('  Per-locomotive breakdown:')
    for loco_id, loco_breakdown in sorted(per_loco.items()):
        typer.echo(f'    {loco_id}:')
        for status, pct in sorted(loco_breakdown.items()):
            typer.echo(f'      {status}:      {pct:.1f}%')


def configure_event_logging(output_path: Path) -> Any:
    """Configure the event logging."""
    event_handler = logging.FileHandler(output_path / 'events.log', mode='w', encoding='utf-8')
    event_handler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)-8s | %(message)s', datefmt='%H:%M:%S'))
    event_handler.setLevel(logging.INFO)
    return event_handler


def configure_console_logging() -> StreamHandler:
    """Configure the console logging."""
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)-8s | %(message)s', datefmt='%H:%M:%S'))
    console_handler.setLevel(logging.ERROR)

    return console_handler


def output_visualization(contexts: Contexts, output_path: Path) -> None:
    """Write files for visualization onto the disk."""
    dashboard_files = contexts.analytics.export_dashboard_data(
        output_dir=output_path,
        yard_context=contexts.yard,
        popup_context=contexts.popup_workshop,
        shunting_context=contexts.shunting,
    )

    typer.echo('\nDashboard data exported:')
    for file_type, file_path in dashboard_files.items():
        typer.echo(f'  - {file_type}: {file_path.name}')

    # Generate visualizations
    context_metrics = {
        'external_trains': contexts.external_trains.get_metrics(),
        'popup': contexts.popup_workshop.get_metrics(),
        'yard': contexts.yard.get_metrics(),
        'shunting': contexts.shunting.get_metrics(),
    }
    charts = contexts.analytics.visualizer.generate_all_charts(contexts.analytics, output_path, context_metrics)
    typer.echo('\nVisualizations generated:')
    for chart in charts:
        typer.echo(f'  - {chart.name}')


@app.command()
def run(
    scenario_path: Annotated[Path, typer.Option('--scenario', help='Path to scenario file')],
    output_path: Annotated[Path, typer.Option('--output', help='Output directory')] = Path('./output'),
    verbose: Annotated[bool, typer.Option('--verbose', help='Verbose output')] = False,
) -> None:
    """Run PopUpSim with new bounded contexts architecture."""
    # Create output directory
    output_path.mkdir(parents=True, exist_ok=True)

    # Configure event logging to file with UTF-8 encoding (always INFO level)
    event_handler = configure_event_logging(output_path)
    console_handler = configure_console_logging()

    logging.basicConfig(
        level=logging.INFO,
        handlers=[event_handler, console_handler],
    )

    # Initialize process logger
    init_process_logger(output_path)

    if verbose:
        typer.echo(f'Loading scenario: {scenario_path}')

    # Load scenario
    scenario = ConfigurationBuilder(scenario_path).build()

    typer.echo(f'Loaded scenario: {scenario.id}')
    typer.echo(f'  Trains: {len(scenario.trains)}')
    typer.echo(f'  Total wagons: {sum(len(t.wagons) for t in scenario.trains)}')

    service = SimulationApplicationService(scenario)
    until = (scenario.end_date - scenario.start_date).total_seconds() / 60.0

    typer.echo('Running simulation...\n')
    result = service.execute(until)

    if result.success:
        typer.echo('\n' + '=' * 60)
        typer.echo('SIMULATION COMPLETED SUCCESSFULLY')
        typer.echo('=' * 60)

        # Get metrics from contexts
        contexts = Contexts(
            analytics=service.context_registry.contexts.get('analytics'),  # type: ignore[arg-type]
            external_trains=service.context_registry.contexts.get('external_trains'),  # type: ignore[arg-type]
            yard=service.context_registry.contexts.get('yard'),  # type: ignore[arg-type]
            popup_workshop=service.context_registry.contexts.get('popup'),  # type: ignore[arg-type]
            shunting=service.context_registry.contexts.get('shunting'),  # type: ignore[arg-type]
        )

        # Generate outputs
        typer.echo('\nGenerating outputs...')
        output_visualization(contexts, output_path)

        typer.echo('\n' + '=' * 60)
        typer.echo('SIMULATION STATISTICS')
        typer.echo('=' * 60)
        print_wagon_metrics(contexts.external_trains)
        print_popup_workshop_metrics(contexts.popup_workshop)
        print_yard_metrics(contexts.yard)
        print_shunting_metrics(contexts.shunting)
        typer.echo(f'\nSIMULATION TIME:            {result.duration:.1f} minutes')
        typer.echo('=' * 60)
    else:
        typer.echo('\nSIMULATION FAILED')
        raise typer.Exit(1)


if __name__ == '__main__':
    app()
