"""PopUp-Sim main entry point for freight rail DAC migration simulation tool."""

from pathlib import Path
from typing import Annotated

from simulation.popupsim import PopupSim
from simulation.sim_adapter import SimPyAdapter
import typer

from configuration.service import ConfigurationError
from configuration.service import ConfigurationService

APP_NAME = 'popupsim'

app = typer.Typer(
    name=APP_NAME,
    help='Main entry point for the popupsim application - freight rail DAC migration simulation tool.',
    add_completion=True,
)


def validate_scenario_path(scenario_path: Path | None) -> Path:
    """Validate that the scenario path is provided, exists, is a file, and is readable.

    Parameters
    ----------
    scenario_path : Path | None
        Path to the scenario file to validate.

    Returns
    -------
    Path
        Validated scenario path.

    Raises
    ------
    typer.Exit
        If validation fails.
    """
    if scenario_path is None:
        typer.echo('Error: Scenario path is required but not provided')
        raise typer.Exit(1)

    if not scenario_path.exists():
        typer.echo(f'Error: Scenario file does not exist: {scenario_path}')
        raise typer.Exit(1)
    if not scenario_path.is_file():
        typer.echo(f'Error: Scenario path is not a file: {scenario_path}')
        raise typer.Exit(1)
    try:
        with scenario_path.open('r'):
            pass
    except (PermissionError, OSError) as e:
        typer.echo(f'Error: Scenario file is not readable: {scenario_path} ({e})')
        raise typer.Exit(1) from None
    return scenario_path


def validate_output_path(output_path: Path | None) -> Path:
    """Validate that the output path is provided, exists, is a directory, and is writable.

    Parameters
    ----------
    output_path : Path | None
        Path to the output directory to validate.

    Returns
    -------
    Path
        Validated output path.

    Raises
    ------
    typer.Exit
        If validation fails.
    """
    if output_path is None:
        typer.echo('Error: Output path is required but not provided')
        raise typer.Exit(1)

    if not output_path.exists():
        typer.echo(f'Error: Output directory does not exist: {output_path}')
        raise typer.Exit(1)
    if not output_path.is_dir():
        typer.echo(f'Error: Output path is not a directory: {output_path}')
        raise typer.Exit(1)
    try:
        test_file = output_path / '.write_test'
        test_file.touch()
        test_file.unlink()
    except (PermissionError, OSError) as e:
        typer.echo(f'Error: Output directory is not writable: {output_path} ({e})')
        raise typer.Exit(1) from None
    return output_path


@app.command()
def main(
    ctx: typer.Context,
    scenario_path: Annotated[
        Path | None,
        typer.Option(
            '--scenarioPath', help='Path to the scenario file (required).', rich_help_panel='Required Parameters'
        ),
    ] = None,
    output_path: Annotated[
        Path | None,
        typer.Option(
            '--outputPath', help='Path to the output directory (required).', rich_help_panel='Required Parameters'
        ),
    ] = None,
    verbose: Annotated[
        bool, typer.Option('--verbose', help='Enable verbose output.', rich_help_panel='Optional Parameters')
    ] = False,
    debug: Annotated[
        str,
        typer.Option(
            '--debug', help='Debug level (ERROR, WARNING, INFO, DEBUG).', rich_help_panel='Optional Parameters'
        ),
    ] = 'INFO',
) -> None:
    """Main entry point for the popupsim application.

    This tool performs freight rail DAC migration simulation processing.
    Both scenario file and output directory paths are required.

    Parameters
    ----------
    ctx : typer.Context
        Typer context for help display.
    scenario_path : Path | None, optional
        Path to the scenario file, by default None.
    output_path : Path | None, optional
        Path to the output directory, by default None.
    verbose : bool, optional
        Enable verbose output, by default False.
    debug : str, optional
        Debug level (ERROR, WARNING, INFO, DEBUG), by default 'INFO'.

    Examples
    --------
    >>> popupsim --scenarioPath ./scenario.json --outputPath ./output
    >>> popupsim --scenarioPath ./scenario.json --outputPath ./output --verbose --debug DEBUG
    """
    # Show help if no required parameters are provided
    if scenario_path is None and output_path is None:
        typer.echo('No required parameters provided. Showing help:\n')
        typer.echo(ctx.get_help(), color=ctx.color)
        raise typer.Exit(1)

    # Validate debug level
    if debug not in ['ERROR', 'WARNING', 'INFO', 'DEBUG']:
        typer.echo(f'Error: Invalid debug level: {debug}. Must be one of: ERROR, WARNING, INFO, DEBUG')
        raise typer.Exit(1)

    # Validate scenarioPath
    scenario_path = validate_scenario_path(scenario_path)
    typer.echo(f'✓ Using scenario file at: {scenario_path}')

    # Validate outputPath
    output_path = validate_output_path(output_path)
    typer.echo(f'✓ Output will be saved to: {output_path}')

    if verbose:
        typer.echo('✓ Verbose mode enabled.')

    typer.echo(f'✓ Debug level set to: {debug}')

    # Load and validate scenario using ConfigurationService ---
    try:
        # Import here to avoid circular import at module level
        service = ConfigurationService()
        # scenario_path is guaranteed to be Path here (validated above)
        if scenario_path is None:
            raise typer.Exit(1)
        scenario_config, validation_result = service.load_complete_scenario(str(scenario_path.parent))
        typer.echo('\nScenario loaded and validated successfully.')
        typer.echo(f'Scenario ID: {scenario_config.scenario_id}')
        typer.echo(f'Start Date: {scenario_config.start_date}')
        typer.echo(f'End Date: {scenario_config.end_date}')
        typer.echo(f'Number of Trains: {len(scenario_config.train) if scenario_config.train else 0}')
        workshop_track_count = 0
        if scenario_config.workshop is not None:
            workshop_track_count = len(getattr(scenario_config.workshop, 'tracks', []))
        typer.echo(f'Number of Workshop Tracks: {workshop_track_count}')
        typer.echo(f'Number of Routes: {len(scenario_config.routes) if scenario_config.routes else 0}')
        typer.echo('\nValidation Summary:')
        validation_result.print_summary()

        if not validation_result.is_valid:
            typer.echo('\nErrors detected in scenario configuration. Exiting.')
            raise typer.Exit(1)
        # Main application logic would go here
        typer.echo('\n🚀 Starting popupsim processing...')
        sim_adapter = SimPyAdapter.create_simpy_adapter()
        popup_sim = PopupSim(sim_adapter, scenario_config)
        # pylint: disable=fixme
        # Todo make sure run_until is set appropriately from scenario config  # noqa: FIX002
        popup_sim.run()

    except ConfigurationError as e:
        typer.echo(f'Configuration error: {e}')
        raise typer.Exit(1) from e
    except Exception as e:
        typer.echo(f'Unexpected error: {e}')
        raise typer.Exit(1) from e


if __name__ == '__main__':
    # Run the Typer CLI app, but provide no arguments so Typer parses from sys.argv
    app()
