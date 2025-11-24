"""PopUp-Sim main entry point for freight rail DAC migration simulation tool."""

from pathlib import Path
from typing import Annotated
from typing import Any

from builders.scenario_builder import BuilderError
from builders.scenario_builder import ScenarioBuilder
from simulation.popupsim import PopupSim
from simulation.sim_adapter import SimPyAdapter
import typer

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


def _validate_and_load_scenario(scenario_path: Path | None, output_path: Path | None,
                                debug: str, verbose: bool) -> Any:
    """Validate inputs and load scenario."""
    if debug not in ['ERROR', 'WARNING', 'INFO', 'DEBUG']:
        typer.echo(f'Error: Invalid debug level: {debug}. Must be one of: ERROR, WARNING, INFO, DEBUG')
        raise typer.Exit(1)
    scenario_path = validate_scenario_path(scenario_path)
    typer.echo(f'Using scenario file at: {scenario_path}')
    output_path = validate_output_path(output_path)
    typer.echo(f'Output will be saved to: {output_path}')
    if verbose:
        typer.echo('Verbose mode enabled.')
    typer.echo(f'Debug level set to: {debug}')
    scenario = ScenarioBuilder(scenario_path).build()
    typer.echo('Scenario loaded and validated successfully.')
    typer.echo(f'Scenario ID: {scenario.scenario_id}')
    typer.echo(f'Start Date: {scenario.start_date}')
    typer.echo(f'End Date: {scenario.end_date}')
    if scenario.routes:
        typer.echo(f'Number of Routes: {len(scenario.routes)}')
    if scenario.trains:
        typer.echo(f'Number of Trains: {len(scenario.trains)}')
    if scenario.workshops:
        typer.echo(f'Number of Workshops: {len(scenario.workshops)}')
    return scenario


def _run_simulation_and_display_metrics(scenario: Any) -> None:  # type: ignore[misc]
    """Run simulation and display metrics."""
    typer.echo('\nStarting simulation...')
    sim_adapter = SimPyAdapter.create_simpy_adapter()
    popup_sim = PopupSim(sim_adapter, scenario)
    popup_sim.run()
    metrics = popup_sim.get_metrics()
    typer.echo('\n=== Simulation Metrics ===')
    for category, category_metrics in metrics.items():
        typer.echo(f'\n{category.upper().replace("_", " ")}:')
        for metric in category_metrics:
            typer.echo(f'  {metric["name"].replace("_", " ").title()}: {metric["value"]} {metric["unit"]}')


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
    if scenario_path is None and output_path is None:
        typer.echo('No required parameters provided. Showing help:\n')
        typer.echo(ctx.get_help(), color=ctx.color)
        raise typer.Exit(1)
    try:
        scenario = _validate_and_load_scenario(scenario_path, output_path, debug, verbose)
        _run_simulation_and_display_metrics(scenario)
    except BuilderError as e:
        typer.echo(f'Configuration error: {e}')
        raise typer.Exit(1) from e
    except Exception as e:
        typer.echo(f'Unexpected error: {e}')
        raise typer.Exit(1) from e


if __name__ == '__main__':
    # Run the Typer CLI app, but provide no arguments so Typer parses from sys.argv
    app()
