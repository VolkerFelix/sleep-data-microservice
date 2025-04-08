import os
import sys
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Add the application to the python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Patch the DATABASE_URL setting BEFORE importing the app
with patch("app.config.settings.settings.DATABASE_URL", "sqlite:///:memory:"):
    from app.main import app
    from app.services.storage.factory import StorageFactory

# Create test client
client = TestClient(app)

# This ensures the patching is applied for all tests in this module
pytestmark = [pytest.mark.usefixtures("use_sqlite_db")]


@pytest.fixture(scope="module")
def use_sqlite_db():
    """Use SQLite for all database operations in this module."""
    with patch("app.config.settings.settings.DATABASE_URL", "sqlite:///:memory:"):
        # Initialize the memory database
        StorageFactory.create_storage_service("memory")
        yield


class TestAPI:
    """Tests for the API endpoints."""

    def test_root_endpoint(self):
        """Test the root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        assert "message" in response.json()
        assert "Sleep Data Microservice" in response.json()["message"]

    def test_health_check(self):
        """Test the health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

    @patch("app.api.sleep_routes.get_sleep_service")
    def test_generate_sleep_data(self, mock_get_service):
        """Test the generate sleep data endpoint."""
        # Setup mock
        mock_service = MagicMock()
        mock_service.generate_dummy_data.return_value = [
            {"id": "test1", "user_id": "user1", "date": "2023-05-01"}
        ]
        mock_get_service.return_value = mock_service

        # Make request
        payload = {
            "user_id": "user1",
            "start_date": "2023-05-01T00:00:00",
            "end_date": "2023-05-01T00:00:00",
            "include_time_series": False,
        }
        response = client.post("/api/sleep/generate", json=payload)

        # Verify response
        assert response.status_code == 201
        data = response.json()
        assert "records" in data
        assert "count" in data
        assert data["count"] == 1
        assert data["records"][0]["id"] == "test1"

        # Verify service was called
        mock_service.generate_dummy_data.assert_called_once()

    @patch("app.api.sleep_routes.get_sleep_service")
    def test_get_sleep_data(self, mock_get_service):
        """Test the get sleep data endpoint."""
        # Setup mock
        mock_service = MagicMock()
        mock_service.get_sleep_data.return_value = [
            {"id": "test1", "user_id": "user1", "date": "2023-05-01"}
        ]
        mock_get_service.return_value = mock_service

        # Make request
        response = client.get("/api/sleep/data?user_id=user1")

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert "records" in data
        assert "count" in data
        assert data["count"] == 1
        assert data["records"][0]["id"] == "test1"

        # Verify service was called
        mock_service.get_sleep_data.assert_called_once()

    @patch("app.api.sleep_routes.get_sleep_service")
    def test_analyze_sleep_data(self, mock_get_service):
        """Test the analyze sleep data endpoint."""
        # Setup mock
        mock_service = MagicMock()
        mock_service.analyze_sleep_data.return_value = {
            "user_id": "user1",
            "start_date": "2023-05-01",
            "end_date": "2023-05-07",
            "stats": {
                "average_duration_minutes": 420.0,
                "average_sleep_quality": 75.0,
                "total_records": 7,
                "date_range_days": 7,
            },
            "trends": {},
            "recommendations": ["Sample recommendation"],
        }
        mock_get_service.return_value = mock_service

        # Make request
        response = client.get(
            "/api/sleep/analytics?user_id=user1&start_date=2023-05-01T00:00:00&end_date=2023-05-07T00:00:00"
        )

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert "stats" in data
        assert data["user_id"] == "user1"

        # Verify service was called
        mock_service.analyze_sleep_data.assert_called_once()

    @patch("app.api.sleep_routes.get_storage_service")
    def test_create_sleep_record(self, mock_get_storage):
        """Test creating a sleep record."""
        # Setup mock
        mock_storage = MagicMock()
        mock_storage.save_sleep_records.return_value = True
        mock_get_storage.return_value = mock_storage

        # Make request
        payload = {
            "user_id": "user1",
            "date": "2023-05-01",
            "sleep_start": "2023-05-01T23:00:00",
            "sleep_end": "2023-05-02T07:00:00",
            "duration_minutes": 480,
            "sleep_quality": 85,
            "metadata": {"source": "manual", "imported_at": "2023-05-02T10:00:00"},
        }
        response = client.post("/api/sleep/records", json=payload)

        # Verify response
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["user_id"] == "user1"
        assert data["sleep_quality"] == 85

        # Verify storage was called
        mock_storage.save_sleep_records.assert_called_once()

    @patch("app.api.sleep_routes.get_storage_service")
    def test_update_sleep_record(self, mock_get_storage):
        """Test updating a sleep record."""
        # Setup mock
        mock_storage = MagicMock()
        mock_storage.get_sleep_records.return_value = [
            {
                "id": "test1",
                "user_id": "user1",
                "date": "2023-05-01",
                "sleep_start": "2023-05-01T23:00:00",
                "sleep_end": "2023-05-02T07:00:00",
                "duration_minutes": 480,
                "sleep_quality": 75,
            }
        ]
        mock_storage.save_sleep_records.return_value = True
        mock_get_storage.return_value = mock_storage

        # Make request
        payload = {"sleep_quality": 85}
        response = client.put("/api/sleep/records/test1?user_id=user1", json=payload)

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "test1"
        assert data["sleep_quality"] == 85  # Updated value

        # Verify storage was called
        mock_storage.get_sleep_records.assert_called_once()
        mock_storage.save_sleep_records.assert_called_once()

    @patch("app.api.sleep_routes.get_storage_service")
    def test_delete_sleep_record(self, mock_get_storage):
        """Test deleting a sleep record."""
        # Setup mock
        mock_storage = MagicMock()
        mock_storage.delete_sleep_record.return_value = True
        mock_get_storage.return_value = mock_storage

        # Make request
        response = client.delete("/api/sleep/records/test1?user_id=user1")

        # Verify response
        assert response.status_code == 204

        # Verify storage was called
        mock_storage.delete_sleep_record.assert_called_once_with("user1", "test1")
