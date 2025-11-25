"""Builder for creating Train instances from CSV schedule data."""

from datetime import datetime
import logging
from pathlib import Path

import pandas as pd

from configuration.domain.models.train import TRAIN_DEFAULT_ID
from configuration.domain.models.train import Train
from configuration.domain.models.wagon import Wagon

logger = logging.getLogger(__name__)


class TrainListParser:
    """Builder class for creating lists of Train instances from CSV data."""

    def __init__(self, schedule_path: Path) -> None:
        """Initialize the builder with a schedule file path.

        Parameters
        ----------
        schedule_path : Path
            Path to the CSV file containing train schedule data.
        """
        self.schedule_path: Path = schedule_path
        self.trains: list[Train] = []

    def add_train(self, train: Train) -> None:
        """Add a Train instance to the list.

        Parameters
        ----------
        train : Train
            The Train instance to be added.
        """
        self.trains.append(train)

    def _load_csv(self) -> pd.DataFrame:
        """Load and validate CSV file.

        Returns
        -------
        pd.DataFrame
            Loaded schedule data.

        Raises
        ------
        FileNotFoundError
            If the schedule file does not exist.
        ValueError
            If CSV parsing fails.
        """
        if not self.schedule_path.exists():
            raise FileNotFoundError(f'Schedule file not found: {self.schedule_path}')

        try:
            df: pd.DataFrame = pd.read_csv(self.schedule_path, sep=';', parse_dates=['arrival_time'])
            # Fill empty train_id with TRAIN_DEFAULT_ID
            df['train_id'] = df['train_id'].fillna(TRAIN_DEFAULT_ID).astype(str)
            # Make sure arrival_time is datetime
            df['arrival_time'] = pd.to_datetime(df['arrival_time'], errors='coerce')
            return df
        except Exception as e:
            raise ValueError(f'Failed to parse CSV file: {e!s}') from e

    def _create_trains_from_dataframe(self, df: pd.DataFrame) -> list[Train]:
        """Create Train objects from DataFrame grouped by train_id.

        Parameters
        ----------
        df : pd.DataFrame
            DataFrame with train schedule data.

        Returns
        -------
        list[Train]
            List of Train objects with wagons.

        Raises
        ------
        ValueError
            If train creation fails.
        """
        trains: list[Train] = []

        for train_id, group in df.groupby('train_id'):
            try:
                # Get latest arrival time for the train
                latest_arrival: pd.Timestamp = group['arrival_time'].max()
                arrival_time: datetime = latest_arrival.to_pydatetime()

                # Create wagons
                wagons: list[Wagon] = [
                    Wagon(
                        wagon_id=str(row['wagon_id']),
                        length=float(row['length']),
                        is_loaded=bool(row['is_loaded']),
                        needs_retrofit=bool(row['needs_retrofit']),
                        train_id=str(train_id),
                    )
                    for _, row in group.iterrows()
                ]

                train: Train = Train(
                    train_id=str(train_id),
                    arrival_time=arrival_time,
                    wagons=wagons,
                )
                trains.append(train)
                logger.debug('Created train %s with %d wagons, arrival: %s', train_id, len(wagons), arrival_time)

            except Exception as e:
                raise ValueError(f'Failed to create train {train_id}: {e!s}') from e

        logger.info('Successfully created %d trains from CSV', len(trains))
        return trains

    def build(self) -> list[Train]:
        """Build and return list of Train instances.

        Returns
        -------
        list[Train]
            List of validated Train objects.

        Raises
        ------
        FileNotFoundError
            If schedule file not found.
        ValueError
            If CSV parsing or train creation fails.
        """
        df: pd.DataFrame = self._load_csv()
        self.trains = self._create_trains_from_dataframe(df)
        return self.trains
