"""PopUp-Sim main entry point for freight rail DAC migration simulation tool."""

import logging
from pathlib import Path
from typing import Annotated
from typing import Any

import typer

from configuration.service import ConfigurationError
from configuration.service import ConfigurationService
from core.i18n import _
from core.i18n import init_i18n
from core.i18n import set_locale
from core.logging import FileConfig
from core.logging import FormatType
from core.logging import Logger
from core.logging import LoggingConfig
from core.logging import configure_logging
from core.logging import get_logger

APP_NAME = 'popupsim'
logger: Logger = get_logger(__name__)

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
        logger.error('Scenario path validation failed', translate=True, reason='not_provided')
        typer.echo(_('Error: Scenario path is required but not provided'))
        raise typer.Exit(1)

    if not scenario_path.exists():
        logger.error('Scenario file not found', translate=True, path=str(scenario_path))
        typer.echo(_('Error: Scenario file does not exist: %(path)s', path=scenario_path))
        raise typer.Exit(1)
    if not scenario_path.is_file():
        logger.error('Scenario path is not a file', translate=True, path=str(scenario_path))
        typer.echo(_('Error: Scenario path is not a file: %(path)s', path=scenario_path))
        raise typer.Exit(1)
    try:
        with scenario_path.open('r'):
            pass
    except (PermissionError, OSError) as e:
        logger.error('Scenario file not readable', translate=True, path=str(scenario_path), error=str(e))
        typer.echo(_('Error: Scenario file is not readable: %(path)s (%(error)s)', path=scenario_path, error=str(e)))
        raise typer.Exit(1) from None

    logger.info('Scenario path validated', translate=True, path=str(scenario_path))
    return scenario_path


def display_scenario_info(config: Any, validation_result: Any) -> None:
    """Display loaded scenario information.

    Parameters
    ----------
    config : ScenarioConfig
        Loaded scenario configuration.
    validation_result : ValidationResult
        Validation results.
    """
    typer.echo(_('\nScenario loaded and validated successfully.'))
    typer.echo(_('Scenario ID: %(id)s', id=config.scenario_id))
    typer.echo(_('Start Date: %(date)s', date=config.start_date))
    typer.echo(_('End Date: %(date)s', date=config.end_date))
    typer.echo(_('Number of Trains: %(count)d', count=len(config.train) if config.train else 0))
    workshop_track_count = len(getattr(config.workshop, 'tracks', [])) if config.workshop else 0
    typer.echo(_('Number of Workshop Tracks: %(count)d', count=workshop_track_count))
    typer.echo(_('Number of Routes: %(count)d', count=len(config.routes) if config.routes else 0))
    typer.echo(_('\nValidation Summary:'))
    validation_result.print_summary()


