"""PopUpSim New Architecture CLI - Bounded contexts implementation."""

from dataclasses import dataclass
import json
import logging
from logging import StreamHandler
from pathlib import Path
import shutil
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
from shared.infrastructure.simpy_time_converters import timedelta_to_sim_ticks
import typer

app = typer.Typer(name='popupsim-new', help='PopUpSim New Architecture - Bounded contexts')


@dataclass(frozen=True)
class Contexts:
    """Class containing all contexts."""

    analytics: AnalyticsContext
    external_trains: ExternalTrainsContext
    yard: YardOperationsContext | None
    popup_workshop: PopUpRetrofitContext | None
    shunting: ShuntingOperationsContext | None


def print_wagon_metrics(
    external_trains: ExternalTrainsContext, is_legacy: bool, output_path: Path | None = None
) -> None:
    """Print metrics of wagons."""
    ext_metrics = external_trains.get_metrics()
    typer.echo('\nWAGON METRICS:')
    typer.echo(f'  Total wagons arrived:     {ext_metrics.get("total_wagons", 0)}')

    # For retrofit workflow, read completed count from summary_metrics.json
    if not is_legacy and output_path:
        summary_file = output_path / 'summary_metrics.json'
        if summary_file.exists():
            with open(summary_file, encoding='utf-8') as f:
                metrics = json.load(f)
            # Show actual arrived count from JSON, not external_trains
            typer.echo(f'  Total wagons in simulation: {metrics.get("wagons_arrived", 0)}')
            typer.echo(f'  Wagons parked (completed):  {metrics.get("wagons_parked", 0)}')
        else:
            typer.echo(f'  Wagons completed:         {ext_metrics.get("completed_wagons", 0)}')
    else:
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


def _setup_directories(scenario_path: Path, output_path: Path) -> None:
    """Setup output directories and copy scenario."""
    output_path.mkdir(parents=True, exist_ok=True)
    scenario_output = output_path / 'scenario'
    if scenario_output.exists():
        shutil.rmtree(scenario_output)
    shutil.copytree(scenario_path, scenario_output)


def _configure_logging(output_path: Path) -> None:
    """Configure logging handlers."""
    event_handler = configure_event_logging(output_path)
    console_handler = configure_console_logging()
    logging.basicConfig(level=logging.INFO, handlers=[event_handler, console_handler])
    init_process_logger(output_path)


def _print_legacy_statistics(contexts: Contexts) -> None:
    """Print statistics for legacy architecture."""
    print_popup_workshop_metrics(contexts.popup_workshop)  # type: ignore[arg-type]
    print_yard_metrics(contexts.yard)  # type: ignore[arg-type]
    print_shunting_metrics(contexts.shunting)  # type: ignore[arg-type]


def _print_retrofit_statistics(output_path: Path) -> None:
    """Print statistics for retrofit workflow."""
    summary_file = output_path / 'summary_metrics.json'
    if not summary_file.exists():
        return

    with open(summary_file, encoding='utf-8') as f:
        metrics = json.load(f)

    typer.echo('\nRETROFIT WORKFLOW METRICS:')
    typer.echo(f'  Total wagons arrived:       {metrics.get("wagons_arrived", 0)}')
    typer.echo(f'  Total wagons rejected:      {metrics.get("wagons_rejected", 0)}')
    typer.echo(f'  Total wagons completed:     {metrics.get("wagons_parked", 0)}')
    wagons_in_process = metrics.get('wagons_in_process', 0)
    if wagons_in_process > 0:
        typer.echo(f'  Total wagons in process:    {wagons_in_process}')
    typer.echo(f'  Completion rate:            {metrics.get("completion_rate", 0) * 100:.1f}%')
    typer.echo(f'  Throughput (wagons/hour):   {metrics.get("throughput_rate_per_hour", 0):.2f}')

    ws_stats = metrics.get('workshop_statistics', {})
    if ws_stats:
        typer.echo('\nWORKSHOP METRICS:')
        typer.echo(f'  Total workshops:            {ws_stats.get("total_workshops", 0)}')
        typer.echo(f'  Total wagons processed:     {ws_stats.get("total_wagons_processed", 0)}')
        typer.echo(f'  Workshop utilization:       {metrics.get("workshop_utilization", 0):.1f}%')
        workshops = ws_stats.get('workshops', {})
        if workshops:
            typer.echo('  Per-workshop breakdown:')
            for ws_id, ws_data in sorted(workshops.items()):
                typer.echo(f'    {ws_id}: {ws_data.get("wagons_processed", 0)} wagons')

    loco_stats = metrics.get('locomotive_statistics', {})
    if loco_stats:
        typer.echo('\nLOCOMOTIVE METRICS:')
        typer.echo(f'  Allocations:                {loco_stats.get("allocations", 0)}')
        typer.echo(f'  Movements:                  {loco_stats.get("movements", 0)}')
        typer.echo(f'  Total operations:           {loco_stats.get("total_operations", 0)}')

    rejection_breakdown = metrics.get('rejection_breakdown', {})
    if rejection_breakdown:
        typer.echo('\nREJECTION BREAKDOWN:')
        for reason, count in rejection_breakdown.items():
            typer.echo(f'  {reason}: {count}')


