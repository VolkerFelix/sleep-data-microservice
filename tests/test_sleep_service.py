import os
import sys
from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest

from app.services.sleep_service import SleepDataService

# Add the application to the python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class TestSleepDataService:
    """Tests for the SleepDataService class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_storage = MagicMock()
        self.service = SleepDataService(storage_service=self.mock_storage)

        # Test data
        self.user_id = "test_user"
        self.start_date = datetime.now() - timedelta(days=7)
        self.end_date = datetime.now()

    def test_generate_dummy_data(self):
        """Test generating dummy sleep data."""
        # Test with default parameters
        sleep_data = self.service.generate_dummy_data(
            user_id=self.user_id, start_date=self.start_date, end_date=self.end_date
        )

        # Verify basic structure and data
        assert len(sleep_data) == 8  # 7 days + today

        for record in sleep_data:
            assert record["user_id"] == self.user_id
            assert "date" in record
            assert "sleep_start" in record
            assert "sleep_end" in record
            assert "duration_minutes" in record
            assert "sleep_phases" in record
            assert "sleep_quality" in record
            assert "heart_rate" in record
            assert "metadata" in record

    def test_generate_dummy_data_with_time_series(self):
        """Test generating dummy sleep data with time series data."""
        sleep_data = self.service.generate_dummy_data(
            user_id=self.user_id,
            start_date=self.start_date,
            end_date=self.start_date,  # Just one day
            include_time_series=True,
        )

        assert len(sleep_data) == 1
        record = sleep_data[0]

        assert "time_series" in record
        assert len(record["time_series"]) > 0

        # Check time series data structure
        ts_entry = record["time_series"][0]
        assert "timestamp" in ts_entry
        assert "stage" in ts_entry
        assert "heart_rate" in ts_entry
        assert "movement" in ts_entry
        assert "respiration_rate" in ts_entry

    def test_generate_with_trends(self):
        """Test generating dummy data with specific trends."""
        # Test improving sleep quality trend
        sleep_data = self.service.generate_dummy_data(
            user_id=self.user_id,
            start_date=self.start_date,
            end_date=self.end_date,
            sleep_quality_trend="improving",
        )

        # First day's quality should be lower than last day's
        first_day_quality = sleep_data[0]["sleep_quality"]
        last_day_quality = sleep_data[-1]["sleep_quality"]

        assert last_day_quality > first_day_quality

        # Test decreasing sleep duration trend
        sleep_data = self.service.generate_dummy_data(
            user_id=self.user_id,
            start_date=self.start_date,
            end_date=self.end_date,
            sleep_duration_trend="decreasing",
        )

        first_day_duration = sleep_data[0]["duration_minutes"]
        last_day_duration = sleep_data[-1]["duration_minutes"]

        assert last_day_duration < first_day_duration

    def test_storage_integration(self):
        """Test that generated data is saved to storage if available."""
        sleep_data = self.service.generate_dummy_data(
            user_id=self.user_id,
            start_date=self.start_date,
            end_date=self.start_date,  # Just one day
        )

        # Verify storage service was called
        self.mock_storage.save_sleep_records.assert_called_once_with(
            self.user_id, sleep_data
        )

    def test_get_sleep_data(self):
        """Test retrieving sleep data from storage."""
        # Setup mock
        mock_records = [{"id": "123", "user_id": self.user_id}]
        self.mock_storage.get_sleep_records.return_value = mock_records

        # Call method
        result = self.service.get_sleep_data(
            user_id=self.user_id, start_date=self.start_date, end_date=self.end_date
        )

        # Verify result
        assert result == mock_records
        self.mock_storage.get_sleep_records.assert_called_once_with(
            user_id=self.user_id,
            start_date=self.start_date,
            end_date=self.end_date,
            limit=100,
            offset=0,
        )

    def test_get_sleep_data_no_storage(self):
        """Test that error is raised when trying to get data without storage service."""
        # Create service without storage
        service = SleepDataService()

        # Verify error
        with pytest.raises(ValueError) as excinfo:
            service.get_sleep_data(user_id=self.user_id)

        assert "Storage service is required" in str(excinfo.value)

    def test_calculate_sleep_trends(self):
        """Test calculating sleep trends from records."""
        # Create sample records with consistent sleep schedule

        trends = self.service._calculate_trend([420, 430, 440])
        assert trends > 0  # Positive trend (increasing)

        consistency = self.service._calculate_consistency(
            [1380, 1385, 1390]
        )  # Minutes past midnight
        assert consistency < 30  # Fairly consistent times
