"""PopUpSim New Architecture CLI - Bounded contexts implementation."""

from dataclasses import dataclass
import json
import logging
from logging import StreamHandler
from pathlib import Path
import shutil
from typing import TYPE_CHECKING
from typing import Annotated
from typing import Any

from application.simulation_service import SimulationApplicationService
from contexts.configuration.domain.configuration_builder import ConfigurationBuilder
from contexts.external_trains.application.external_trains_context import ExternalTrainsContext
from infrastructure.logging import init_process_logger
from shared.infrastructure.simpy_time_converters import timedelta_to_sim_ticks
import typer

if TYPE_CHECKING:
    from optimizer.search import OptimizationResult

app = typer.Typer(name='popupsim-new', help='PopUpSim New Architecture - Bounded contexts')


@dataclass(frozen=True)
class Contexts:
    """Class containing all contexts."""

    external_trains: ExternalTrainsContext


def print_wagon_metrics(external_trains: ExternalTrainsContext, output_path: Path | None = None) -> None:
    """Print metrics of wagons."""
    ext_metrics = external_trains.get_metrics()
    typer.echo('\nWAGON METRICS:')
    typer.echo(f'  Total wagons arrived:     {ext_metrics.get("total_wagons", 0)}')

    # Read completed count from summary_metrics.json
    if output_path:
        summary_file = output_path / 'summary_metrics.json'
        if summary_file.exists():
            with open(summary_file, encoding='utf-8') as f:
                metrics = json.load(f)
            typer.echo(f'  Total wagons in simulation: {metrics.get("wagons_arrived", 0)}')
            typer.echo(f'  Wagons parked (completed):  {metrics.get("wagons_parked", 0)}')
        else:
            typer.echo(f'  Wagons completed:         {ext_metrics.get("completed_wagons", 0)}')


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


def _print_retrofit_statistics(output_path: Path) -> None:
    """Print statistics for retrofit workflow."""
    summary_file = output_path / 'summary_metrics.json'
    if not summary_file.exists():
        return

    with open(summary_file, encoding='utf-8') as f:
        metrics = json.load(f)

    typer.echo('\nRETROFIT WORKFLOW METRICS:')
    typer.echo(f'  Total wagons in timetable:  {metrics.get("total_wagons", 0)}')
    typer.echo(f'  Wagons eligible for retrofit: {metrics.get("wagons_eligible", 0)}')
    typer.echo(f'  Wagons processable:         {metrics.get("wagons_processable", 0)}')
    typer.echo(f'  Wagons arrived at facility: {metrics.get("wagons_arrived", 0)}')
    typer.echo(f'  Wagons completed (parked):  {metrics.get("wagons_parked", 0)}')
    wagons_in_process = metrics.get('wagons_in_process', 0)
    if wagons_in_process > 0:
        typer.echo(f'  Wagons in process:          {wagons_in_process}')
    typer.echo('\n  REJECTIONS:')
    typer.echo(f'    No retrofit needed:       {metrics.get("rejected_no_retrofit", 0)}')
    typer.echo(f'    Wagon loaded:             {metrics.get("rejected_loaded", 0)}')
    typer.echo(f'    Track full:               {metrics.get("rejected_track_full", 0)}')
    rejected_other = metrics.get('rejected_other', 0)
    if rejected_other > 0:
        typer.echo(f'    Other reasons:            {rejected_other}')
    typer.echo(f'    Total rejected:           {metrics.get("wagons_rejected", 0)}')
    typer.echo(f'\n  Completion rate:            {metrics.get("completion_rate", 0) * 100:.1f}%')
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


def output_visualization(output_path: Path, service: Any) -> None:
    """Write files for visualization onto the disk.

    Args:
        output_path: Path to output directory
        service: Simulation service containing retrofit workflow context
    """
    # Export retrofit workflow events
    retrofit_context = service.contexts.get('retrofit_workflow')
    if retrofit_context and hasattr(retrofit_context, 'export_events'):
        retrofit_context.export_events(str(output_path))
        typer.echo('\nRetrofit workflow data exported:')
        typer.echo('  - wagon_journey.csv')
        typer.echo('  - rejected_wagons.csv')
        typer.echo('  - locomotive_movements.csv')
        typer.echo('  - summary_metrics.json')
        typer.echo('\nDual-stream event files (new):')
        typer.echo('  - resource_states.csv (state changes)')
        typer.echo('  - resource_locations.csv (location tracking)')
        typer.echo('  - resource_processes.csv (process events)')
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
    typer.echo(f'  Trains: {len(scenario.trains or [])}')
    typer.echo(f'  Total wagons: {sum(len(t.wagons) for t in (scenario.trains or []))}')

    service = SimulationApplicationService(scenario, output_path)
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

    typer.echo('\nGenerating outputs...')
    output_visualization(output_path, service)

    typer.echo('\n' + '=' * 60)
    typer.echo('SIMULATION STATISTICS')
    typer.echo('=' * 60)

    _print_retrofit_statistics(output_path)

    typer.echo(f'\nSIMULATION TIME:            {result.duration:.1f} minutes')
    typer.echo('=' * 60)


