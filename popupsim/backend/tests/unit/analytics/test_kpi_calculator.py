"""Tests for KPI calculator."""

from datetime import UTC
from datetime import datetime

from analytics.domain.services.kpi_calculator import KPICalculator
import pytest
from workshop_operations.domain.entities.wagon import Wagon
from workshop_operations.domain.entities.wagon import WagonStatus
from workshop_operations.domain.entities.workshop import Workshop

from configuration.domain.models.scenario import Scenario


@pytest.fixture
def sample_scenario() -> Scenario:
    """Create sample scenario for testing."""
    return Scenario(
        scenario_id='TEST_SCENARIO',
        start_date=datetime(2025, 1, 1, 0, 0, tzinfo=UTC),
        end_date=datetime(2025, 1, 2, 0, 0, tzinfo=UTC),
    )


@pytest.fixture
def sample_workshops() -> list[Workshop]:
    """Create sample workshops for testing."""
    return [
        Workshop(
            workshop_id='WS001',
            track_id='T001',
            start_date='2025-01-01T00:00:00',
            end_date='2025-01-02T00:00:00',
            retrofit_stations=10,
            worker=5,
        ),
        Workshop(
            workshop_id='WS002',
            track_id='T002',
            start_date='2025-01-01T00:00:00',
            end_date='2025-01-02T00:00:00',
            retrofit_stations=8,
            worker=4,
        ),
    ]


@pytest.fixture
def sample_wagons() -> list[Wagon]:
    """Create sample wagons for testing."""
    return [
        Wagon(
            wagon_id='W001',
            length=15.0,
            is_loaded=True,
            needs_retrofit=True,
            track_id='T001',
            status=WagonStatus.RETROFITTED,
            arrival_time=datetime(2025, 1, 1, 0, 0, tzinfo=UTC),
            retrofit_start_time=600.0,
        ),
        Wagon(
            wagon_id='W002',
            length=15.0,
            is_loaded=True,
            needs_retrofit=True,
            track_id='T001',
            status=WagonStatus.RETROFITTED,
            arrival_time=datetime(2025, 1, 1, 0, 0, tzinfo=UTC),
            retrofit_start_time=900.0,
        ),
        Wagon(
            wagon_id='W003',
            length=15.0,
            is_loaded=True,
            needs_retrofit=True,
            track_id='T002',
            status=WagonStatus.RETROFITTED,
            arrival_time=datetime(2025, 1, 1, 0, 0, tzinfo=UTC),
            retrofit_start_time=1200.0,
        ),
        Wagon(
            wagon_id='W004',
            length=15.0,
            is_loaded=True,
            needs_retrofit=True,
            track_id='T002',
            status=WagonStatus.RETROFITTED,
            arrival_time=datetime(2025, 1, 1, 0, 0, tzinfo=UTC),
            retrofit_start_time=300.0,
        ),
    ]


@pytest.fixture
def sample_metrics() -> dict:
    """Create sample metrics for testing."""
    return {
        'wagon': [
            {'name': 'wagons_delivered', 'value': 5, 'unit': 'wagons'},
            {'name': 'wagons_retrofitted', 'value': 4, 'unit': 'wagons'},
            {'name': 'wagons_rejected', 'value': 1, 'unit': 'wagons'},
            {'name': 'avg_flow_time', 'value': 45.5, 'unit': 'min'},
        ]
    }


def test_kpi_calculator_initialization() -> None:
    """Test KPICalculator initialization."""
    calculator = KPICalculator()
    assert calculator is not None


def test_calculate_throughput_basic(
    sample_scenario: Scenario, sample_wagons: list[Wagon], sample_metrics: dict
) -> None:
    """Test basic throughput calculation."""
    calculator = KPICalculator()

    result = calculator.calculate_from_simulation(
        metrics=sample_metrics,
        scenario=sample_scenario,
        wagons=sample_wagons,
        rejected_wagons=[],
        workshops=[],
    )

    assert result.throughput.total_wagons_processed == 4
    assert result.throughput.total_wagons_retrofitted == 4
    assert result.throughput.total_wagons_rejected == 0
    assert result.throughput.simulation_duration_hours == 24.0


