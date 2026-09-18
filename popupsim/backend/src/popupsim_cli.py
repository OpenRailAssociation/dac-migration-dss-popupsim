"""Console-script entry point for PopUpSim.

The backend sources use top-level imports (e.g. ``from application...``) that
assume this directory (``popupsim/backend/src``) is on ``sys.path``. This shim
ensures that is the case before importing the Typer app, so the ``popupsim``
console script (``uv run popupsim``) behaves the same as
``uv run python popupsim/backend/src/main.py``.
"""

from pathlib import Path
import sys


def main() -> None:
    """Run the PopUpSim Typer CLI."""
    src_str = str(Path(__file__).resolve().parent)
    if src_str not in sys.path:
        sys.path.insert(0, src_str)

    from main import app  # imported after sys.path setup

    app()


if __name__ == '__main__':
    main()
