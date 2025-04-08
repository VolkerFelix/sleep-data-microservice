from typing import Optional
from loguru import logger

from app.config.settings import settings
from app.services.storage.file_storage import FileStorage
from app.services.storage.db_storage import DatabaseStorage

class StorageFactory:
    """Factory for creating storage service instances."""
    
    @staticmethod
    def get_storage_service(storage_type: Optional[str] = None):
        """
        Get a storage service instance.
        
        Args:
            storage_type: Type of storage service to create ('file' or 'database')
            
        Returns:
            Storage service instance
        """
        storage_type = storage_type or settings.STORAGE_TYPE
        
        if storage_type.lower() == "file":
            logger.info("Using file-based storage")
            return FileStorage(data_dir=settings.FILE_STORAGE_PATH)
        
        elif storage_type.lower() == "database":
            logger.info("Using database storage")
            return DatabaseStorage(db_url=settings.DATABASE_URL)
        
        else:
            logger.warning(f"Unknown storage type '{storage_type}', falling back to file storage")
            return FileStorage(data_dir=settings.FILE_STORAGE_PATH)