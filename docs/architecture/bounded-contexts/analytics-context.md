# Analytics Context - KPI Berechnung

## Verantwortlichkeit

**Zentrale KPI-Berechnung im Backend** - Frontend nur Visualisierung

### Kernaufgaben
- **Echtzeit-KPIs**: Auslastung, Durchsatz, Wartezeiten
- **Aggregierte Metriken**: Tages-/Wochen-/Monatsstatistiken  
- **Performance-Indikatoren**: Engpässe, Effizienz, Kapazitätsnutzung
- **Trend-Analysen**: Zeitreihen, Vergleiche, Prognosen

## Domain Services

```python
class KPICalculationService:
    """Zentrale KPI-Berechnung im Backend"""
    
    def calculate_real_time_kpis(self, simulation_state: SimulationState) -> RealTimeKPIs:
        """Berechnet Echtzeit-KPIs"""
        return RealTimeKPIs(
            track_utilization=self._calculate_track_utilization(simulation_state),
            workshop_utilization=self._calculate_workshop_utilization(simulation_state),
            locomotive_utilization=self._calculate_locomotive_utilization(simulation_state),
            worker_utilization=self._calculate_worker_utilization(simulation_state),
            throughput_per_hour=self._calculate_throughput(simulation_state),
            average_waiting_time=self._calculate_waiting_times(simulation_state)
        )
    
    def _calculate_track_utilization(self, state: SimulationState) -> Dict[str, float]:
        """Berechnet Gleisauslastung in %"""
        utilization = {}
        for track in state.tracks:
            utilization[track.id] = (track.current_occupancy / track.capacity) * 100
        return utilization
    
    def _calculate_workshop_utilization(self, state: SimulationState) -> Dict[str, float]:
        """Berechnet Werkstattauslastung in %"""
        utilization = {}
        for workshop in state.workshops:
            utilization[workshop.id] = (workshop.active_stations / workshop.total_stations) * 100
        return utilization

@dataclass(frozen=True)
class RealTimeKPIs:
    """KPIs werden im Backend berechnet, ans Frontend gesendet"""
    track_utilization: Dict[str, float]
    workshop_utilization: Dict[str, float] 
    locomotive_utilization: Dict[str, float]
    worker_utilization: Dict[str, float]
    throughput_per_hour: float
    average_waiting_time: float
    timestamp: datetime = field(default_factory=datetime.now)
```

## Frontend Integration

**Frontend empfängt nur berechnete KPIs via WebSocket:**

```python
# Backend sendet KPIs
@dataclass
class KPIUpdateEvent:
    kpis: RealTimeKPIs
    simulation_id: str
    timestamp: datetime
```

**Frontend visualisiert nur - berechnet NICHT:**
- Empfängt KPIUpdateEvent via WebSocket
- Zeigt Charts/Dashboards an
- Keine KPI-Berechnung im Frontend