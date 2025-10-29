"""PopUp-Sim main entry point for freight rail DAC migration simulation tool."""

from pathlib import Path
from typing import Optional

import typer  # type: ignore[import-not-found] # pylint: disable=import-error
from typing_extensions import Annotated

from configuration.service import (  # type: ignore[import-not-found,import-untyped] # pylint: disable=import-error
    ConfigurationError,
    ConfigurationService,
)

APP_NAME = 'popupsim'

app = typer.Typer(
    name=APP_NAME,
    help='Main entry point for the popupsim application - freight rail DAC migration simulation tool.',
    add_completion=True,
)


def validate_scenario_path(scenario_path: Optional[Path]) -> Path:
    """Validate that the scenario path is provided, exists, is a file, and is readable."""
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


def validate_output_path(output_path: Optional[Path]) -> Path:
    """Validate that the output path is provided, exists, is a directory, and is writable."""
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
        Optional[Path],
        typer.Option(
            '--scenarioPath', help='Path to the scenario file (required).', rich_help_panel='Required Parameters'
        ),
    ] = None,
    output_path: Annotated[
        Optional[Path],
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
    """
    Main entry point for the popupsim application.

    This tool performs freight rail DAC migration simulation processing.
    Both scenario file and output directory paths are required.

    Examples:
        popupsim --scenarioPath ./scenario.json --outputPath ./output
        popupsim --scenarioPath ./scenario.json --outputPath ./output --verbose --debug DEBUG
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
        if scenario_path is None:  # pragma: no cover
            raise typer.Exit(1)
        config, validation_result = service.load_complete_scenario(str(scenario_path.parent))
        typer.echo('\nScenario loaded and validated successfully.')
        typer.echo(f'Scenario ID: {config.scenario_id}')
        typer.echo(f'Start Date: {config.start_date}')
        typer.echo(f'End Date: {config.end_date}')
        typer.echo(f'Number of Trains: {len(config.train)}')
        typer.echo(f'Number of Workshop Tracks: {len(config.workshop.tracks)}')
        typer.echo(f'Number of Routes: {len(config.routes)}')
        typer.echo('\nValidation Summary:')
        validation_result.print_summary()
    except ConfigurationError as e:
        typer.echo(f'Configuration error: {e}')
        raise typer.Exit(1) from e
    except Exception as e:
        typer.echo(f'Unexpected error: {e}')
        raise typer.Exit(1) from e

    # Main application logic would go here
    typer.echo('\n🚀 Starting popupsim processing...')
    typer.echo('Application would start processing here...')


if __name__ == '__main__':
    # Run the Typer CLI app, but provide no arguments so Typer parses from sys.argv
    app()
