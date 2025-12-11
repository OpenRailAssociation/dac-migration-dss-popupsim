"""Workshop metrics calculator."""

from collections import defaultdict
from typing import Any


class WorkshopMetricsCalculator:
    """Calculates workshop-specific metrics from events."""

    def __init__(self, events: list[tuple[float, Any]], duration_hours: float) -> None:
        self.events = events
        self.duration_hours = duration_hours

    def calculate(self) -> dict[str, Any]:
        """Calculate workshop statistics."""
        workshop_data = defaultdict(
            lambda: {
                'wagons_processed': 0,
                'retrofits_started': 0,
                'utilization_percent': 0.0,
            }
        )

        for _, event in self.events:
            event_type = type(event).__name__
            workshop_id = getattr(event, 'workshop_id', None)

            if workshop_id:
                if event_type in (
                    'WagonRetrofitCompletedEvent',
                    'RetrofitCompletedEvent',
                ):
                    workshop_data[workshop_id]['wagons_processed'] += 1
                elif event_type == 'RetrofitStartedEvent':
                    workshop_data[workshop_id]['retrofits_started'] += 1

        for workshop_id in workshop_data:
            processed = workshop_data[workshop_id]['wagons_processed']
            workshop_data[workshop_id]['utilization_percent'] = min(
                processed / max(self.duration_hours, 0.1) * 100, 100.0
            )

        return {
            'total_workshops': len(workshop_data),
            'workshops': dict(workshop_data),
            'total_wagons_processed': sum(w['wagons_processed'] for w in workshop_data.values()),
        }