@app.command()
# Each parameter below is a distinct CLI option, so the argument count is intentional.
def optimize(  # noqa: PLR0913  # pylint: disable=too-many-arguments,too-many-positional-arguments
    scenario_folder_path: Annotated[Path, typer.Option('--scenario', help='Path to scenario directory')],
    seed: Annotated[int, typer.Option('--seed', help='Random seed')] = 42,
    n_random: Annotated[int, typer.Option('--n-random', help='Number of random samples')] = 500,
    n_workers: Annotated[int, typer.Option('--n-workers', help='Number of parallel workers')] = 10,
    k_starts: Annotated[int, typer.Option('--k-starts', help='Number of top elites to start Phase 2 descent from')] = 5,
    max_rounds: Annotated[int, typer.Option('--max-rounds', help='Maximum rounds of coordinate descent')] = 5,
    weight_completion: Annotated[
        float, typer.Option('--weight-completion', help='Weight for completion rate in score calculation')
    ] = 0.9,
    weight_loco: Annotated[
        float, typer.Option('--weight-loco', help='Weight for locomotive utilization in score calculation')
    ] = -0.1,
    results_json: Annotated[Path, typer.Option('--results-json', help='Path to output JSON file')] = Path(
        'optimization_results.json'
    ),
) -> None:
    """Load and optimize a scenario using a two-phase adaptive coordinate search."""
    # Imported here to avoid a circular import: optimizer.harness imports `run`
    # from this module, so importing optimizer.search at module load would be cyclic.
    from optimizer.search import SearchConfig  # pylint: disable=import-outside-toplevel
    from optimizer.search import optimize_scenario  # pylint: disable=import-outside-toplevel
    from optimizer.search import write_results  # pylint: disable=import-outside-toplevel

    config = SearchConfig(
        seed=seed,
        n_random=n_random,
        k_starts=k_starts,
        max_rounds=max_rounds,
        weight_completion=weight_completion,
        weight_loco=weight_loco,
        n_workers=n_workers,
    )

    typer.echo('Running two-phase optimization (random search + coordinate descent)...')
    result = optimize_scenario(scenario_folder_path, config)

    write_results(result, results_json)
    _print_optimization_summary(result, len(result.records))


def _format_diff(value: float, initial_value: float, is_pct: bool = False) -> str:
    """Format the signed difference of ``value`` from ``initial_value`` for display."""
    diff = value - initial_value
    if abs(diff) < 1e-9:
        diff = 0.0
    sign = '+' if diff >= 0 else ''
    if is_pct:
        return f' ({sign}{diff:.2f}%)'
    return f' ({sign}{diff:.4f})'


def _print_optimization_summary(result: 'OptimizationResult', total_evaluated: int) -> None:
    """Print the initial configuration and the top optimized configurations."""
    initial = result.initial
    ranked = result.ranked()

    typer.echo('\n' + '=' * 60)
    typer.echo(f'OPTIMIZATION COMPLETE (Total unique configurations evaluated: {total_evaluated})')
    typer.echo('=' * 60)

    typer.echo('\nInitial Configuration:')
    typer.echo(
        f'  Score = {initial.score:.4f} | '
        f'Completion Rate = {initial.completion_rate_pct:.2f}% | '
        f'Loco Utilization = {initial.loco_utilization_pct:.2f}%'
    )

    typer.echo('\nTop 5 Overall Optimized Configurations:')
    for rank, record in enumerate(ranked[:5], start=1):
        score_diff = _format_diff(record.score, initial.score)
        comp_diff = _format_diff(record.completion_rate_pct, initial.completion_rate_pct, is_pct=True)
        loco_diff = _format_diff(record.loco_utilization_pct, initial.loco_utilization_pct, is_pct=True)
        typer.echo(
            f'  Rank {rank}: Score = {record.score:.4f}{score_diff} | '
            f'Completion Rate = {record.completion_rate_pct:.2f}%{comp_diff} | '
            f'Loco Utilization = {record.loco_utilization_pct:.2f}%{loco_diff}'
        )


if __name__ == '__main__':
    app()
