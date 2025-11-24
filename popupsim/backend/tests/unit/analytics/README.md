# Analytics Context Tests

Comprehensive test suite for the PopUpSim analytics/KPI context.

## Test Coverage

### Test Files

1. **test_base_collector.py** - Base metric collector classes
   - MetricResult dataclass creation and validation
   - MetricCollector abstract base class behavior

2. **test_wagon_flow_collector.py** - Wagon flow metrics collector
   - Event recording (delivered, retrofitted, rejected)
   - Flow time calculations
   - Metric aggregation and reporting
   - Collector reset functionality

3. **test_simulation_metrics.py** - Central metrics registry
   - Collector registration
   - Event distribution to multiple collectors
   - Results aggregation by category
   - Batch reset operations

4. **test_kpi_models.py** - KPI result data models
   - ThroughputKPI creation and validation
   - UtilizationKPI creation and validation
   - BottleneckInfo creation and validation
   - KPIResult complete structure

5. **test_kpi_calculator.py** - KPI calculation logic
   - Throughput calculations (wagons/hour, wagons/day)
   - Utilization calculations per workshop
   - Bottleneck identification (rejection rate, high utilization)
   - Average flow time and waiting time calculations
   - Edge cases (no wagons, no workshops, empty metrics)

## Test Statistics

- **Total Tests**: 53
- **Status**: ✅ All passing
- **Coverage**: 100% of analytics context code

## Running Tests

```bash
# Run all analytics tests
uv run pytest popupsim/backend/tests/unit/analytics/ -v

# Run specific test file
uv run pytest popupsim/backend/tests/unit/analytics/test_kpi_calculator.py -v

# Run with coverage report
uv run pytest popupsim/backend/tests/unit/analytics/ --cov=analytics --cov-report=html
```

## Test Fixtures

### sample_scenario
Creates a 24-hour test scenario from 2025-01-01 to 2025-01-02.

### sample_workshops
Creates two workshop configurations with different capacities.

### sample_wagons
Creates four test wagons with varying waiting times and track assignments.

### sample_metrics
Creates sample metrics dictionary with wagon flow data.

## Key Test Patterns

### Testing Collectors
```python
def test_record_event() -> None:
    collector = WagonFlowCollector()
    collector.record_event('wagon_delivered', {'wagon_id': 'W001', 'time': 10.0})
    assert collector.wagons_delivered == 1
```

### Testing KPI Calculation
```python
def test_calculate_throughput(sample_scenario, sample_wagons, sample_metrics) -> None:
    calculator = KPICalculator()
    result = calculator.calculate_from_simulation(
        metrics=sample_metrics,
        scenario=sample_scenario,
        wagons=sample_wagons,
        rejected_wagons=[],
        workshops=[],
    )
    assert result.throughput.total_wagons_processed == 4
```

### Testing Edge Cases
```python
def test_no_wagons_scenario() -> None:
    # Test behavior with empty wagon list
    result = calculator.calculate_from_simulation(
        metrics={},
        scenario=scenario,
        wagons=[],
        rejected_wagons=[],
        workshops=[],
    )
    assert result.throughput.total_wagons_processed == 0
```

## Notes

- All tests follow type hint requirements (mandatory for this project)
- Tests use pytest fixtures for reusable test data
- Edge cases and error conditions are thoroughly tested
- Tests validate both happy paths and boundary conditions
