"""JSON-based analytics repository implementation."""

import json
from pathlib import Path
from typing import Any

from contexts.analytics.domain.aggregates.analytics_session import (
    AnalyticsSession,
)
from contexts.analytics.domain.repositories.analytics_repository import (
    AnalyticsRepository,
)
from contexts.analytics.domain.value_objects.analytics_metrics import (
    Threshold,
)


class JSONAnalyticsRepository(AnalyticsRepository):
    """JSON file-based storage for analytics sessions."""

    def __init__(self, storage_dir: Path) -> None:
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def save(self, session: AnalyticsSession) -> None:
        """Save analytics session to JSON."""
        session_file = self.storage_dir / f"{session.session_id}.json"

        data = {
            "session_id": session.session_id,
            "start_time": session.start_time,
            "collectors": self._serialize_collectors(session),
            "thresholds": self._serialize_thresholds(session),
        }

        with open(session_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def find_by_id(self, session_id: str) -> AnalyticsSession | None:
        """Find session by ID from JSON."""
        session_file = self.storage_dir / f"{session_id}.json"

        if not session_file.exists():
            return None

        with open(session_file, encoding="utf-8") as f:
            data = json.load(f)
            return self._deserialize_session(data)

    def find_all(self) -> list[AnalyticsSession]:
        """Find all sessions from JSON files."""
        sessions = []
        for session_file in self.storage_dir.glob("*.json"):
            with open(session_file, encoding="utf-8") as f:
                data = json.load(f)
                session = self._deserialize_session(data)
                if session:
                    sessions.append(session)
        return sessions

    def delete(self, session_id: str) -> None:
        """Delete session JSON file."""
        session_file = self.storage_dir / f"{session_id}.json"
        if session_file.exists():
            session_file.unlink()

    def _serialize_collectors(self, session: AnalyticsSession) -> dict[str, Any]:
        """Serialize collectors to dict."""
        collectors_data = {}

        for collector_id, collector in session.get_all_collectors().items():
            metrics_data = {}
            for key in collector.get_metric_keys():
                metrics_data[key] = [
                    {"key": key, "value": value, "timestamp": timestamp}
                    for timestamp, value in collector.get_time_series(key)
                ]

            collectors_data[collector_id] = {
                "collector_id": collector.collector_id.id,
                "events_processed": collector.events_processed,
                "metrics": metrics_data,
            }

        return collectors_data

    def _serialize_thresholds(self, session: AnalyticsSession) -> list[dict[str, Any]]:
        """Serialize thresholds to list."""
        return [
            {
                "metric_name": threshold.metric_name,
                "warning_value": threshold.warning_value,
                "critical_value": threshold.critical_value,
            }
            for threshold in session.get_all_thresholds().values()
        ]

    def _deserialize_session(self, data: dict[str, Any]) -> AnalyticsSession:
        """Deserialize session from dict."""
        session = AnalyticsSession(
            session_id=data["session_id"], start_time=data["start_time"]
        )

        # Restore collectors
        for collector_id, collector_data in data.get("collectors", {}).items():
            collector = session.add_collector(collector_id)
            collector.events_processed = collector_data["events_processed"]

            # Restore metrics
            for entries_data in collector_data.get("metrics", {}).values():
                for entry_data in entries_data:
                    collector.record_metric(
                        entry_data["key"], entry_data["value"], entry_data["timestamp"]
                    )

        # Restore thresholds
        for threshold_data in data.get("thresholds", []):
            threshold = Threshold(
                metric_name=threshold_data["metric_name"],
                warning_value=threshold_data["warning_value"],
                critical_value=threshold_data["critical_value"],
            )
            session.set_threshold(threshold)

        return session
