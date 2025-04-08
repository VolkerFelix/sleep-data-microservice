import uuid
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set

from loguru import logger


class AppleHealthImporter:
    """Service for importing sleep data from Apple Health exports."""

    def __init__(self, storage_service=None):
        """Initialize the Apple Health importer with an optional storage service."""
        self.storage_service = storage_service

    def import_from_xml(self, user_id: str, xml_data: str) -> Dict[str, Any]:
        """
        Import sleep data from Apple Health Export XML.

        Args:
            user_id: User identifier
            xml_data: XML string from Apple Health Export

        Returns:
            Dictionary with import results
        """
        try:
            root = ET.fromstring(xml_data)

            # Extract sleep data
            sleep_records = self._extract_sleep_records(root, user_id)

            # Extract heart rate data that we can associate with sleep
            heart_rate_data = self._extract_heart_rate_data(root)

            # Enhance sleep records with heart rate data
            self._enhance_with_heart_rate(sleep_records, heart_rate_data)

            # Extract respiratory rate data
            respiratory_data = self._extract_respiratory_data(root)

            # Enhance sleep records with respiratory data
            self._enhance_with_respiratory_data(sleep_records, respiratory_data)

            # Extract environmental data if available
            environmental_data = self._extract_environmental_data(root)

            # Enhance sleep records with environmental data
            self._enhance_with_environmental_data(sleep_records, environmental_data)

            # Save records if storage service is available
            if self.storage_service and sleep_records:
                self.storage_service.save_sleep_records(user_id, sleep_records)

            return {
                "user_id": user_id,
                "records_imported": len(sleep_records),
                "heart_rate_data_points": len(heart_rate_data),
                "respiratory_data_points": len(respiratory_data),
                "environmental_data_points": len(environmental_data),
                "import_time": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error importing Apple Health data: {e}")
            raise

    def _extract_sleep_records(self, root: ET.Element, user_id: str) -> List[Dict]:
        """
        Extract sleep records from Apple Health data.

        Args:
            root: XML root element
            user_id: User identifier

        Returns:
            List of sleep records
        """
        sleep_records = []

        # Find sleep analysis records
        sleep_entries: Dict[str, Dict[str, Any]] = {}

        # First, find all sleep entries to group them by date
        for record in root.findall(".//Record"):
            if record.get("type") == "HKCategoryTypeIdentifierSleepAnalysis":
                value = record.get("value")
                source_name = record.get("sourceName", "Unknown")

                # Safely parse date strings
                start_date_str = record.get("startDate")
                end_date_str = record.get("endDate")

                if not start_date_str or not end_date_str:
                    logger.warning(
                        "Skipping sleep record with missing start or end date"
                    )
                    continue

                # Handle 'Z' timezone marker safely
                start_date = self._parse_apple_date(start_date_str)
                end_date = self._parse_apple_date(end_date_str)

                if not start_date or not end_date:
                    logger.warning(
                        f"""Skipping sleep record due to date
                        parsing error: {start_date_str} to {end_date_str}"""
                    )
                    continue

                # Determine the primary date for this
                # sleep record (the day the person went to sleep)
                date_key = start_date.strftime("%Y-%m-%d")

                # Only process sleep records (not
                # "in bed" records, unless we don't have sleep data)
                if value == "HKCategoryValueSleepAnalysisAsleep":
                    duration = (
                        end_date - start_date
                    ).total_seconds() / 60  # in minutes

                    # Create or update a sleep entry
                    if date_key not in sleep_entries:
                        sleep_entries[date_key] = {
                            "date": date_key,
                            "segments": [],  # type: ignore
                            "source_names": set(),  # type: ignore
                        }

                    from typing import cast

                    segments = cast(
                        List[Dict[str, Any]], sleep_entries[date_key]["segments"]
                    )
                    segments.append(
                        {
                            "start": start_date,
                            "end": end_date,
                            "duration_minutes": duration,
                            "source_name": source_name,
                            "value": value,
                        }
                    )

                    source_names = cast(
                        Set[str], sleep_entries[date_key]["source_names"]
                    )
                    source_names.add(source_name)

        # Process the grouped sleep entries into complete sleep records
        for date_key, entry in sleep_entries.items():
            segments = sorted(entry["segments"], key=lambda x: x["start"])

            if not segments:
                continue

            # Determine overall sleep period
            sleep_start = min(segment["start"] for segment in segments)
            sleep_end = max(segment["end"] for segment in segments)
            total_sleep_minutes = sum(
                segment["duration_minutes"] for segment in segments
            )

            # Merge segments that are close together (within 30 minutes)
            merged_segments = []
            if segments:
                current_segment = segments[0]

                for i in range(1, len(segments)):
                    if (
                        segments[i]["start"] - current_segment["end"]
                    ).total_seconds() / 60 <= 30:
                        # Merge segments
                        current_segment["end"] = max(
                            current_segment["end"], segments[i]["end"]
                        )
                        current_segment["duration_minutes"] += segments[i][
                            "duration_minutes"
                        ]
                    else:
                        # Start a new segment
                        merged_segments.append(current_segment)
                        current_segment = segments[i]

                merged_segments.append(current_segment)

            # Create the sleep record
            sleep_record = {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "date": date_key,
                "sleep_start": sleep_start.isoformat(),
                "sleep_end": sleep_end.isoformat(),
                "duration_minutes": int(total_sleep_minutes),
                "sleep_phases": {
                    # Apple Health doesn't directly provide this
                    "deep_sleep_minutes": None,
                    # Apple Health doesn't directly provide this
                    "rem_sleep_minutes": None,
                    # Apple Health doesn't directly provide this
                    "light_sleep_minutes": None,
                    "awake_minutes": int(
                        (sleep_end - sleep_start).total_seconds() / 60
                        - total_sleep_minutes
                    ),
                },
                "time_series": [],
                "meta_data": {
                    "source": "apple_health",
                    "imported_at": datetime.now().isoformat(),
                    "source_name": ", ".join(entry["source_names"]),
                    "segments_count": len(merged_segments),
                },
            }

            # Add time series data for sleep segments
            for segment in merged_segments:
                # Add entry at start of segment
                sleep_record["time_series"].append(
                    {
                        "timestamp": segment["start"].isoformat(),
                        # Apple Health doesn't provide detailed sleep stages
                        "stage": "light",
                        "heart_rate": None,
                        "movement": None,
                        "respiration_rate": None,
                    }
                )

                # Add entry at end of segment
                sleep_record["time_series"].append(
                    {
                        "timestamp": segment["end"].isoformat(),
                        "stage": "awake",
                        "heart_rate": None,
                        "movement": None,
                        "respiration_rate": None,
                    }
                )

            sleep_records.append(sleep_record)

        return sleep_records

    def _parse_apple_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """
        Safely parse Apple Health date strings, handling different formats.

        Args:
            date_str: Date string from Apple Health

        Returns:
            Parsed datetime object or None if parsing fails
        """
        if not date_str:
            return None

        try:
            # Handle Apple Health format (e.g., "2023-05-01 23:30:45 -0700")
            # First try direct ISO format
            try:
                return datetime.fromisoformat(date_str)
            except ValueError:
                # If that fails, parse the Apple Health format
                import re

                # Regular expression to match Apple Health date format
                pattern = r"(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}:\d{2}) ([-+]\d{4})"
                match = re.match(pattern, date_str)

                if match:
                    date_part, time_part, tz_part = match.groups()

                    # Convert timezone offset to ISO format (e.g., -0700 to -07:00)
                    tz_hours = tz_part[0:3]  # Include sign
                    tz_minutes = tz_part[3:5]
                    tz_iso = f"{tz_hours}:{tz_minutes}"

                    # Combine into ISO format
                    iso_datetime = f"{date_part}T{time_part}{tz_iso}"
                    return datetime.fromisoformat(iso_datetime)

                # If still no match, try other formats as needed
                raise ValueError(f"Unrecognized date format: {date_str}")

        except (ValueError, TypeError) as e:
            logger.warning(f"Error parsing date string: {date_str} - {e}")
            return None

    def _extract_heart_rate_data(self, root: ET.Element) -> List[Dict]:
        """
        Extract heart rate data from Apple Health.

        Args:
            root: XML root element

        Returns:
            List of heart rate data points
        """
        heart_rate_data = []

        for record in root.findall(
            './/Record[@type="HKQuantityTypeIdentifierHeartRate"]'
        ):
            try:
                # Safely parse the timestamp
                date_str = record.get("startDate")
                if not date_str:
                    continue

                timestamp = self._parse_apple_date(date_str)
                if not timestamp:
                    continue

                # Get and validate the value
                value_str = record.get("value")
                if not value_str:
                    continue

                try:
                    value = float(value_str)
                except (ValueError, TypeError):
                    continue

                if value > 0:  # Skip invalid readings
                    heart_rate_data.append(
                        {
                            "timestamp": timestamp,
                            "value": value,
                            "source": record.get("sourceName", "Unknown"),
                        }
                    )
            except Exception as e:
                logger.warning(f"Error parsing heart rate data: {e}")

        return heart_rate_data

    def _extract_respiratory_data(self, root: ET.Element) -> List[Dict]:
        """
        Extract respiratory rate data from Apple Health.

        Args:
            root: XML root element

        Returns:
            List of respiratory rate data points
        """
        respiratory_data = []

        for record in root.findall(
            './/Record[@type="HKQuantityTypeIdentifierRespiratoryRate"]'
        ):
            try:
                # Safely parse the timestamp
                date_str = record.get("startDate")
                if not date_str:
                    continue

                timestamp = self._parse_apple_date(date_str)
                if not timestamp:
                    continue

                # Get and validate the value
                value_str = record.get("value")
                if not value_str:
                    continue

                try:
                    value = float(value_str)
                except (ValueError, TypeError):
                    continue

                if value > 0:  # Skip invalid readings
                    respiratory_data.append(
                        {
                            "timestamp": timestamp,
                            "value": value,
                            "source": record.get("sourceName", "Unknown"),
                        }
                    )
            except Exception as e:
                logger.warning(f"Error parsing respiratory data: {e}")

        return respiratory_data

    def _extract_environmental_data(self, root: ET.Element) -> List[Dict]:
        """
        Extract environmental data from Apple Health (if available).

        Args:
            root: XML root element

        Returns:
            List of environmental data points
        """
        environmental_data = []

        # Check for environmental audio exposure (noise levels)
        for record in root.findall(
            './/Record[@type="HKQuantityTypeIdentifierEnvironmentalAudioExposure"]'
        ):
            try:
                # Safely parse the timestamp
                date_str = record.get("startDate")
                if not date_str:
                    continue

                timestamp = self._parse_apple_date(date_str)
                if not timestamp:
                    continue

                # Get and validate the value
                value_str = record.get("value")
                if not value_str:
                    continue

                try:
                    value = float(value_str)
                except (ValueError, TypeError):
                    continue

                environmental_data.append(
                    {
                        "timestamp": timestamp,
                        "type": "noise_level",
                        "value": value,
                        "source": record.get("sourceName", "Unknown"),
                    }
                )
            except Exception as e:
                logger.warning(f"Error parsing environmental audio data: {e}")

        return environmental_data

    def _enhance_with_heart_rate(
        self, sleep_records: List[Dict], heart_rate_data: List[Dict]
    ) -> None:
        """
        Enhance sleep records with heart rate data.

        Args:
            sleep_records: List of sleep records to enhance
            heart_rate_data: List of heart rate data points
        """
        for record in sleep_records:
            try:
                sleep_start = datetime.fromisoformat(record["sleep_start"])
                sleep_end = datetime.fromisoformat(record["sleep_end"])

                # Find heart rate data during this sleep period
                sleep_hr_data = [
                    item
                    for item in heart_rate_data
                    if sleep_start <= item["timestamp"] <= sleep_end
                ]

                if sleep_hr_data:
                    hr_values = [item["value"] for item in sleep_hr_data]
                    record["heart_rate"] = {
                        "average": sum(hr_values) / len(hr_values),
                        "min": min(hr_values),
                        "max": max(hr_values),
                    }

                    # Enhance time series with heart rate data
                    for ts_entry in record["time_series"]:
                        try:
                            ts_time = datetime.fromisoformat(ts_entry["timestamp"])

                            # Find closest heart rate reading (within 10 minutes)
                            closest_hr = None
                            min_diff = timedelta(minutes=10)

                            for hr_item in sleep_hr_data:
                                time_diff = abs(ts_time - hr_item["timestamp"])
                                if time_diff < min_diff:
                                    min_diff = time_diff
                                    closest_hr = hr_item["value"]

                            if closest_hr:
                                ts_entry["heart_rate"] = closest_hr
                        except Exception as e:
                            logger.warning(
                                f"Error enhancing time series with heart rate: {e}"
                            )
            except Exception as e:
                logger.warning(f"Error enhancing sleep record with heart rate: {e}")

    def _enhance_with_respiratory_data(
        self, sleep_records: List[Dict], respiratory_data: List[Dict]
    ) -> None:
        """
        Enhance sleep records with respiratory rate data.

        Args:
            sleep_records: List of sleep records to enhance
            respiratory_data: List of respiratory rate data points
        """
        for record in sleep_records:
            try:
                sleep_start = datetime.fromisoformat(record["sleep_start"])
                sleep_end = datetime.fromisoformat(record["sleep_end"])

                # Find respiratory data during this sleep period
                sleep_resp_data = [
                    item
                    for item in respiratory_data
                    if sleep_start <= item["timestamp"] <= sleep_end
                ]

                if sleep_resp_data:
                    resp_values = [item["value"] for item in sleep_resp_data]

                    # Add breathing data to the record
                    record["breathing"] = {
                        "average_rate": sum(resp_values) / len(resp_values),
                        "disruptions": None,  # Not available from Apple Health
                    }

                    # Enhance time series with respiratory data
                    for ts_entry in record["time_series"]:
                        try:
                            ts_time = datetime.fromisoformat(ts_entry["timestamp"])

                            # Find closest respiratory reading (within 10 minutes)
                            closest_resp = None
                            min_diff = timedelta(minutes=10)

                            for resp_item in sleep_resp_data:
                                time_diff = abs(ts_time - resp_item["timestamp"])
                                if time_diff < min_diff:
                                    min_diff = time_diff
                                    closest_resp = resp_item["value"]

                            if closest_resp:
                                ts_entry["respiration_rate"] = closest_resp
                        except Exception as e:
                            logger.warning(
                                f"""Error enhancing time series
                                with respiratory data: {e}"""
                            )
            except Exception as e:
                logger.warning(
                    f"Error enhancing sleep record with respiratory data: {e}"
                )

    def _enhance_with_environmental_data(
        self, sleep_records: List[Dict], environmental_data: List[Dict]
    ) -> None:
        """
        Enhance sleep records with environmental data.

        Args:
            sleep_records: List of sleep records to enhance
            environmental_data: List of environmental data points
        """
        for record in sleep_records:
            try:
                sleep_start = datetime.fromisoformat(record["sleep_start"])
                sleep_end = datetime.fromisoformat(record["sleep_end"])

                # Find environmental data during this sleep period
                sleep_env_data = [
                    item
                    for item in environmental_data
                    if sleep_start <= item["timestamp"] <= sleep_end
                ]

                # Group by data type
                env_by_type = {}  # type: ignore
                for item in sleep_env_data:
                    data_type = item["type"]
                    if data_type not in env_by_type:
                        env_by_type[data_type] = []
                    env_by_type[data_type].append(item["value"])

                # Add environment data if available
                if env_by_type:
                    record["environment"] = {}

                    if "noise_level" in env_by_type and env_by_type["noise_level"]:
                        record["environment"]["noise_level"] = sum(
                            env_by_type["noise_level"]
                        ) / len(env_by_type["noise_level"])
            except Exception as e:
                logger.warning(
                    f"Error enhancing sleep record with environmental data: {e}"
                )
