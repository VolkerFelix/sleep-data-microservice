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
            from app.services.storage.file_storage import FileStorage

            return FileStorage(data_dir="./data")
        elif storage_type == "memory":
            # Use an in-memory SQLite database
            from app.services.storage.db_storage import DatabaseStorage

            # Create a storage with in-memory SQLite
            storage = DatabaseStorage()
            storage.db_url = "sqlite:///:memory:"
            # Configure for SQLite
            from sqlalchemy import create_engine
            from sqlalchemy.orm import sessionmaker
            from sqlalchemy.pool import StaticPool

            storage.engine = create_engine(
                storage.db_url,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
            )
            storage.Session = sessionmaker(bind=storage.engine)
            # Create tables
            from app.services.storage.db_storage import Base

            Base.metadata.create_all(storage.engine)
            return storage

        # Add other storage types as needed

        return None
