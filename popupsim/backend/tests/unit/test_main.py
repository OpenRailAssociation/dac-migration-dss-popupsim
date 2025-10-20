"""Unit tests for the main entry point module."""

from unittest.mock import MagicMock

import pytest

from src.main import APP_NAME, main


@pytest.mark.unit
def test_app_name():
    """Test that APP_NAME constant is correctly set."""
    assert APP_NAME == 'popupsim'


@pytest.mark.unit
def test_main_with_config_path(mocker):
    """Test main function when config path is provided."""
    # Arrange
    test_config_path = '/path/to/config'
    mock_args = MagicMock()
    mock_args.configpath = test_config_path
    mocker.patch('argparse.ArgumentParser.parse_args', return_value=mock_args)
    mock_print = mocker.patch('builtins.print')

    # Act
    main()

    # Assert
    mock_print.assert_called_once_with(f'Using config file at: {test_config_path}')


@pytest.mark.unit
def test_main_without_config_path(mocker):
    """Test main function when no config path is provided."""
    # Arrange
    mock_args = MagicMock()
    mock_args.configpath = None
    mocker.patch('argparse.ArgumentParser.parse_args', return_value=mock_args)
    mock_print = mocker.patch('builtins.print')

    # Act
    main()

    # Assert
    mock_print.assert_called_once_with('No config path provided. Using default configuration.')


@pytest.mark.unit
def test_argument_parser_creation(mocker):
    """Test argument parser is created with correct parameters."""
    # Arrange
    mock_parser = mocker.patch('argparse.ArgumentParser')
    mock_parser_instance = MagicMock()
    mock_parser.return_value = mock_parser_instance

    # Act
    main()

    # Assert
    mock_parser.assert_called_once()  # Assert on the mock, not on the patcher
    mock_parser_instance.add_argument.assert_called_once_with(
        '--configpath', type=str, default=None, help='Path to the configuration file.'
    )
