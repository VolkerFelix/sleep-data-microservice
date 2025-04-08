from unittest.mock import patch

import pytest

from app.services.storage.db_storage import DatabaseStorage
from app.services.storage.factory import StorageFactory

# Create a single shared database storage for all tests
test_db_storage = DatabaseStorage(db_url="sqlite:///:memory:")


# Patch the factory to always return our test storage
@pytest.fixture(autouse=True)
def mock_storage_factory():
    with patch.object(
        StorageFactory, "create_storage_service", return_value=test_db_storage
    ):
        yield