def test_calculate_throughput_with_rejections(
    sample_scenario: Scenario, sample_wagons: list[Wagon], sample_metrics: dict
) -> None:
    """Test throughput calculation with rejected wagons."""
    calculator = KPICalculator()
    rejected = [
        Wagon(
            wagon_id='W999',
            length=15.0,
            is_loaded=True,
            needs_retrofit=True,
            track_id='T001',
            status=WagonStatus.REJECTED,
        ),
    ]

    result = calculator.calculate_from_simulation(
        metrics=sample_metrics,
        scenario=sample_scenario,
        wagons=sample_wagons,
        rejected_wagons=rejected,
        workshops=[],
    )

    assert result.throughput.total_wagons_rejected == 1


def test_calculate_wagons_per_hour(sample_scenario: Scenario, sample_wagons: list[Wagon], sample_metrics: dict) -> None:
    """Test wagons per hour calculation."""
    calculator = KPICalculator()

    result = calculator.calculate_from_simulation(
        metrics=sample_metrics,
        scenario=sample_scenario,
        wagons=sample_wagons,
        rejected_wagons=[],
        workshops=[],
    )

    expected_per_hour = 4 / 24.0
    assert result.throughput.wagons_per_hour == round(expected_per_hour, 2)
    assert result.throughput.wagons_per_day == round(expected_per_hour * 24, 2)


def test_calculate_utilization(
    sample_scenario: Scenario, sample_wagons: list[Wagon], sample_workshops: list[Workshop], sample_metrics: dict
) -> None:
    """Test utilization calculation."""
    calculator = KPICalculator()

    result = calculator.calculate_from_simulation(
        metrics=sample_metrics,
        scenario=sample_scenario,
        wagons=sample_wagons,
        rejected_wagons=[],
        workshops=sample_workshops,
    )

    assert len(result.utilization) == 2
    assert result.utilization[0].workshop_id == 'WS001'
    assert result.utilization[1].workshop_id == 'WS002'
    assert result.utilization[0].total_capacity == 10
    assert result.utilization[1].total_capacity == 8


def test_identify_bottleneck_high_rejection(sample_scenario: Scenario, sample_metrics: dict) -> None:
    """Test bottleneck identification for high rejection rate."""
    calculator = KPICalculator()
    wagons = [
        Wagon(
            wagon_id=f'W{i:03d}',
            length=15.0,
            is_loaded=True,
            needs_retrofit=True,
            track_id='T001',
            status=WagonStatus.RETROFITTED,
        )
        for i in range(10)
    ]
    rejected = [
        Wagon(
            wagon_id=f'W{i:03d}',
            length=15.0,
            is_loaded=True,
            needs_retrofit=True,
            track_id='T001',
            status=WagonStatus.REJECTED,
        )
        for i in range(10, 13)
    ]

    result = calculator.calculate_from_simulation(
        metrics=sample_metrics,
        scenario=sample_scenario,
        wagons=wagons,
        rejected_wagons=rejected,
        workshops=[],
    )

    rejection_bottlenecks = [b for b in result.bottlenecks if 'rejection' in b.description.lower()]
    assert len(rejection_bottlenecks) > 0


def test_identify_bottleneck_high_utilization(sample_scenario: Scenario, sample_metrics: dict) -> None:
    """Test bottleneck identification for high utilization."""
    calculator = KPICalculator()
    workshop = Workshop(
        workshop_id='WS001',
        track_id='T001',
        start_date='2025-01-01T00:00:00',
        end_date='2025-01-02T00:00:00',
        retrofit_stations=1,
        worker=1,
    )
    wagons = [
        Wagon(
            wagon_id=f'W{i:03d}',
            length=15.0,
            is_loaded=True,
            needs_retrofit=True,
            track_id='T001',
            status=WagonStatus.RETROFITTED,
        )
        for i in range(100)
    ]

    result = calculator.calculate_from_simulation(
        metrics=sample_metrics,
        scenario=sample_scenario,
        wagons=wagons,
        rejected_wagons=[],
        workshops=[workshop],
    )

    workshop_bottlenecks = [b for b in result.bottlenecks if b.type == 'workshop']
    assert len(workshop_bottlenecks) > 0