def setup_logging_and_i18n(debug: str) -> None:
    """Initialize i18n and configure logging system.

    Parameters
    ----------
    debug : str
        Debug level (ERROR, WARNING, INFO, DEBUG).
    """
    localizer = init_i18n(Path('popupsim/backend/src/core/i18n/locales'))
    set_locale('de')
    log_level = getattr(logging, debug.upper(), logging.INFO)
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    configure_logging(
        LoggingConfig(
            level=log_level,
            format_type=FormatType.STRUCTURED,
            console_output=True,
            file=FileConfig(path=log_dir / 'simulation.log', max_bytes=50 * 1024 * 1024, backup_count=5),
            translator=localizer,
        )
    )


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
        logger.error('Output path validation failed', translate=True, reason='not_provided')
        typer.echo(_('Error: Output path is required but not provided'))
        raise typer.Exit(1)

    if not output_path.exists():
        logger.error('Output directory not found', translate=True, path=str(output_path))
        typer.echo(_('Error: Output directory does not exist: %(path)s', path=output_path))
        raise typer.Exit(1)
    if not output_path.is_dir():
        logger.error('Output path is not a directory', translate=True, path=str(output_path))
        typer.echo(_('Error: Output path is not a directory: %(path)s', path=output_path))
        raise typer.Exit(1)
    try:
        test_file = output_path / '.write_test'
        test_file.touch()
        test_file.unlink()
    except (PermissionError, OSError) as e:
        logger.error('Output directory not writable', translate=True, path=str(output_path), error=str(e))
        typer.echo(_('Error: Output directory is not writable: %(path)s (%(error)s)', path=output_path, error=str(e)))
        raise typer.Exit(1) from None

    logger.info('Output path validated', translate=True, path=str(output_path))
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
    setup_logging_and_i18n(debug)

    logger.info('Application started', translate=True, app_name=APP_NAME, debug_level=debug)

    # Show help if no required parameters are provided
    if scenario_path is None and output_path is None:
        logger.warning('No required parameters provided', translate=True)
        typer.echo(_('No required parameters provided. Showing help:\n'))
        typer.echo(ctx.get_help(), color=ctx.color)
        raise typer.Exit(1)

    # Validate debug level
    if debug not in ['ERROR', 'WARNING', 'INFO', 'DEBUG']:
        logger.error('Invalid debug level', translate=True, debug_level=debug)
        typer.echo(_('Error: Invalid debug level: %(level)s. Must be one of: ERROR, WARNING, INFO, DEBUG', level=debug))
        raise typer.Exit(1)

    # Validate scenarioPath
    scenario_path = validate_scenario_path(scenario_path)
    typer.echo(_('✓ Using scenario file at: %(path)s', path=scenario_path))

    # Validate outputPath
    output_path = validate_output_path(output_path)
    typer.echo(_('✓ Output will be saved to: %(path)s', path=output_path))

    if verbose:
        logger.info('Verbose mode enabled', translate=True)
        typer.echo(_('✓ Verbose mode enabled.'))

    typer.echo(_('✓ Debug level set to: %(level)s', level=debug))

    # Load and validate scenario using ConfigurationService
    try:
        logger.info('Loading scenario configuration', translate=True, scenario_dir=str(scenario_path.parent))
        service = ConfigurationService()
        # scenario_path is guaranteed to be Path here (validated above)
        if scenario_path is None:  # pragma: no cover
            raise typer.Exit(1)
        config, validation_result = service.load_complete_scenario(str(scenario_path.parent))

        workshop_tracks = len(getattr(config.workshop, 'tracks', [])) if config.workshop else 0
        logger.info(
            'Scenario loaded successfully',
            translate=True,
            scenario_id=config.scenario_id,
            train_count=len(config.train) if config.train else 0,
            workshop_tracks=workshop_tracks,
            routes_count=len(config.routes) if config.routes else 0,
        )

        display_scenario_info(config, validation_result)

        # Check for critical errors that prevent simulation
        if not validation_result.is_valid:
            logger.error(
                'Critical validation errors found', translate=True, error_count=len(validation_result.get_errors())
            )
            typer.echo(_('\nCritical errors found. Simulation cannot proceed.'))
            raise typer.Exit(1)

    except ConfigurationError as e:
        logger.error('Configuration error occurred', translate=True, error=str(e), exc_info=True)
        typer.echo(_('Configuration error: %(error)s', error=str(e)))
        raise typer.Exit(1) from e
    except Exception as e:
        logger.error(
            'Unexpected error occurred', translate=True, error=str(e), error_type=type(e).__name__, exc_info=True
        )
        typer.echo(_('Unexpected error: %(error)s', error=str(e)))
        raise typer.Exit(1) from e

    # Main application logic would go here
    logger.info('Starting simulation processing', translate=True)
    typer.echo(_('\n🚀 Starting popupsim processing...'))
    typer.echo(_('Application would start processing here...'))

    logger.info('Application completed successfully', translate=True)


if __name__ == '__main__':
    # Run the Typer CLI app, but provide no arguments so Typer parses from sys.argv
    app()
