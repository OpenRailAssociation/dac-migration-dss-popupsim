"""CSV-based analytics repository implementation."""

import csv
import json
from pathlib import Path
from typing import Any

from contexts.analytics.domain.aggregates.analytics_session import AnalyticsSession
from contexts.analytics.domain.repositories.analytics_repository import AnalyticsRepository


class CSVAnalyticsRepository(AnalyticsRepository):
    """CSV file-based storage for analytics sessions."""

    def __init__(self, storage_dir: Path) -> None:
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._sessions_file = storage_dir / 'sessions.csv'
        self._metrics_dir = storage_dir / 'metrics'
        self._metrics_dir.mkdir(exist_ok=True)

    def save(self, session: AnalyticsSession) -> None:
        """Save analytics session to CSV."""
        self._save_session_metadata(session)
        self._save_session_metrics(session)

    def find_by_id(self, session_id: str) -> AnalyticsSession | None:
        """Find session by ID from CSV."""
        if not self._sessions_file.exists():
            return None

        with open(self._sessions_file, encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['session_id'] == session_id:
                    return self._load_session(row)
        return None

    def find_all(self) -> list[AnalyticsSession]:
        """Find all sessions from CSV."""
        if not self._sessions_file.exists():
            return []

        sessions = []
        with open(self._sessions_file, encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                session = self._load_session(row)
                if session:
                    sessions.append(session)
        return sessions

    def delete(self, session_id: str) -> None:
        """Delete session from CSV."""
        if not self._sessions_file.exists():
            return

        rows = []
        with open(self._sessions_file, encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = [row for row in reader if row['session_id'] != session_id]

        with open(self._sessions_file, 'w', newline='', encoding='utf-8') as f:
            if rows:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)

        metrics_file = self._metrics_dir / f'{session_id}.csv'
        if metrics_file.exists():
            metrics_file.unlink()

    def _save_session_metadata(self, session: AnalyticsSession) -> None:
        """Save session metadata to sessions.csv."""
        file_exists = self._sessions_file.exists()

        rows = []
        if file_exists:
            with open(self._sessions_file, encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = [row for row in reader if row['session_id'] != session.session_id]

        rows.append(
            {
                'session_id': session.session_id,
                'start_time': session.start_time,
                'collector_count': len(session.get_all_collectors()),
                'total_events': sum(c.events_processed for c in session.get_all_collectors().values()),
            }
        )

        with open(self._sessions_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    'session_id',
                    'start_time',
                    'collector_count',
                    'total_events',
                ],
            )
            writer.writeheader()
            writer.writerows(rows)

    def _save_session_metrics(self, session: AnalyticsSession) -> None:
        """Save session metrics to individual CSV file."""
        metrics_file = self._metrics_dir / f'{session.session_id}.csv'

        rows = []
        for collector_id, collector in session.get_all_collectors().items():
            for key in collector.get_metric_keys():
                for timestamp, value in collector.get_time_series(key):
                    rows.append(
                        {
                            'collector_id': collector_id,
                            'metric_key': key,
                            'value': value,
                            'timestamp': timestamp,
                        }
                    )

        if rows:
            with open(metrics_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['collector_id', 'metric_key', 'value', 'timestamp'])
                writer.writeheader()
                writer.writerows(rows)

    def _load_session(self, row: dict[str, str]) -> AnalyticsSession | None:
        """Load session from CSV row."""
        session = AnalyticsSession(session_id=row['session_id'], start_time=float(row['start_time']))

        metrics_file = self._metrics_dir / f'{session.session_id}.csv'
        if metrics_file.exists():
            with open(metrics_file, encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for metric_row in reader:
                    collector_id = metric_row['collector_id']
                    if collector_id not in session.get_all_collectors():
                        session.add_collector(collector_id)

                    collector = session.get_collector(collector_id)
                    if collector:
                        collector.record_metric(
                            metric_row['metric_key'],
                            self._parse_value(metric_row['value']),
                            float(metric_row['timestamp']),
                        )

        return session

    def _parse_value(self, value: str) -> Any:
        """Parse value from string."""
        try:
            return json.loads(value)
        except (json.JSONDecodeError, ValueError):
            return value
