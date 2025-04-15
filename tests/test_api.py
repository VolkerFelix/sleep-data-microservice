"""Test the API endpoints."""

import os
import uuid
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.main import app

os.environ["DATABASE_URL"] = "sqlite:///:memory:"


# Create a test client
client = TestClient(app)


@pytest.mark.usefixtures("use_sqlite_db")
class TestAPI:
    """Test the API endpoints."""

    def test_database_storage_directly(self):
        """Test the database storage directly to troubleshoot retrieval issues."""
        import uuid
        from datetime import datetime, timedelta

        from app.services.storage.db_storage import DatabaseStorage

        # Create a test record with a known ID and user ID
        test_user_id = f"direct_test_user_{uuid.uuid4()}"
        test_record_id = str(uuid.uuid4())

        # Create a database storage instance
        db_storage = DatabaseStorage()

        # Create a test sleep record
        test_record = {
            "id": test_record_id,
            "user_id": test_user_id,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "sleep_start": datetime.now().isoformat(),
            "sleep_end": (datetime.now() + timedelta(hours=8)).isoformat(),
            "duration_minutes": 480,
            "sleep_quality": 85,
            "meta_data": {"source": "test", "generated_at": datetime.now().isoformat()},
            "time_series": [],
        }

        # Directly save the record to the database
        save_success = db_storage.save_sleep_records(test_user_id, [test_record])
        assert save_success, "Failed to save record directly to database"

        # Directly retrieve the record from the database
        retrieved_records = db_storage.get_sleep_records(test_user_id)

        # Print diagnostic info
        print(
            f"""Retrieved {len(retrieved_records)} records
            directly from database for user {test_user_id}"""
        )
        if retrieved_records:
            print(f"First record: {retrieved_records[0]}")

        # Verify record was saved and retrieved correctly
        assert len(retrieved_records) > 0, "No records retrieved directly from database"
        assert (
            retrieved_records[0]["id"] == test_record_id
        ), "Retrieved record ID doesn't match test record ID"

    def test_storage_service_save_function(self):
        """Test the storage service save function directly."""
        import os
        import uuid
        from datetime import datetime, timedelta

        from app.services.storage.factory import StorageFactory

        # Create a test record
        test_user_id = f"storage_service_test_{uuid.uuid4()}"
        test_record = {
            "id": str(uuid.uuid4()),
            "user_id": test_user_id,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "sleep_start": datetime.now().isoformat(),
            "sleep_end": (datetime.now() + timedelta(hours=8)).isoformat(),
            "duration_minutes": 480,
            "sleep_quality": 85,
            "meta_data": {"source": "test", "generated_at": datetime.now().isoformat()},
            "time_series": [],
        }

        # Print current DATABASE_URL for debugging
        print(
            f"""Current DATABASE_URL:
            {os.environ.get('DATABASE_URL', 'Not set in environment')}"""
        )

        # Get storage service from factory
        storage_service = StorageFactory.create_storage_service()
        print(f"Storage service type: {type(storage_service).__name__}")

        # Save record
        save_result = storage_service.save_sleep_records(test_user_id, [test_record])
        print(f"Save result: {save_result}")

        # Retrieve record
        retrieved_records = storage_service.get_sleep_records(test_user_id)
        print(f"Retrieved {len(retrieved_records)} records")

        # Verify
        assert save_result, "Failed to save test record"
        assert len(retrieved_records) > 0, "No records retrieved after saving"

    def test_root_endpoint(self):
        """Test the root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Sleep Data Microservice" in data["message"]

    def test_health_check(self):
        """Test the health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

    def test_generate_sleep_data(self):
        """Test generating sleep data."""
        # Prepare the payload
        payload = {
            "user_id": "test_user",
            "start_date": (datetime.now() - timedelta(days=7)).isoformat(),
            "end_date": datetime.now().isoformat(),
            "include_time_series": False,
        }

        # Make the request
        response = client.post("/api/sleep/generate", json=payload)

        # Verify response
        assert response.status_code == 201
        data = response.json()

        # Verify response structure
        assert "records" in data
        assert "count" in data
        assert data["count"] > 0

        # Check first record
        record = data["records"][0]

        # Verify record has required fields
        assert "id" in record
        assert "user_id" in record
        assert record["user_id"] == "test_user"
        assert "date" in record
        assert "sleep_start" in record
        assert "sleep_end" in record
        assert "duration_minutes" in record

        # Verify meta_data
        assert "meta_data" in record
        meta_data = record["meta_data"]
        assert "source" in meta_data
        assert "generated_at" in meta_data

    def test_generate_sleep_data_with_time_series(self):
        """Test generating sleep data with time series."""
        # Prepare the payload
        payload = {
            "user_id": "time_series_user",
            "start_date": (datetime.now() - timedelta(days=1)).isoformat(),
            "end_date": datetime.now().isoformat(),
            "include_time_series": True,
            "sleep_quality_trend": "improving",
        }

        # Make the request
        response = client.post("/api/sleep/generate", json=payload)

        # Verify response
        assert response.status_code == 201
        data = response.json()

        # Verify response structure
        assert "records" in data
        assert "count" in data
        assert data["count"] > 0

        # Check first record
        record = data["records"][0]

        # Verify time series data when requested
        if "time_series" in record:
            assert len(record["time_series"]) > 0

            # Check time series point structure
            ts_point = record["time_series"][0]
            assert "timestamp" in ts_point
            assert "stage" in ts_point
            assert "heart_rate" in ts_point
            assert "movement" in ts_point
            assert "respiration_rate" in ts_point

    def test_create_sleep_record(self):
        """Test creating a sleep record."""
        # Prepare a sleep record payload
        current_time = datetime.now()
        payload = {
            "user_id": "create_test_user",
            "date": current_time.strftime("%Y-%m-%d"),
            "sleep_start": (current_time - timedelta(hours=8)).isoformat(),
            "sleep_end": current_time.isoformat(),
            "duration_minutes": 480,
            "sleep_quality": 85,
            "sleep_phases": None,
            "heart_rate": None,
            "breathing": None,
            "environment": None,
            "time_series": [],
            "tags": None,
            "notes": None,
            "meta_data": {
                "source": "manual",
                "generated_at": current_time.isoformat(),
                "source_name": "Test Client",
                "device": None,
                "version": None,
                "imported_at": None,
                "raw_data": None,
            },
        }

        # Make the request
        response = client.post("/api/sleep/records", json=payload)

        # Verify response
        assert response.status_code == 201

        # Verify returned record
        record = response.json()
        assert "id" in record
        assert record["user_id"] == payload["user_id"]
        assert record["sleep_quality"] == payload["sleep_quality"]
        assert record["meta_data"]["source"] == "manual"
        assert record["meta_data"]["device"] is None
        assert record["meta_data"]["version"] is None
        assert record["meta_data"]["imported_at"] is None
        assert record["meta_data"]["raw_data"] is None

    def test_get_sleep_data(self):
        """Test retrieving sleep data."""
        # Use a specific user ID for this test
        user_id = f"data_retrieval_user_{uuid.uuid4()}"

        # Generate data
        generate_payload = {
            "user_id": user_id,
            "start_date": (datetime.now() - timedelta(days=7)).isoformat(),
            "end_date": datetime.now().isoformat(),
            "include_time_series": False,
        }

        # Generate data
        response = client.post("/api/sleep/generate", json=generate_payload)
        assert response.status_code == 201

        # Now retrieve the data
        response = client.get(f"/api/sleep/data?user_id={user_id}")

        # Verify response
        assert response.status_code == 200
        data = response.json()

        assert "records" in data
        assert "count" in data
        assert data["count"] > 0

    def test_analyze_sleep_data(self):
        """Test analyzing sleep data."""
        # First, generate some data
        generate_payload = {
            "user_id": "analysis_user",
            "start_date": (datetime.now() - timedelta(days=30)).isoformat(),
            "end_date": datetime.now().isoformat(),
            "include_time_series": False,
        }
        client.post("/api/sleep/generate", json=generate_payload)

        # Now analyze the data
        response = client.get(
            f"/api/sleep/analytics?user_id=analysis_user"
            f"&start_date={(datetime.now() - timedelta(days=30)).isoformat()}"
            f"&end_date={datetime.now().isoformat()}"
        )

        # Verify response
        assert response.status_code == 200
        data = response.json()

        # Check key analysis components
        assert "user_id" in data
        assert "start_date" in data
        assert "end_date" in data
        assert "stats" in data

        # Verify stats structure
        stats = data["stats"]
        assert "average_duration_minutes" in stats
        assert "total_records" in stats
        assert "date_range_days" in stats

    def test_get_sleep_data_with_shared_db(self):
        """Test generating and retrieving sleep data using the shared database."""
        # Import necessary modules
        import os
        import uuid
        from datetime import datetime, timedelta

        # Use the same database URL as defined in conftest.py
        db_url = os.environ.get("DATABASE_URL")
        print(f"Test is using database URL: {db_url}")

        # Create a unique user ID for this test
        user_id = f"shared_db_test_{uuid.uuid4()}"

        # Generate data via API
        generate_payload = {
            "user_id": user_id,
            "start_date": (datetime.now() - timedelta(days=3)).isoformat(),
            "end_date": datetime.now().isoformat(),
            "include_time_series": False,
        }

        # Call API to generate data
        response = client.post("/api/sleep/generate", json=generate_payload)
        assert response.status_code == 201
        print(f"Generated data response: {response.json()}")

        # Retrieve data via API
        response = client.get(f"/api/sleep/data?user_id={user_id}")
        print(f"Retrieved data response: {response.json()}")

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["count"] > 0, "No records in API response"

    def test_get_users_endpoint(self):
        """Test the /api/sleep/users endpoint for retrieving users."""
        # First, generate data for a few test users with unique IDs
        test_users = [f"test_user_{uuid.uuid4()}" for _ in range(3)]

        for user_id in test_users:
            # Generate data for each user
            payload = {
                "user_id": user_id,
                "start_date": (datetime.now() - timedelta(days=7)).isoformat(),
                "end_date": datetime.now().isoformat(),
                "include_time_series": False,
            }

            # Make the request to generate data
            response = client.post("/api/sleep/generate", json=payload)
            assert response.status_code == 201, f"Failed to generate data for {user_id}"

        # Now retrieve the users
        response = client.get("/api/sleep/users")

        # Verify the response
        assert response.status_code == 200
        data = response.json()

        # Check the response structure
        assert "users" in data
        assert "count" in data
        assert isinstance(data["users"], list)
        assert data["count"] > 0

        # Verify all our test users are in the response
        user_ids_in_response = [user["user_id"] for user in data["users"]]
        for user_id in test_users:
            assert (
                user_id in user_ids_in_response
            ), f"User {user_id} not found in response"

        # Check that each user has the expected fields
        for user in data["users"]:
            assert "user_id" in user
            assert "record_count" in user
            assert "latest_record_date" in user
            assert isinstance(user["record_count"], int)
            assert user["record_count"] > 0
            assert isinstance(user["latest_record_date"], str)

    def test_get_users_pagination(self):
        """Test pagination for the /api/sleep/users endpoint."""
        # Generate at least 5 users to test pagination
        test_users = [f"pagination_user_{uuid.uuid4()}" for _ in range(5)]

        for user_id in test_users:
            # Generate data for each user
            payload = {
                "user_id": user_id,
                "start_date": (datetime.now() - timedelta(days=7)).isoformat(),
                "end_date": datetime.now().isoformat(),
                "include_time_series": False,
            }
            client.post("/api/sleep/generate", json=payload)

        # Test with limit parameter
        limit = 2
        response = client.get(f"/api/sleep/users?limit={limit}")

        assert response.status_code == 200
        data = response.json()

        # Should return only the requested number of users
        assert len(data["users"]) <= limit

        # Test with offset parameter
        offset = 2
        response = client.get(f"/api/sleep/users?offset={offset}")

        assert response.status_code == 200
        data_with_offset = response.json()

        # Get all users to compare
        response_all = client.get("/api/sleep/users")
        all_users = response_all.json()["users"]

        # Check if offset is working correctly
        if len(all_users) > offset:
            assert (
                data_with_offset["users"][0]["user_id"] == all_users[offset]["user_id"]
            )

    def test_get_users_empty_database(self):
        """Test the /api/sleep/users endpoint with no users in the database."""
        # Create a unique user ID that definitely won't be in the database
        unique_user_id = f"nonexistent_user_{uuid.uuid4()}"

        # Make a request to get a specific, nonexistent user to ensure it doesn't exist
        response = client.get(f"/api/sleep/data?user_id={unique_user_id}")
        records = response.json().get("records", [])
        assert len(records) == 0, "Test requires empty database but found records"

        # Now query the users endpoint with a filter that won't match anything
        response = client.get(
            "/api/sleep/users?limit=100&offset=10000"
        )  # Very high offset

        # Verify the response - should be an empty list but still a successful response
        assert response.status_code == 200
        data = response.json()

        assert data["users"] == []
        assert data["count"] == 0
