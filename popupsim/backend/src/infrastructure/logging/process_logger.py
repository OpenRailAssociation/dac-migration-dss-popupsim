"""Process logger for tracking simulation operations."""

import logging
from pathlib import Path


class ProcessLogger:
    """Logger for tracking detailed process operations."""

    def __init__(self, output_dir: Path) -> None:
        self.logger = logging.getLogger('process')
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False

        # Clear existing handlers
        self.logger.handlers.clear()

        # File handler for process log
        output_dir.mkdir(parents=True, exist_ok=True)
        handler = logging.FileHandler(output_dir / 'process.log', mode='w', encoding='utf-8')
        handler.setFormatter(logging.Formatter('%(asctime)s | t=%(sim_time)6.1f | %(message)s', datefmt='%H:%M:%S'))
        self.logger.addHandler(handler)
        self.current_time = 0.0

    def set_time(self, sim_time: float) -> None:
        """Update current simulation time."""
        self.current_time = sim_time

    def log(self, message: str, **kwargs: float) -> None:
        """Log process message with simulation time."""
        self.logger.info(message, extra={'sim_time': kwargs.get('sim_time', self.current_time)})


# Global process logger instance
_PROCESS_LOGGER: ProcessLogger | None = None


def init_process_logger(output_dir: Path) -> ProcessLogger:
    """Initialize global process logger."""
    # pylint: disable=global-statement
    global _PROCESS_LOGGER
    _PROCESS_LOGGER = ProcessLogger(output_dir)
    return _PROCESS_LOGGER


def get_process_logger() -> ProcessLogger:
    """Get global process logger instance."""
    if _PROCESS_LOGGER is None:
        msg = 'Process logger not initialized'
        raise RuntimeError(msg)
    return _PROCESS_LOGGER
