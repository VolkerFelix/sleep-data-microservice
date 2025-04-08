"""Tests for FileStorage implementation."""
import os
import sys
from copy import deepcopy
from datetime import datetime, timedelta

# Add the application to the python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class TestFileStorage:
    """Tests for the FileStorage class."""

    def test_save_and_retrieve_records(self, file_storage, sample_sleep_record):
        """Test saving and retrieving sleep records."""
        user_id = "test_user"

        # Make a copy of the sample record to avoid modifying the fixture
        record = deepcopy(sample_sleep_record)

        # Save the record
        result = file_storage.save_sleep_records(user_id, [record])
        assert result is True

        # Retrieve records
        records = file_storage.get_sleep_records(user_id)

        # Verify
        assert len(records) == 1
        assert records[0]["id"] == record["id"]
        assert records[0]["user_id"] == user_id
        assert records[0]["sleep_quality"] == 85

    def test_save_with_time_series(self, file_storage):
        """Test saving records with time series data."""
        user_id = "test_user"

        # Create a record with time series data
        record = {
            "id": "test-ts-record",
            "user_id": user_id,
            "date": "2023-05-20",
            "sleep_start": "2023-05-20T23:00:00",
            "sleep_end": "2023-05-21T07:00:00",
            "duration_minutes": 480,
            "meta_data": {"source": "test"},
            "time_series": [
                {
                    "timestamp": "2023-05-20T23:30:00",
                    "stage": "light",
                    "heart_rate": 65,
                },
                {"timestamp": "2023-05-21T01:30:00", "stage": "deep", "heart_rate": 55},
            ],
        }

        # Save the record
        result = file_storage.save_sleep_records(user_id, [record])
        assert result is True

        # Retrieve the record
        records = file_storage.get_sleep_records(user_id)

        # Verify
        assert len(records) == 1
        assert "time_series" in records[0]
        assert len(records[0]["time_series"]) == 2
        assert records[0]["time_series"][0]["stage"] == "light"
        assert records[0]["time_series"][1]["heart_rate"] == 55

    def test_date_filtering(self, file_storage):
        """Test filtering by date range."""
        user_id = "test_user"

        # Create records with different dates
        records = [
            {
                "id": f"test-record-{i}",
                "user_id": user_id,
                "date": (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d"),
                "sleep_start": f"2023-05-{20-i}T23:00:00",
                "sleep_end": f"2023-05-{21-i}T07:00:00",
                "duration_minutes": 480,
                "meta_data": {"source": "test"},
            }
            for i in range(10)  # Create 10 records
        ]

        # Save the records
        result = file_storage.save_sleep_records(user_id, records)
        assert result is True

        # Get all records
        all_records = file_storage.get_sleep_records(user_id)
        assert len(all_records) == 10

        # Filter by start date
        start_date = datetime.now() - timedelta(days=5)
        filtered_records = file_storage.get_sleep_records(
            user_id, start_date=start_date
        )
        assert len(filtered_records) == 6  # Today + 5 days

        # Filter by end date
        end_date = datetime.now() - timedelta(days=8)
        filtered_records = file_storage.get_sleep_records(user_id, end_date=end_date)
        assert len(filtered_records) == 2  # Days 8 and 9

        # Filter by date range
        filtered_records = file_storage.get_sleep_records(
            user_id,
            start_date=datetime.now() - timedelta(days=7),
            end_date=datetime.now() - timedelta(days=3),
        )
        assert len(filtered_records) == 5  # Days 3, 4, 5, 6, 7

    def test_pagination(self, file_storage):
        """Test paginating results."""
        user_id = "test_user"

        # Create 20 records
        records = [
            {
                "id": f"test-record-{i}",
                "user_id": user_id,
                "date": f"2023-05-{i+1:02d}",
                "sleep_start": f"2023-05-{i+1:02d}T23:00:00",
                "sleep_end": f"2023-05-{i+2:02d}T07:00:00",
                "duration_minutes": 480,
                "meta_data": {"source": "test"},
            }
            for i in range(20)
        ]

        # Save the records
        result = file_storage.save_sleep_records(user_id, records)
        assert result is True

        # Test limit
        limited_records = file_storage.get_sleep_records(user_id, limit=5)
        assert len(limited_records) == 5

        # Test offset
        offset_records = file_storage.get_sleep_records(user_id, offset=15)
        assert len(offset_records) == 5  # 20 total - 15 offset

        # Test limit and offset
        paginated_records = file_storage.get_sleep_records(user_id, limit=5, offset=10)
        assert len(paginated_records) == 5
        # Records should be sorted by date (descending)
        assert paginated_records[0]["date"] > paginated_records[-1]["date"]

    def test_delete_record(self, file_storage, sample_sleep_record):
        """Test deleting a sleep record."""
        user_id = "test_user"

        # Save a record
        record = deepcopy(sample_sleep_record)
        file_storage.save_sleep_records(user_id, [record])

        # Verify it exists
        records = file_storage.get_sleep_records(user_id)
        assert len(records) == 1

        # Delete the record
        result = file_storage.delete_sleep_record(user_id, record["id"])
        assert result is True

        # Verify it's gone
        records = file_storage.get_sleep_records(user_id)
        assert len(records) == 0

        # Attempt to delete non-existent record
        result = file_storage.delete_sleep_record(user_id, "non-existent-id")
        assert result is False