def output_visualization(contexts: Contexts, output_path: Path, is_legacy: bool, service: Any = None) -> None:
    """Write files for visualization onto the disk."""
    if is_legacy:
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
            'popup': (contexts.popup_workshop.get_metrics() if contexts.popup_workshop else {}),  # type: ignore[union-attr]  # pylint: disable=line-too-long
            'yard': contexts.yard.get_metrics() if contexts.yard else {},  # type: ignore[union-attr]
            'shunting': (contexts.shunting.get_metrics() if contexts.shunting else {}),  # type: ignore[union-attr]
        }
        charts = contexts.analytics.visualizer.generate_all_charts(contexts.analytics, output_path, context_metrics)
        typer.echo('\nVisualizations generated:')
        for chart in charts:
            typer.echo(f'  - {chart.name}')
    else:
        # Export retrofit workflow events
        retrofit_context = service.contexts.get('retrofit_workflow')
        if retrofit_context and hasattr(retrofit_context, 'export_events'):
            retrofit_context.export_events(str(output_path))
            typer.echo('\nRetrofit workflow data exported:')
            typer.echo('  - wagon_journey.csv')
            typer.echo('  - rejected_wagons.csv')
            typer.echo('  - locomotive_movements.csv')
            typer.echo('  - summary_metrics.json')
        else:
            typer.echo('\nRetrofit workflow output generation not available')


@app.command()
def run(
    scenario_path: Annotated[Path, typer.Option('--scenario', help='Path to scenario file')],
    output_path: Annotated[Path, typer.Option('--output', help='Output directory')] = Path('./output'),
    verbose: Annotated[bool, typer.Option('--verbose', help='Verbose output')] = False,
) -> None:
    """Run PopUpSim with new bounded contexts architecture."""
    # Setup
    _setup_directories(scenario_path, output_path)
    _configure_logging(output_path)

    if verbose:
        typer.echo(f'Loading scenario: {scenario_path}')

    # Load and run simulation
    scenario = ConfigurationBuilder(scenario_path).build()
    typer.echo(f'Loaded scenario: {scenario.id}')
    typer.echo(f'  Trains: {len(scenario.trains)}')
    typer.echo(f'  Total wagons: {sum(len(t.wagons) for t in scenario.trains)}')

    service = SimulationApplicationService(scenario)
    until = timedelta_to_sim_ticks(scenario.end_date - scenario.start_date)
    typer.echo('Running simulation...\n')
    result = service.execute(until)

    if not result.success:
        typer.echo('\nSIMULATION FAILED')
        raise typer.Exit(1)

    # Success - generate outputs and print statistics
    typer.echo('\n' + '=' * 60)
    typer.echo('SIMULATION COMPLETED SUCCESSFULLY')
    typer.echo('=' * 60)

    contexts = Contexts(
        analytics=service.context_registry.contexts.get('analytics'),  # type: ignore[arg-type]
        external_trains=service.context_registry.contexts.get('external_trains'),  # type: ignore[arg-type]
        yard=service.context_registry.contexts.get('yard'),  # type: ignore[arg-type]
        popup_workshop=service.context_registry.contexts.get('popup'),  # type: ignore[arg-type]
        shunting=service.context_registry.contexts.get('shunting'),  # type: ignore[arg-type]
    )

    typer.echo('\nGenerating outputs...')
    is_legacy = contexts.yard is not None
    output_visualization(contexts, output_path, is_legacy, service)

    typer.echo('\n' + '=' * 60)
    typer.echo('SIMULATION STATISTICS')
    typer.echo('=' * 60)

    if is_legacy:
        print_wagon_metrics(contexts.external_trains, is_legacy, output_path)
        _print_legacy_statistics(contexts)
    else:
        _print_retrofit_statistics(output_path)

    typer.echo(f'\nSIMULATION TIME:            {result.duration:.1f} minutes')
    typer.echo('=' * 60)


if __name__ == '__main__':
    app()
