# In tests/conftest.py

import os
from unittest.mock import patch

import pytest

# Define a fixed path for the test database
TEST_DB_PATH = os.path.join(os.path.dirname(__file__), "test_db.db")
TEST_DB_URL = f"sqlite:///{TEST_DB_PATH}"


@pytest.fixture(scope="session", autouse=True)
def use_sqlite_db():
    """Use a fixed SQLite database for all tests."""
    # Store original database URL
    original_db_url = os.environ.get("DATABASE_URL")

    # Set our test database URL as an environment variable
    os.environ["DATABASE_URL"] = TEST_DB_URL

    # Also patch the settings module
    with patch("app.config.settings.settings.DATABASE_URL", TEST_DB_URL):
        yield

    # Clean up
    if original_db_url:
        os.environ["DATABASE_URL"] = original_db_url
    else:
        os.environ.pop("DATABASE_URL", None)

    # Optionally: Clean up the database file after tests
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)
