"""Factory for creating storage service instances."""

from typing import Optional, Union

from app.services.storage.db_storage import DatabaseStorage
from app.services.storage.file_storage import FileStorage  # Will implement this


class StorageFactory:
    """Factory for creating storage service instances."""

    @staticmethod
    def create_storage_service(
        storage_type: Optional[str] = None,
    ) -> Union[DatabaseStorage, "FileStorage", None]:
        """
        Create a storage service instance based on the specified type.

        Args:
            storage_type: Type of storage service to create
                Options: 'database', 'file', 'memory'
                If None, use the default from settings.

        Returns:
            Storage service instance or None if type is not supported.
        """
        if storage_type is None:
            # Default to database storage for production
            storage_type = "database"

        if storage_type == "database":
            return DatabaseStorage()
        elif storage_type == "file":
            # Create FileStorage with a default data directory
            return FileStorage(data_dir="./data")
        elif storage_type == "memory":
            # Create a DatabaseStorage with SQLite in-memory database
            return DatabaseStorage(db_url="sqlite:///:memory:")

        # Add other storage types as needed
        return None
