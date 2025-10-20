"""PopUp-Sim main entry point for freight rail DAC migration simulation tool."""

import argparse

APP_NAME = 'popupsim'


def main() -> None:
    """Main entry point for the popupsim application."""
    parser = argparse.ArgumentParser(description=f'Main entry point for the {APP_NAME} application.')
    parser.add_argument('--configpath', type=str, default=None, help='Path to the configuration file.')
    args = parser.parse_args()

    if args.configpath:
        print(f'Using config file at: {args.configpath}')
    else:
        print('No config path provided. Using default configuration.')


if __name__ == '__main__':
    main()
