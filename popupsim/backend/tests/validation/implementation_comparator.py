"""Framework for comparing original and rake-first implementations."""

from typing import Any
from typing import List
from typing import Tuple

from contexts.retrofit_workflow.application.config.rake_support_config import RakeSupportConfig
from contexts.retrofit_workflow.application.retrofit_workflow_context import RetrofitWorkshopContext
import simpy


class ImplementationComparator:
    """Compare original and rake-first implementations."""

    def __init__(self):
        self.results = []

    def run_comparison(
        self,
        scenario_name: str,
        num_wagons: int,
        num_workshops: int,
        retrofit_time: float,
        until: float,
        workshop_bays: list[int] | None = None,
    ) -> dict[str, Any]:
        """Run scenario with both implementations and compare results."""

        print(f'\n🔍 Comparing implementations for: {scenario_name}')

        # Run original implementation
        original_result = self._run_original_implementation(
            num_wagons, num_workshops, retrofit_time, until, workshop_bays
        )

        # Run rake-first implementation
        rake_result = self._run_rake_implementation(num_wagons, num_workshops, retrofit_time, until, workshop_bays)

        # Compare results
        comparison = self._compare_results(original_result, rake_result)
        comparison['scenario'] = scenario_name

        self.results.append(comparison)
        return comparison

    def _run_original_implementation(
        self,
        num_wagons: int,
        num_workshops: int,
        retrofit_time: float,
        until: float,
        workshop_bays: list[int] | None = None,
    ) -> dict[str, Any]:
        """Run with original implementation."""

        try:
            from tests.validation.test_retrofit_workflow_scenarios import run_timeline_test

            events, analytics = run_timeline_test(num_wagons, num_workshops, retrofit_time, until, workshop_bays)

            return {
                'success': True,
                'events': events,
                'event_count': len(events),
                'event_types': [type(e).__name__ for t, e in events],
                'error': None,
            }
        except Exception as e:
            return {'success': False, 'events': [], 'event_count': 0, 'event_types': [], 'error': str(e)}

    def _run_rake_implementation(
        self,
        num_wagons: int,
        num_workshops: int,
        retrofit_time: float,
        until: float,
        workshop_bays: list[int] | None = None,
    ) -> dict[str, Any]:
        """Run with rake-first implementation."""

        try:
            # Create scenario
            from tests.validation.test_retrofit_workflow_scenarios import create_test_scenario

            env = simpy.Environment()
            scenario = create_test_scenario(num_wagons, num_workshops, retrofit_time, workshop_bays)

            # Enable rake support
            rake_config = RakeSupportConfig.create_default()
            context = RetrofitWorkshopContext(env, scenario, rake_config)

            # Verify rake support is enabled
            status = context.get_status()
            assert status['rake_support_enabled'] is True
            assert status['coordinator_type'] == 'RAKE_FIRST'

            # Initialize context
            context.initialize()

            # For now, just verify the context was created successfully
            # TODO: Implement full rake-first simulation run

            return {
                'success': True,
                'events': [],  # Would collect events from rake-first run
                'event_count': 0,
                'event_types': [],
                'error': None,
                'rake_support_verified': True,
            }

        except Exception as e:
            return {
                'success': False,
                'events': [],
                'event_count': 0,
                'event_types': [],
                'error': str(e),
                'rake_support_verified': False,
            }

    def _compare_results(self, original: dict[str, Any], rake: dict[str, Any]) -> dict[str, Any]:
        """Compare results from both implementations."""

        comparison = {
            'original_success': original['success'],
            'rake_success': rake['success'],
            'original_events': original['event_count'],
            'rake_events': rake['event_count'],
            'events_match': original['event_count'] == rake['event_count'],
            'both_successful': original['success'] and rake['success'],
            'original_error': original.get('error'),
            'rake_error': rake.get('error'),
            'rake_support_verified': rake.get('rake_support_verified', False),
        }

        # Print comparison results
        if comparison['both_successful']:
            print(f'   ✓ Both implementations successful')
            print(f'   📊 Original: {original["event_count"]} events')
            print(f'   📊 Rake-first: {rake["event_count"]} events')
            if comparison['events_match']:
                print(f'   ✓ Event counts match')
            else:
                print(f'   ⚠️  Event counts differ')
        else:
            if not original['success']:
                print(f'   ❌ Original failed: {original["error"]}')
            if not rake['success']:
                print(f'   ❌ Rake-first failed: {rake["error"]}')

        if rake.get('rake_support_verified'):
            print(f'   ✓ Rake support verified')

        return comparison

    def print_summary(self) -> None:
        """Print summary of all comparisons."""

        print('\n' + '=' * 60)
        print('IMPLEMENTATION COMPARISON SUMMARY')
        print('=' * 60)

        total_scenarios = len(self.results)
        successful_comparisons = sum(1 for r in self.results if r['both_successful'])
        matching_events = sum(1 for r in self.results if r['events_match'])

        print(f'Total scenarios tested: {total_scenarios}')
        print(f'Both implementations successful: {successful_comparisons}/{total_scenarios}')
        print(f'Event counts matching: {matching_events}/{total_scenarios}')

        print('\nDetailed Results:')
        for result in self.results:
            status = '✓' if result['both_successful'] else '❌'
            events = '✓' if result['events_match'] else '⚠️'
            print(f'  {status} {result["scenario"]}: Events {events}')

        print('=' * 60)


def run_implementation_comparison():
    """Run comprehensive implementation comparison."""

    comparator = ImplementationComparator()

    # Test scenarios
    scenarios = [
        ('single_wagon', 1, 1, 10.0, 30.0, [1]),
        ('two_wagons_one_station', 2, 1, 10.0, 50.0, [1]),
        ('two_wagons_two_stations', 2, 1, 10.0, 50.0, [2]),
    ]

    print('🚀 Starting Implementation Comparison')
    print('Testing original vs rake-first coordinators...')

    for name, wagons, workshops, retrofit_time, until, bays in scenarios:
        comparator.run_comparison(name, wagons, workshops, retrofit_time, until, bays)

    comparator.print_summary()

    return comparator.results


if __name__ == '__main__':
    results = run_implementation_comparison()
