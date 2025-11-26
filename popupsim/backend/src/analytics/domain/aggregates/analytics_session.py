"""Analytics session aggregate root."""

from dataclasses import dataclass
from dataclasses import field

from ..events.base_event import DomainEvent
from ..events.simulation_events import BottleneckDetectedEvent
from ..models.kpi_result import KPIResult
from ..value_objects.timestamp import Timestamp


@dataclass
class AnalyticsSession:
    """Aggregate root for analytics operations."""

    scenario_id: str
    _events: list[DomainEvent] = field(default_factory=list, init=False)
    _kpi_result: KPIResult | None = field(default=None, init=False)

    def record_event(self, event: DomainEvent) -> None:
        """Record domain event in session."""
        self._events.append(event)

    def get_events(self) -> list[DomainEvent]:
        """Get all recorded events."""
        return self._events.copy()

    def set_kpi_result(self, kpi_result: KPIResult) -> None:
        """Set calculated KPI result."""
        self._kpi_result = kpi_result

        # Detect and record bottlenecks as events
        for bottleneck in kpi_result.bottlenecks:
            if bottleneck.severity in ['high', 'critical']:
                event = BottleneckDetectedEvent.create(
                    timestamp=Timestamp.from_simulation_time(0.0),  # End of simulation
                    location=bottleneck.location,
                    severity=bottleneck.severity,
                    impact_description=bottleneck.description,
                )
                self.record_event(event)

    def get_kpi_result(self) -> KPIResult | None:
        """Get KPI calculation result."""
        return self._kpi_result

    def has_critical_bottlenecks(self) -> bool:
        """Check if session has critical bottlenecks."""
        if not self._kpi_result:
            return False
        return any(b.severity == 'critical' for b in self._kpi_result.bottlenecks)

    def add_event(self, event: DomainEvent) -> None:
        """Add event to session (alias for record_event)."""
        self.record_event(event)

    def complete_session(self) -> None:
        """Mark session as completed."""
        # Session completion logic if needed
