import os
import shutil
import sys
import tempfile
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# ruff: noqa: E501

# Add the application to the python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Patch database URL to use SQLite before importing app
with patch("app.config.settings.settings.DATABASE_URL", "sqlite:///:memory:"):
    from app.main import app
    from app.services.storage.factory import StorageFactory

# Apply SQLite patching for all tests in this module
pytestmark = [pytest.mark.usefixtures("use_sqlite_db")]


@pytest.fixture(scope="session", autouse=True)
def use_sqlite_db():
    """Use SQLite for all database operations."""
    with patch("app.config.settings.settings.DATABASE_URL", "sqlite:///:memory:"):
        yield


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_storage():
    """Create a mock storage service."""
    storage = MagicMock()
    # Configure common mock behaviors
    storage.get_sleep_records.return_value = []
    storage.save_sleep_records.return_value = True
    storage.delete_sleep_record.return_value = True
    return storage


@pytest.fixture
def memory_db_storage():
    """Create an in-memory database storage for testing."""
    # Use our factory to create an in-memory database
    return StorageFactory.create_storage_service("memory")


@pytest.fixture
def file_storage():
    """Create a temporary file storage for testing."""
    # Create a temporary directory for test data
    temp_dir = tempfile.mkdtemp()

    # Use our factory to create file storage with the temp directory
    from app.services.storage.file_storage import FileStorage

    storage = FileStorage(data_dir=temp_dir)

    yield storage

    # Clean up the temporary directory after the test
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_sleep_record():
    """Sample sleep record for testing."""
    return {
        "id": "test-record-id",
        "user_id": "test-user",
        "date": "2023-05-15",
        "sleep_start": "2023-05-15T23:00:00",
        "sleep_end": "2023-05-16T07:00:00",
        "duration_minutes": 480,
        "sleep_phases": {
            "deep_sleep_minutes": 120,
            "rem_sleep_minutes": 100,
            "light_sleep_minutes": 240,
            "awake_minutes": 20,
        },
        "sleep_quality": 85,
        "heart_rate": {"average": 60.5, "min": 55.0, "max": 75.0},
        "breathing": {"average_rate": 14.2, "disruptions": 0},
        "meta_data": {"source": "test", "generated_at": "2023-05-16T09:00:00"},
    }


@pytest.fixture
def sample_apple_health_xml():
    """Sample Apple Health XML for testing."""
    return """
    <?xml version="1.0" encoding="UTF-8"?>
    <HealthData locale="en_US">
        <ExportDate value="2023-05-15 10:30:45 -0700"/>
        <Me HKCharacteristicTypeIdentifierDateOfBirth="1990-01-01" HKCharacteristicTypeIdentifierBiologicalSex="HKBiologicalSexMale"/>
        <Record type="HKCategoryTypeIdentifierSleepAnalysis" sourceName="Sleep Cycle" sourceVersion="1" device="iPhone" unit="" value="HKCategoryValueSleepAnalysisAsleep" startDate="2023-05-15 23:30:45 -0700" endDate="2023-05-16 06:45:23 -0700"/>
        <Record type="HKQuantityTypeIdentifierHeartRate" sourceName="Apple Watch" sourceVersion="1" device="AppleWatch" unit="count/min" value="62" startDate="2023-05-15 23:45:00 -0700" endDate="2023-05-15 23:45:00 -0700"/>
        <Record type="HKQuantityTypeIdentifierHeartRate" sourceName="Apple Watch" sourceVersion="1" device="AppleWatch" unit="count/min" value="58" startDate="2023-05-16 02:15:00 -0700" endDate="2023-05-16 02:15:00 -0700"/>
        <Record type="HKQuantityTypeIdentifierRespiratoryRate" sourceName="Apple Watch" sourceVersion="1" device="AppleWatch" unit="count/min" value="14" startDate="2023-05-16 01:00:00 -0700" endDate="2023-05-16 01:00:00 -0700"/>
    </HealthData>
    """