def test_avg_flow_time_from_metrics(
    sample_scenario: Scenario, sample_wagons: list[Wagon], sample_metrics: dict
) -> None:
    """Test average flow time extraction from metrics."""
    calculator = KPICalculator()

    result = calculator.calculate_from_simulation(
        metrics=sample_metrics,
        scenario=sample_scenario,
        wagons=sample_wagons,
        rejected_wagons=[],
        workshops=[],
    )

    assert result.avg_flow_time_minutes == 45.5


def test_avg_waiting_time_calculation(sample_scenario: Scenario, sample_metrics: dict) -> None:
    """Test average waiting time calculation."""
    calculator = KPICalculator()
    base_time = datetime(2025, 1, 1, 0, 0, tzinfo=UTC).timestamp()
    wagons = [
        Wagon(
            wagon_id='W001',
            length=15.0,
            is_loaded=True,
            needs_retrofit=True,
            track_id='T001',
            status=WagonStatus.RETROFITTED,
            arrival_time=datetime(2025, 1, 1, 0, 0, tzinfo=UTC),
            retrofit_start_time=base_time + 600.0,
        ),
        Wagon(
            wagon_id='W002',
            length=15.0,
            is_loaded=True,
            needs_retrofit=True,
            track_id='T001',
            status=WagonStatus.RETROFITTED,
            arrival_time=datetime(2025, 1, 1, 0, 0, tzinfo=UTC),
            retrofit_start_time=base_time + 900.0,
        ),
        Wagon(
            wagon_id='W003',
            length=15.0,
            is_loaded=True,
            needs_retrofit=True,
            track_id='T002',
            status=WagonStatus.RETROFITTED,
            arrival_time=datetime(2025, 1, 1, 0, 0, tzinfo=UTC),
            retrofit_start_time=base_time + 1200.0,
        ),
        Wagon(
            wagon_id='W004',
            length=15.0,
            is_loaded=True,
            needs_retrofit=True,
            track_id='T002',
            status=WagonStatus.RETROFITTED,
            arrival_time=datetime(2025, 1, 1, 0, 0, tzinfo=UTC),
            retrofit_start_time=base_time + 300.0,
        ),
    ]

    result = calculator.calculate_from_simulation(
        metrics=sample_metrics,
        scenario=sample_scenario,
        wagons=wagons,
        rejected_wagons=[],
        workshops=[],
    )

    expected_avg = (600.0 + 900.0 + 1200.0 + 300.0) / 4 / 60.0
    assert result.avg_waiting_time_minutes == round(expected_avg, 1)


def test_no_wagons_scenario(sample_scenario: Scenario, sample_metrics: dict) -> None:
    """Test KPI calculation with no wagons."""
    calculator = KPICalculator()

    result = calculator.calculate_from_simulation(
        metrics=sample_metrics,
        scenario=sample_scenario,
        wagons=[],
        rejected_wagons=[],
        workshops=[],
    )

    assert result.throughput.total_wagons_processed == 0
    assert result.throughput.total_wagons_retrofitted == 0
    assert result.throughput.wagons_per_hour == 0.0


def test_no_workshops_scenario(sample_scenario: Scenario, sample_wagons: list[Wagon], sample_metrics: dict) -> None:
    """Test KPI calculation with no workshops."""
    calculator = KPICalculator()

    result = calculator.calculate_from_simulation(
        metrics=sample_metrics,
        scenario=sample_scenario,
        wagons=sample_wagons,
        rejected_wagons=[],
        workshops=[],
    )

    assert len(result.utilization) == 0


