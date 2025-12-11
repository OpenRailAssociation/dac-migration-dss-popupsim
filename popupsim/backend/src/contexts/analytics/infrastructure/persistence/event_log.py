"""Append-only event log."""

import json
from pathlib import Path
from typing import Any


class EventLog:
    """Append-only event log using JSONL."""

    def __init__(self, log_path: Path) -> None:
        self.log_path = log_path
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, timestamp: float, event: Any) -> None:
        """Append event to log."""
        event_data = {
            'timestamp': timestamp,
            'event_type': type(event).__name__,
            'event_data': self._serialize(event),
        }
        with open(self.log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(event_data) + '\n')

    def _serialize(self, event: Any) -> dict[str, Any]:
        """Serialize event."""
        if hasattr(event, '__dict__'):
            return {k: v for k, v in event.__dict__.items() if not k.startswith('_')}
        return {'value': str(event)}
