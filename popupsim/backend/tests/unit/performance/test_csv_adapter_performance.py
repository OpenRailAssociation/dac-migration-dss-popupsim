"""Performance benchmark for CSV adapter train processing."""

from typing import Any

import pandas as pd
import pytest


def create_test_data(num_trains: int, wagons_per_train: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Create test DataFrames for benchmarking."""
    trains_data = [
        {
            'id': f'T{i}',
            'arrival_time': f'2024-01-01 {i:02d}:00:00',
            'departure_time': f'2024-01-01 {i + 1:02d}:00:00',
            'locomotive_id': f'L{i}',
            'route_id': f'R{i}',
        }
        for i in range(num_trains)
    ]

    wagons_data = [
        {
            'train_id': f'T{i}',
            'wagon_id': f'W{i}_{j}',
            'id': f'W{i}_{j}',
            'length': 14.5 + j,
            'is_loaded': j % 2 == 0,
            'needs_retrofit': True,
            'track': 'ABC_D',
        }
        for i in range(num_trains)
        for j in range(wagons_per_train)
    ]

    return pd.DataFrame(trains_data), pd.DataFrame(wagons_data)


def process_trains_original(trains_df: pd.DataFrame, wagons_df: pd.DataFrame) -> list[dict[str, Any]]:
    """Original implementation using iterrows() - O(n*m)."""
    trains = []
    for _, train_row in trains_df.iterrows():
        train_wagons = wagons_df[wagons_df['train_id'] == train_row['id']]
        wagon_dtos = [
            {
                'id': str(wagon_row['wagon_id']),
                'length': float(wagon_row['length']),
                'is_loaded': bool(wagon_row.get('is_loaded', False)),
                'needs_retrofit': bool(wagon_row.get('needs_retrofit', True)),
                'track': wagon_row.get('track'),
            }
            for _, wagon_row in train_wagons.iterrows()
        ]

        trains.append(
            {
                'train_id': str(train_row['id']),
                'arrival_time': str(train_row['arrival_time']),
                'departure_time': str(train_row['departure_time']),
                'locomotive_id': str(train_row.get('locomotive_id', '')),
                'route_id': str(train_row.get('route_id', '')),
                'wagons': wagon_dtos,
            }
        )
    return trains


def process_trains_dict(trains_df: pd.DataFrame, wagons_df: pd.DataFrame) -> list[dict[str, Any]]:
    """Optimized implementation using dict grouping - O(n+m)."""
    trains_dict = trains_df.to_dict('records')
    wagons_dict = wagons_df.to_dict('records')

    wagons_by_train: dict[str, list[dict]] = {}
    for wagon in wagons_dict:
        train_id = str(wagon['train_id'])
        wagons_by_train.setdefault(train_id, []).append(wagon)

    trains = []
    for train_row in trains_dict:
        train_id = str(train_row['id'])
        wagon_dtos = [
            {
                'id': str(w['wagon_id']),
                'length': float(w['length']),
                'is_loaded': bool(w.get('is_loaded', False)),
                'needs_retrofit': bool(w.get('needs_retrofit', True)),
                'track': w.get('track'),
            }
            for w in wagons_by_train.get(train_id, [])
        ]

        trains.append(
            {
                'train_id': train_id,
                'arrival_time': str(train_row['arrival_time']),
                'departure_time': str(train_row['departure_time']),
                'locomotive_id': str(train_row.get('locomotive_id', '')),
                'route_id': str(train_row.get('route_id', '')),
                'wagons': wagon_dtos,
            }
        )
    return trains


def process_trains_groupby(trains_df: pd.DataFrame, wagons_df: pd.DataFrame) -> list[dict[str, Any]]:
    """Pandas groupby implementation - O(n+m) with pandas overhead."""
    wagons_grouped = wagons_df.groupby('train_id')

    trains = []
    for train_dict in trains_df.to_dict('records'):
        train_id = str(train_dict['id'])
        try:
            train_wagons = wagons_grouped.get_group(train_id)
            wagon_dtos = [
                {
                    'id': str(w['wagon_id']),
                    'length': float(w['length']),
                    'is_loaded': bool(w.get('is_loaded', False)),
                    'needs_retrofit': bool(w.get('needs_retrofit', True)),
                    'track': w.get('track'),
                }
                for w in train_wagons.to_dict('records')
            ]
        except KeyError:
            wagon_dtos = []

        trains.append(
            {
                'train_id': train_id,
                'arrival_time': str(train_dict['arrival_time']),
                'departure_time': str(train_dict['departure_time']),
                'locomotive_id': str(train_dict.get('locomotive_id', '')),
                'route_id': str(train_dict.get('route_id', '')),
                'wagons': wagon_dtos,
            }
        )
    return trains


@pytest.mark.benchmark(group='original')
@pytest.mark.parametrize('num_trains,wagons_per_train', [(2, 10), (4, 40), (10, 50)])
def test_original_implementation(benchmark: Any, num_trains: int, wagons_per_train: int) -> None:
    """Benchmark original O(n*m) implementation."""
    trains_df, wagons_df = create_test_data(num_trains, wagons_per_train)
    result = benchmark(process_trains_original, trains_df, wagons_df)
    assert len(result) == num_trains
    assert len(result[0]['wagons']) == wagons_per_train


@pytest.mark.benchmark(group='dict-grouping')
@pytest.mark.parametrize('num_trains,wagons_per_train', [(2, 10), (4, 40), (10, 50)])
def test_dict_implementation(benchmark: Any, num_trains: int, wagons_per_train: int) -> None:
    """Benchmark dict grouping O(n+m) implementation."""
    trains_df, wagons_df = create_test_data(num_trains, wagons_per_train)
    result = benchmark(process_trains_dict, trains_df, wagons_df)
    assert len(result) == num_trains
    assert len(result[0]['wagons']) == wagons_per_train


@pytest.mark.benchmark(group='pandas-groupby')
@pytest.mark.parametrize('num_trains,wagons_per_train', [(2, 10), (4, 40), (10, 50)])
def test_groupby_implementation(benchmark: Any, num_trains: int, wagons_per_train: int) -> None:
    """Benchmark pandas groupby O(n+m) implementation."""
    trains_df, wagons_df = create_test_data(num_trains, wagons_per_train)
    result = benchmark(process_trains_groupby, trains_df, wagons_df)
    assert len(result) == num_trains
    assert len(result[0]['wagons']) == wagons_per_train


def test_correctness_comparison() -> None:
    """Verify all implementations produce identical results."""
    trains_df, wagons_df = create_test_data(5, 10)

    result_original = process_trains_original(trains_df, wagons_df)
    result_dict = process_trains_dict(trains_df, wagons_df)
    result_groupby = process_trains_groupby(trains_df, wagons_df)

    assert len(result_original) == len(result_dict) == len(result_groupby)

    for i in range(len(result_original)):
        assert result_original[i]['train_id'] == result_dict[i]['train_id'] == result_groupby[i]['train_id']
        assert len(result_original[i]['wagons']) == len(result_dict[i]['wagons']) == len(result_groupby[i]['wagons'])


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--benchmark-only', '--no-cov'])
