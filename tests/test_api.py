from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from app.main import app

# Create a test client
client = TestClient(app)


class TestAPI:
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
        payload = {
            "user_id": "create_test_user",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "sleep_start": (datetime.now() - timedelta(hours=8)).isoformat(),
            "sleep_end": datetime.now().isoformat(),
            "duration_minutes": 480,
            "sleep_quality": 85,
            "meta_data": {
                "source": "manual",
                "generated_at": datetime.now().isoformat(),
                "source_name": "Test Client",
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

    def test_get_sleep_data(self):
        """Test retrieving sleep data."""
        # First, generate some data
        generate_payload = {
            "user_id": "data_retrieval_user",
            "start_date": (datetime.now() - timedelta(days=7)).isoformat(),
            "end_date": datetime.now().isoformat(),
            "include_time_series": False,
        }
        client.post("/api/sleep/generate", json=generate_payload)

        # Now retrieve the data
        response = client.get("/api/sleep/data?user_id=data_retrieval_user")

        # Verify response
        assert response.status_code == 200
        data = response.json()

        assert "records" in data
        assert "count" in data
        assert data["count"] > 0

        # Check first record structure
        record = data["records"][0]
        assert "id" in record
        assert "user_id" in record
        assert "date" in record

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