def test_empty_metrics(sample_scenario: Scenario, sample_wagons: list[Wagon]) -> None:
    """Test KPI calculation with empty metrics."""
    calculator = KPICalculator()

    result = calculator.calculate_from_simulation(
        metrics={},
        scenario=sample_scenario,
        wagons=sample_wagons,
        rejected_wagons=[],
        workshops=[],
    )

    assert result.avg_flow_time_minutes == 0.0


def test_wagons_without_waiting_time(sample_scenario: Scenario, sample_metrics: dict) -> None:
    """Test average waiting time with wagons that have no waiting time."""
    calculator = KPICalculator()
    wagons = [
        Wagon(
            wagon_id='W001',
            length=15.0,
            is_loaded=True,
            needs_retrofit=True,
            track_id='T001',
            status=WagonStatus.RETROFITTED,
        ),
        Wagon(
            wagon_id='W002',
            length=15.0,
            is_loaded=True,
            needs_retrofit=True,
            track_id='T001',
            status=WagonStatus.RETROFITTED,
        ),
    ]

    result = calculator.calculate_from_simulation(
        metrics=sample_metrics,
        scenario=sample_scenario,
        wagons=wagons,
        rejected_wagons=[],
        workshops=[],
    )

    assert result.avg_waiting_time_minutes == 0.0


def test_scenario_id_in_result(sample_scenario: Scenario, sample_wagons: list[Wagon], sample_metrics: dict) -> None:
    """Test that scenario ID is included in result."""
    calculator = KPICalculator()

    result = calculator.calculate_from_simulation(
        metrics=sample_metrics,
        scenario=sample_scenario,
        wagons=sample_wagons,
        rejected_wagons=[],
        workshops=[],
    )

    assert result.scenario_id == 'TEST_SCENARIO'


def test_bottleneck_severity_levels(sample_scenario: Scenario, sample_metrics: dict) -> None:
    """Test different bottleneck severity levels."""
    calculator = KPICalculator()
    wagons = [
        Wagon(
            wagon_id=f'W{i:03d}',
            length=15.0,
            is_loaded=True,
            needs_retrofit=True,
            track_id='T001',
            status=WagonStatus.RETROFITTED,
        )
        for i in range(10)
    ]
    rejected = [
        Wagon(
            wagon_id=f'W{i:03d}',
            length=15.0,
            is_loaded=True,
            needs_retrofit=True,
            track_id='T001',
            status=WagonStatus.REJECTED,
        )
        for i in range(10, 13)
    ]

    result = calculator.calculate_from_simulation(
        metrics=sample_metrics,
        scenario=sample_scenario,
        wagons=wagons,
        rejected_wagons=rejected,
        workshops=[],
    )

    if result.bottlenecks:
        assert all(b.severity in ['low', 'medium', 'high', 'critical'] for b in result.bottlenecks)


def test_utilization_capped_at_100(sample_scenario: Scenario, sample_metrics: dict) -> None:
    """Test that utilization is capped at 100%."""
    calculator = KPICalculator()
    workshop = Workshop(
        workshop_id='WS001',
        track_id='T001',
        start_date='2025-01-01T00:00:00',
        end_date='2025-01-02T00:00:00',
        retrofit_stations=1,
        worker=1,
    )
    wagons = [
        Wagon(
            wagon_id=f'W{i:03d}',
            length=15.0,
            is_loaded=True,
            needs_retrofit=True,
            track_id='T001',
            status=WagonStatus.RETROFITTED,
        )
        for i in range(1000)
    ]

    result = calculator.calculate_from_simulation(
        metrics=sample_metrics,
        scenario=sample_scenario,
        wagons=wagons,
        rejected_wagons=[],
        workshops=[workshop],
    )

    assert all(u.average_utilization_percent <= 100.0 for u in result.utilization)
    assert all(u.peak_utilization_percent <= 100.0 for u in result.utilization)
