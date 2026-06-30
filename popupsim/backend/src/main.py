"""PopUpSim New Architecture CLI - Bounded contexts implementation."""

from dataclasses import dataclass
import json
import logging
from logging import StreamHandler
import os
from pathlib import Path
import shutil
from typing import Annotated
from typing import Any

from application.simulation_service import SimulationApplicationService
from contexts.configuration.domain.configuration_builder import ConfigurationBuilder
from contexts.configuration.domain.models.scenario import Scenario
from contexts.external_trains.application.external_trains_context import ExternalTrainsContext
from infrastructure.logging import init_process_logger
from shared.infrastructure.simpy_time_converters import timedelta_to_sim_ticks
import typer

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
def optimize(
    scenario_folder_path: Annotated[Path, typer.Option('--scenario', help='Path to scenario directory')],
    seed: Annotated[int, typer.Option('--seed', help='Random seed')] = 42,
    n_random: Annotated[int, typer.Option('--n-random', help='Number of random samples')] = 500,
    n_workers: Annotated[int, typer.Option('--n-workers', help='Number of parallel workers')] = 10,
    k_starts: Annotated[int, typer.Option('--k-starts', help='Number of top elites to start Phase 2 descent from')] = 5,
    max_rounds: Annotated[int, typer.Option('--max-rounds', help='Maximum rounds of coordinate descent')] = 5,
    weight_completion: Annotated[float, typer.Option('--weight-completion', help='Weight for completion rate in score calculation')] = 0.9,
    weight_loco: Annotated[float, typer.Option('--weight-loco', help='Weight for locomotive utilization in score calculation')] = -0.1,
    results_json: Annotated[Path, typer.Option('--results-json', help='Path to output JSON file')] = Path('optimization_results.json'),
) -> None:
    """Load and optimize a scenario using a two-phase adaptive coordinate search."""
    import random
    import copy
    import json
    from tqdm import trange
    from optimizer.harness import run_simulation, run_parallel
    from optimizer.problem_space import parameter_config
    from optimizer.util import score, convert, get_neighbors
    
    scenario = Scenario.model_validate_json((scenario_folder_path / "scenario.json").read_text(encoding='utf-8'))
    initial_result = run_simulation(scenario_folder_path, weight_completion=weight_completion, weight_loco=weight_loco)
    initial_summary = initial_result[0]
    initial_score = initial_result[1]

    # Helper function to canonicalize parameter dicts for caching seen configurations
    def dict_to_key(d: dict) -> str:
        def _serialize_enums(obj):
            if isinstance(obj, dict):
                return {k: _serialize_enums(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [_serialize_enums(x) for x in obj]
            elif hasattr(obj, "value"):
                return obj.value
            return obj
        return json.dumps(_serialize_enums(d), sort_keys=True)

    # Initialize seen evaluations to avoid duplicates and store initial config
    seen = {}
    initial_params = {
        "task_priorities": {
            k: (v.model_dump() if v is not None else None)
            for k, v in scenario.task_priorities.items()
        }
    }
    initial_key = dict_to_key(initial_params)
    seen[initial_key] = {
        "score": initial_score,
        "completion_rate_pct": initial_summary.completion_rate_pct,
        "loco_utilization_pct": initial_summary.loco_utilization_pct,
        "params": initial_params,
    }

    print(parameter_config.size())

    # 1. Phase: Randomly generate parameters.
    rng = random.Random(seed)
    samples = []
    elite_scenarios = []
    attempts = 0
    while len(samples) < n_random and attempts < n_random * 10:
        attempts += 1
        test = parameter_config.sample_value(rng)
        if test is None:
            raise RuntimeError("Failed to sample parameters. Top-Level Parameters should not contain Optionals.")
        key = dict_to_key(test)
        if key in seen or any(dict_to_key(s) == key for s in samples):
            continue
        new_scenario = convert(test, scenario)
        samples.append(test)
        elite_scenarios.append(new_scenario)

    typer.echo("Evaluating initial random sample pool in parallel...")
    results = run_parallel(scenario_folder_path, elite_scenarios, weight_completion=weight_completion, weight_loco=weight_loco)
    
    rated_runs = []
    for param_dict, res in zip(samples, results):
        if res is not None:
            summary, sc, scen = res
            rated_runs.append((sc, param_dict, res))
            
    rated_runs.sort(key=lambda x: x[0], reverse=True)

    # Print top 5 elites
    for i in range(min(5, len(rated_runs))):
        sc, param_dict, res = rated_runs[i]
        result = res[0]
        typer.echo(f"Top {i+1} Elite: Score = {sc:.4f}, Completion Rate = {result.completion_rate_pct:.1f}%, Loco Utilization = {result.loco_utilization_pct:.1f}%")

    # Cache Phase 1 evaluations
    for sc, param_dict, res in rated_runs:
        summary = res[0]
        seen[dict_to_key(param_dict)] = {
            "score": sc,
            "completion_rate_pct": summary.completion_rate_pct,
            "loco_utilization_pct": summary.loco_utilization_pct,
            "params": param_dict,
        }

    # 2. Phase: Coordinate descent search along elites.
    starts = rated_runs[:k_starts]
    _TASK_NAMES = (
        "collection_to_retrofit",
        "retrofit_to_workshop",
        "workshop_to_retrofitted",
        "retrofitted_to_parking",
    )

    typer.echo(f"\nPhase 2 — coordinate descent from {len(starts)} starting point(s)")

    for start_idx, (start_score, start_params, start_res) in enumerate(starts):
        current_params = start_params
        current_score = start_score
        typer.echo(f"\n  Start {start_idx + 1}/{len(starts)}  (initial score={current_score:.4f})")

        for round_idx in range(max_rounds):
            improved = False

            for task_name in _TASK_NAMES:
                task_param = parameter_config.params["task_priorities"].params[task_name]
                task_val = current_params["task_priorities"][task_name]
                
                neighbors_task_val = get_neighbors(task_param, task_val)
                
                neighbor_params = []
                neighbor_scenarios = []
                
                for task_neighbor in neighbors_task_val:
                    n_params = copy.deepcopy(current_params)
                    n_params["task_priorities"][task_name] = task_neighbor
                    
                    key = dict_to_key(n_params)
                    if key not in seen:
                        neighbor_params.append(n_params)
                        neighbor_scenarios.append(convert(n_params, scenario))

                if neighbor_scenarios:
                    # Run neighbor batch in parallel
                    batch_results = run_parallel(scenario_folder_path, neighbor_scenarios, weight_completion=weight_completion, weight_loco=weight_loco)
                    for n_p, res in zip(neighbor_params, batch_results):
                        if res is not None:
                            summary, sc, scen = res
                            seen[dict_to_key(n_p)] = {
                                "score": sc,
                                "completion_rate_pct": summary.completion_rate_pct,
                                "loco_utilization_pct": summary.loco_utilization_pct,
                                "params": n_p,
                            }

                # Find the best neighbor (including previously evaluated configurations)
                best_neighbor = None
                best_neighbor_score = current_score
                
                for task_neighbor in neighbors_task_val:
                    n_params = copy.deepcopy(current_params)
                    n_params["task_priorities"][task_name] = task_neighbor
                    key = dict_to_key(n_params)
                    s = seen.get(key, {}).get("score", float("-inf"))
                    if s > best_neighbor_score:
                        best_neighbor_score = s
                        best_neighbor = n_params

                if best_neighbor is not None:
                    typer.echo(
                        f"    [{task_name[:3]}] improved: "
                        f"{current_score:.4f} → {best_neighbor_score:.4f}"
                    )
                    current_params = best_neighbor
                    current_score = best_neighbor_score
                    improved = True

            if not improved:
                typer.echo(f"  Converged after round {round_idx + 1}")
                break
        else:
            typer.echo(f"  Reached max_rounds={max_rounds}")

        typer.echo(f"  Final score for start {start_idx + 1}: {current_score:.4f}")

    # Output overall results
    sorted_seen = sorted(seen.values(), key=lambda x: x["score"], reverse=True)

    def serialize_params(obj):
        if isinstance(obj, dict):
            return {k: serialize_params(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [serialize_params(x) for x in obj]
        elif hasattr(obj, "value"):
            return obj.value
        return obj

    results_list = [
        {
            "parameters": serialize_params(r["params"]),
            "completion": r["completion_rate_pct"],
            "loco_utilization": r["loco_utilization_pct"],
            "score": r["score"],
        }
        for r in sorted_seen
    ]

    results_json.parent.mkdir(parents=True, exist_ok=True)
    with open(results_json, "w", encoding="utf-8") as f:
        json.dump(results_list, f, indent=2)

    typer.echo("\n" + "=" * 60)
    typer.echo(f"OPTIMIZATION COMPLETE (Total unique configurations evaluated: {len(seen)})")
    typer.echo("=" * 60)

    # Helper function to format the difference compared to initial
    def format_diff(val: float, initial_val: float, is_pct: bool = False) -> str:
        diff = val - initial_val
        if abs(diff) < 1e-9:
            diff = 0.0
        sign = "+" if diff >= 0 else ""
        pct_sign = "%" if is_pct else ""
        if is_pct:
            return f" ({sign}{diff:.2f}{pct_sign})"
        else:
            return f" ({sign}{diff:.4f})"

    typer.echo("\nInitial Configuration:")
    typer.echo(
        f"  Score = {initial_score:.4f} | "
        f"Completion Rate = {initial_summary.completion_rate_pct:.2f}% | "
        f"Loco Utilization = {initial_summary.loco_utilization_pct:.2f}%"
    )

    typer.echo("\nTop 5 Overall Optimized Configurations:")
    for i in range(min(5, len(sorted_seen))):
        r = sorted_seen[i]
        sc = r["score"]
        comp = r["completion_rate_pct"]
        loco = r["loco_utilization_pct"]
        
        score_diff = format_diff(sc, initial_score, is_pct=False)
        comp_diff = format_diff(comp, initial_summary.completion_rate_pct, is_pct=True)
        loco_diff = format_diff(loco, initial_summary.loco_utilization_pct, is_pct=True)
        
        typer.echo(
            f"  Rank {i+1}: Score = {sc:.4f}{score_diff} | "
            f"Completion Rate = {comp:.2f}%{comp_diff} | "
            f"Loco Utilization = {loco:.2f}%{loco_diff}"
        )


if __name__ == '__main__':
    app()
