"""PopUpSim New Architecture CLI - Bounded contexts implementation."""

import logging
from pathlib import Path
from typing import Annotated

import typer

from application.simulation_service import SimulationApplicationService
from contexts.configuration.domain.configuration_builder import ConfigurationBuilder
from infrastructure.logging import init_process_logger

app = typer.Typer(name='popupsim-new', help='PopUpSim New Architecture - Bounded contexts')


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
    event_handler = logging.FileHandler(output_path / 'events.log', mode='w', encoding='utf-8')
    event_handler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)-8s | %(message)s', datefmt='%H:%M:%S'))
    event_handler.setLevel(logging.INFO)

    # Configure console logging (only warnings and errors)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)-8s | %(message)s', datefmt='%H:%M:%S'))
    console_handler.setLevel(logging.ERROR)

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

    if verbose:
        typer.echo(f'Scenario: {scenario.id} ({len(scenario.trains)} trains)')
        typer.echo('Using new bounded contexts architecture')

    # Run new architecture simulation
    service = SimulationApplicationService(scenario)
    until = (scenario.end_date - scenario.start_date).total_seconds() / 60.0

    typer.echo('Running simulation...\n')
    result = service.execute(until)

    if result.success:
        typer.echo('\n' + '=' * 60)
        typer.echo('SIMULATION COMPLETED SUCCESSFULLY')
        typer.echo('=' * 60)

        # Get metrics from contexts
        external_trains = service.contexts.get('external_trains')
        yard = service.contexts.get('yard')
        popup = service.contexts.get('popup')
        shunting = service.contexts.get('shunting')
        analytics = service.contexts.get('analytics')

        # Generate outputs
        typer.echo(f'\nGenerating outputs...')

        # Dashboard export and visualizations
        if analytics:
            # Export dashboard data
            dashboard_files = analytics.export_dashboard_data(
                output_path, yard_context=yard, popup_context=popup, shunting_context=shunting
            )
            typer.echo(f'\nDashboard data exported:')
            for file_type, file_path in dashboard_files.items():
                typer.echo(f'  - {file_type}: {file_path.name}')

            # Generate visualizations
            context_metrics = {
                'external_trains': external_trains.get_metrics() if external_trains else {},
                'popup': popup.get_metrics() if popup else {},
                'yard': yard.get_metrics() if yard else {},
                'shunting': shunting.get_metrics() if shunting else {},
            }
            charts = analytics.visualizer.generate_all_charts(analytics, output_path, context_metrics)
            typer.echo(f'\nVisualizations generated:')
            for chart in charts:
                typer.echo(f'  - {chart.name}')

        # Show process log content
        process_log_path = output_path / 'process.log'
        if process_log_path.exists():
            typer.echo(f'\nPROCESS LOG:')
            typer.echo('=' * 60)
            with open(process_log_path, 'r', encoding='utf-8') as f:
                typer.echo(f.read())
            typer.echo('=' * 60)

        # Statistics after log
        typer.echo('\n' + '=' * 60)
        typer.echo('SIMULATION STATISTICS')
        typer.echo('=' * 60)

        # Wagon metrics
        typer.echo('\nWAGON METRICS:')
        if external_trains:
            ext_metrics = external_trains.get_metrics()
            typer.echo(f'  Total wagons arrived:     {ext_metrics.get("total_wagons", 0)}')
            typer.echo(f'  Wagons completed:         {ext_metrics.get("completed_wagons", 0)}')

        # Workshop metrics
        if popup:
            popup_metrics = popup.get_metrics()
            typer.echo(f'\nWORKSHOP METRICS:')
            typer.echo(f'  Workshops:                {popup_metrics.get("workshops", 0)}')
            typer.echo(f'  Total retrofit bays:      {popup_metrics.get("total_bays", 0)}')
            typer.echo(f'  Overall utilization:      {popup_metrics.get("utilization_percentage", 0):.1f}%')
            per_workshop = popup_metrics.get('per_workshop_utilization', {})
            if per_workshop:
                # Filter out track-based workshop entries
                filtered_workshops = {k: v for k, v in per_workshop.items() if not k.startswith('track_')}
                for workshop_id, util in sorted(filtered_workshops.items()):
                    typer.echo(f'    {workshop_id}:             {util:.1f}%')
            per_bay = popup_metrics.get('per_bay_utilization', {})
            if per_bay:
                typer.echo(f'  Bay utilization:')
                for bay_id, util in sorted(per_bay.items()):
                    typer.echo(f'    {bay_id}:    {util:.1f}%')

        # Yard metrics
        if yard:
            yard_metrics = yard.get_metrics()
            typer.echo(f'\nYARD METRICS:')
            typer.echo(f'  Wagons classified:        {yard_metrics.get("classified_wagons", 0)}')
            typer.echo(f'  Wagons rejected:          {yard_metrics.get("rejected_wagons", 0)}')
            typer.echo(f'  Wagons on retrofitted:    {yard_metrics.get("wagons_on_retrofitted", 0)}')
            typer.echo(f'  Wagons parked:            {yard_metrics.get("wagons_parked", 0)}')
            track_util = yard_metrics.get('track_utilization', {})
            if track_util:
                typer.echo(f'  Track utilization:')
                for track_id, util in sorted(track_util.items()):
                    typer.echo(f'    {track_id}:          {util:.1f}%')

        # Shunting metrics
        if shunting:
            shunt_metrics = shunting.get_metrics()
            typer.echo(f'\nSHUNTING METRICS:')
            typer.echo(f'  Total locomotives:        {shunt_metrics.get("total_locomotives", 0)}')
            typer.echo(f'  Locomotive utilization:   {shunt_metrics.get("utilization_percentage", 0):.1f}%')
            breakdown = shunt_metrics.get('utilization_breakdown', {})
            if breakdown:
                typer.echo(f'  Utilization breakdown:')
                for status, pct in sorted(breakdown.items()):
                    typer.echo(f'    {status}:          {pct:.1f}%')
            per_loco = shunt_metrics.get('per_locomotive_breakdown', {})
            if per_loco:
                typer.echo(f'  Per-locomotive breakdown:')
                for loco_id, loco_breakdown in sorted(per_loco.items()):
                    typer.echo(f'    {loco_id}:')
                    for status, pct in sorted(loco_breakdown.items()):
                        typer.echo(f'      {status}:      {pct:.1f}%')

        typer.echo(f'\nSIMULATION TIME:            {result.duration:.1f} minutes')
        typer.echo('=' * 60)

    else:
        typer.echo('\nSIMULATION FAILED')
        raise typer.Exit(1)


if __name__ == '__main__':
    app()
