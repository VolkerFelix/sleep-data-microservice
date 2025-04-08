import json
import os
from datetime import datetime
from typing import Dict, List, Optional
import uuid
from loguru import logger

class FileStorage:
    """Simple file-based storage service for sleep data.
    
    Note: This is for development and testing only. In a production environment,
    use a proper database instead of file storage.
    """
    
    def __init__(self, data_dir: str = None):
        """Initialize the storage service."""
        self.data_dir = data_dir or os.environ.get("FILE_STORAGE_PATH", "./data/sleep")
        os.makedirs(self.data_dir, exist_ok=True)
    
    def _get_user_file_path(self, user_id: str) -> str:
        """Get the file path for a user's sleep data."""
        safe_user_id = self._sanitize_filename(user_id)
        return os.path.join(self.data_dir, f"{safe_user_id}.json")
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename to avoid path traversal."""
        return "".join(c for c in filename if c.isalnum() or c in ('-', '_')).lower()
    
    def save_sleep_records(self, user_id: str, records: List[Dict]) -> bool:
        """Save sleep records for a user."""
        try:
            file_path = self._get_user_file_path(user_id)
            
            # Load existing data if file exists
            existing_records = []
            if os.path.exists(file_path):
                with open(file_path, "r") as f:
                    existing_records = json.load(f)
            
            # Add new records, update existing ones
            existing_ids = {record.get("id"): i for i, record in enumerate(existing_records)}
            
            for record in records:
                if "id" not in record:
                    record["id"] = str(uuid.uuid4())
                
                record_id = record["id"]
                if record_id in existing_ids:
                    # Update existing record
                    existing_records[existing_ids[record_id]] = record
                else:
                    # Add new record
                    existing_records.append(record)
            
            # Save all records
            with open(file_path, "w") as f:
                json.dump(existing_records, f, indent=2)
            
            return True
        except Exception as e:
            logger.error(f"Error saving sleep records: {e}")
            return False
    
    def get_sleep_records(
        self, 
        user_id: str, 
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict]:
        """Get sleep records for a user, optionally filtered by date range."""
        try:
            file_path = self._get_user_file_path(user_id)
            
            if not os.path.exists(file_path):
                return []
            
            with open(file_path, "r") as f:
                records = json.load(f)
            
            # Filter by date range if specified
            if start_date or end_date:
                filtered_records = []
                for record in records:
                    record_date = record.get("date")
                    if not record_date:
                        continue
                    
                    record_datetime = datetime.strptime(record_date, "%Y-%m-%d")
                    
                    if start_date and record_datetime < start_date:
                        continue
                    if end_date and record_datetime > end_date:
                        continue
                    
                    filtered_records.append(record)
                
                records = filtered_records
            
            # Sort by date (newest first)
            records.sort(key=lambda x: x.get("date", ""), reverse=True)
            
            # Apply pagination
            paginated_records = records[offset:offset + limit]
            
            return paginated_records
        
        except Exception as e:
            logger.error(f"Error getting sleep records: {e}")
            return []
    
    def delete_sleep_record(self, user_id: str, record_id: str) -> bool:
        """Delete a sleep record."""
        try:
            file_path = self._get_user_file_path(user_id)
            
            if not os.path.exists(file_path):
                return False
            
            with open(file_path, "r") as f:
                records = json.load(f)
            
            # Find and remove the record
            original_length = len(records)
            records = [r for r in records if r.get("id") != record_id]
            
            if len(records) == original_length:
                # Record not found
                return False
            
            # Save the updated records
            with open(file_path, "w") as f:
                json.dump(records, f, indent=2)
            
            return True
        
        except Exception as e:
            logger.error(f"Error deleting sleep record: {e}")
            return False