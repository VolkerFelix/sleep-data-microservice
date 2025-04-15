"""File-based storage service for sleep data."""

import errno
import json
import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from loguru import logger


class FileStorage:
    """File-based storage service for sleep data."""

    def __init__(self, base_path: str = "./data", data_dir: Optional[str] = None):
        """
        Initialize file storage service.

        Args:
            base_path: Base directory for storing data files
            data_dir: Optional alternative directory path (for backwards compatibility)
        """
        # Prefer data_dir if provided, otherwise use base_path
        self.base_path = data_dir or base_path
        os.makedirs(self.base_path, exist_ok=True)

    def _get_user_dir(self, user_id: str) -> str:
        """
        Get the directory path for a specific user.

        Args:
            user_id: User identifier

        Returns:
            Path to the user's data directory
        """
        user_dir = os.path.join(self.base_path, user_id)
        os.makedirs(user_dir, exist_ok=True)
        return user_dir

    def _save_file(self, file_path: str, data: Dict) -> bool:
        """
        Save data to a JSON file.

        Args:
            file_path: Full path to the file
            data: Data to be saved

        Returns:
            Boolean indicating success of save operation
        """
        try:
            with open(file_path, "w") as f:
                json.dump(data, f, indent=2)
            return True
        except IOError as e:
            logger.error(f"Error saving file {file_path}: {e}")
            return False

    def save_sleep_records(self, user_id: str, records: List[Dict]) -> bool:
        """
        Save sleep records for a user.

        Args:
            user_id: User identifier
            records: List of sleep records to save

        Returns:
            Boolean indicating success of save operation
        """
        user_dir = self._get_user_dir(user_id)
        success = True

        for record in records:
            # Ensure each record has a unique ID
            if "record_id" not in record:
                record["record_id"] = str(uuid.uuid4())

            # Separate time series data
            time_series = record.pop("time_series", [])

            # Save main record
            record_file = os.path.join(user_dir, f"{record['record_id']}.json")
            success &= self._save_file(record_file, record)

            # Save time series data if present
            if time_series:
                ts_dir = os.path.join(user_dir, "time_series")
                os.makedirs(ts_dir, exist_ok=True)
                ts_path = os.path.join(
                    ts_dir, f"{record['record_id']}_time_series.json"
                )
                success &= self._save_file(ts_path, {"time_series": time_series})

        return success

    def get_sleep_records(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict]:
        """
        Retrieve sleep records for a user.

        Args:
            user_id: User identifier
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            List of sleep records
        """
        user_dir = self._get_user_dir(user_id)
        records = []

        try:
            # Find all record files
            record_files = [
                f
                for f in os.listdir(user_dir)
                if f.endswith(".json") and not f.startswith("time_series")
            ]

            # Sort and slice records based on pagination
            record_files = sorted(record_files)[offset : offset + limit]

            for filename in record_files:
                try:
                    with open(os.path.join(user_dir, filename), "r") as f:
                        record = json.load(f)

                    # Try to load time series data
                    ts_dir = os.path.join(user_dir, "time_series")
                    ts_filename = f"{record['record_id']}_time_series.json"
                    ts_path = os.path.join(ts_dir, ts_filename)
                    if os.path.exists(ts_path):
                        with open(ts_path, "r") as f:
                            ts_data = json.load(f)
                            record["time_series"] = ts_data.get("time_series", [])

                    # Apply date filtering if dates are provided
                    record_date = datetime.fromisoformat(record["date"])
                    if (start_date is None or record_date >= start_date) and (
                        end_date is None or record_date <= end_date
                    ):
                        records.append(record)

                except json.JSONDecodeError as e:
                    logger.error(f"Error decoding JSON in {filename}: {e}")
                except FileNotFoundError as e:
                    logger.error(f"File not found: {e}")

        except FileNotFoundError:
            logger.warning(f"No records found for user {user_id}")
        except Exception as e:
            logger.error(f"Unexpected error retrieving records: {e}")

        return records

    def delete_sleep_record(self, user_id: str, record_id: str) -> bool:
        """
        Delete a specific sleep record.

        Args:
            user_id: User identifier
            record_id: Record identifier to delete

        Returns:
            Boolean indicating success of deletion
        """
        user_dir = self._get_user_dir(user_id)
        record_path = os.path.join(user_dir, f"{record_id}.json")
        ts_dir = os.path.join(user_dir, "time_series")
        ts_path = os.path.join(ts_dir, f"{record_id}_time_series.json")

        try:
            # Remove record file
            if os.path.exists(record_path):
                os.remove(record_path)

            # Remove time series file
            if os.path.exists(ts_path):
                os.remove(ts_path)
                # Try to remove the directory too if empty
                try:
                    os.rmdir(ts_dir)
                except OSError as dir_error:
                    # Only log if directory is not empty or other error occurs
                    if dir_error.errno != errno.ENOTEMPTY:
                        logger.warning(
                            f"Could not remove time series directory: {dir_error}"
                        )

            return True
        except FileNotFoundError:
            logger.warning(f"Record {record_id} not found for user {user_id}")
            return False
        except PermissionError as e:
            logger.error(f"Permission denied when deleting record {record_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting record {record_id}: {e}")
            return False

    def get_users(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get a list of unique users in the file storage with record counts.

        Args:
            limit: Maximum number of users to return
            offset: Number of users to skip

        Returns:
            List of dictionaries containing user_id and record_count
        """
        try:
            # Get all subdirectories in the base path (each subdirectory is a user)
            user_dirs = [
                d
                for d in os.listdir(self.base_path)
                if os.path.isdir(os.path.join(self.base_path, d))
            ]

            # Calculate record counts for each user
            user_records = []
            for user_id in user_dirs:
                user_dir = os.path.join(self.base_path, user_id)
                # Count .json files that are not in the time_series directory
                record_files = [
                    f
                    for f in os.listdir(user_dir)
                    if f.endswith(".json") and not f.startswith("time_series")
                ]

                user_records.append(
                    {"user_id": user_id, "record_count": len(record_files)}
                )

            # Sort by record count (descending)
            user_records.sort(
                key=lambda x: x["record_count"], reverse=True  # type: ignore
            )

            # Apply pagination
            return user_records[offset : offset + limit]

        except FileNotFoundError:
            logger.warning(f"Base directory {self.base_path} not found")
            return []
        except Exception as e:
            logger.error(f"Unexpected error retrieving users: {e}")
            return []
