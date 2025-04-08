import random
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

from loguru import logger

from app.models.sleep_models import SleepStage


class SleepDataService:
    """Service for handling sleep data, including generation and analysis."""

    def __init__(self, storage_service=None):
        """Initialize the sleep data service with an optional storage service."""
        self.storage_service = storage_service

    # In app/services/sleep_service.py, update the generate_dummy_data method:

    def generate_dummy_data(
        self,
        user_id: str,
        start_date: datetime,
        end_date: datetime,
        include_time_series: bool = False,
        sleep_quality_trend: Optional[str] = None,
        sleep_duration_trend: Optional[str] = None,
    ) -> List[Dict]:
        """
        Generate dummy sleep data for a date range.

        Args:
            user_id: User identifier
            start_date: Start date for generating data
            end_date: End date for generating data
            include_time_series: Whether to include detailed time series data
            sleep_quality_trend: Trend for sleep quality
            sleep_duration_trend: Trend for sleep duration

        Returns:
            List of sleep data records
        """
        sleep_data = []
        current_date = start_date
        days_total = (end_date - start_date).days + 1
        day_counter = 0

        # Base values for trending
        base_quality = random.randint(65, 80)
        base_duration = random.uniform(6.5, 7.5)

        while current_date <= end_date:
            day_counter += 1
            progress_factor = day_counter / days_total

            # Apply trends if specified
            if sleep_quality_trend:
                if sleep_quality_trend == "improving":
                    quality_modifier = progress_factor * 15
                elif sleep_quality_trend == "declining":
                    quality_modifier = -progress_factor * 15
                elif sleep_quality_trend == "stable":
                    quality_modifier = 0
                else:  # random
                    quality_modifier = random.uniform(-5, 5)
            else:
                quality_modifier = random.uniform(-5, 5)

            if sleep_duration_trend:
                if sleep_duration_trend == "increasing":
                    duration_modifier = progress_factor * 2
                elif sleep_duration_trend == "decreasing":
                    duration_modifier = -progress_factor * 2
                elif sleep_duration_trend == "stable":
                    duration_modifier = 0
                else:  # random
                    duration_modifier = random.uniform(-0.5, 0.5)
            else:
                duration_modifier = random.uniform(-0.5, 0.5)

            # Generate a random sleep time between 9 PM and midnight
            sleep_hour = random.randint(21, 23)
            sleep_minute = random.randint(0, 59)
            sleep_start = datetime(
                current_date.year,
                current_date.month,
                current_date.day,
                sleep_hour,
                sleep_minute,
            )

            # Apply trends to sleep duration
            sleep_duration_hours = max(
                4.0,
                min(
                    10.0, base_duration + duration_modifier + random.uniform(-0.5, 0.5)
                ),
            )
            sleep_end = sleep_start + timedelta(hours=sleep_duration_hours)

            # Generate random sleep quality metrics with trend
            quality_base = base_quality + quality_modifier
            quality_with_noise = max(40, min(98, quality_base + random.uniform(-5, 5)))
            sleep_quality = int(quality_with_noise)

            # Calculate duration in minutes
            duration_minutes = int(sleep_duration_hours * 60)

            # Generate sleep phases
            deep_sleep_pct = random.uniform(0.15, 0.25)  # 15-25% deep sleep
            rem_sleep_pct = random.uniform(0.20, 0.30)  # 20-30% REM sleep
            light_sleep_pct = (
                1 - deep_sleep_pct - rem_sleep_pct
            )  # Remaining is light sleep

            # Calculate minutes in each phase
            deep_sleep_minutes = int(duration_minutes * deep_sleep_pct)
            rem_sleep_minutes = int(duration_minutes * rem_sleep_pct)
            light_sleep_minutes = int(duration_minutes * light_sleep_pct)
            awake_minutes = (
                duration_minutes
                - deep_sleep_minutes
                - rem_sleep_minutes
                - light_sleep_minutes
            )

            # Prepare record
            record = {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "date": current_date.strftime("%Y-%m-%d"),
                "sleep_start": sleep_start.isoformat(),
                "sleep_end": sleep_end.isoformat(),
                "duration_minutes": duration_minutes,
                "sleep_quality": sleep_quality,
                "sleep_phases": {
                    "deep_sleep_minutes": deep_sleep_minutes,
                    "rem_sleep_minutes": rem_sleep_minutes,
                    "light_sleep_minutes": light_sleep_minutes,
                    "awake_minutes": awake_minutes if awake_minutes >= 0 else 0,
                },
                "heart_rate": {
                    "average": round(random.uniform(55, 65), 1),
                    "min": round(random.uniform(45, 55), 1),
                    "max": round(random.uniform(65, 85), 1),
                },
                "meta_data": {
                    "source": "generated",
                    "generated_at": datetime.now().isoformat(),
                    "source_name": "Sleep Service",
                },
            }

            # Optionally generate time series data
            if include_time_series:
                record["time_series"] = self._generate_time_series(
                    sleep_start, sleep_end, duration_minutes
                )

            sleep_data.append(record)
            current_date += timedelta(days=1)

        # If storage service is available, store the generated records
        if self.storage_service:
            try:
                success = self.storage_service.save_sleep_records(user_id, sleep_data)
                if not success:
                    logger.error(
                        """Failed to store generated sleep records:
                        save operation returned False"""
                    )
                    raise Exception("Failed to store generated sleep records")
            except Exception as e:
                logger.error(f"Failed to store generated sleep records: {str(e)}")
                raise

        return sleep_data

    def _generate_time_series(
        self,
        sleep_start: Union[datetime, str],
        sleep_end: Union[datetime, str],
        duration_minutes: int,
    ) -> List[Dict[str, Any]]:
        """
        Generate time series data for a sleep record.

        Args:
            sleep_start: Start time of sleep
            sleep_end: End time of sleep
            duration_minutes: Total sleep duration

        Returns:
            List of time series data points
        """
        # Convert to datetime if strings
        if isinstance(sleep_start, str):
            sleep_start = datetime.fromisoformat(sleep_start)
        if isinstance(sleep_end, str):
            sleep_end = datetime.fromisoformat(sleep_end)

        time_series = []
        current_time = sleep_start
        interval_minutes = 10  # Data points every 10 minutes

        while current_time < sleep_end:
            # Randomly select a sleep stage
            stage = random.choice(list(SleepStage))

            # Simulate heart rate variations based on sleep stage
            if stage == SleepStage.DEEP:
                heart_rate = random.uniform(50, 60)
            elif stage == SleepStage.REM:
                heart_rate = random.uniform(60, 70)
            elif stage == SleepStage.LIGHT:
                heart_rate = random.uniform(55, 65)
            else:  # AWAKE
                heart_rate = random.uniform(65, 75)

            # Simulate movement based on sleep stage
            if stage == SleepStage.DEEP:
                movement = random.uniform(0, 0.1)
            elif stage == SleepStage.REM:
                movement = random.uniform(0.1, 0.5)
            elif stage == SleepStage.LIGHT:
                movement = random.uniform(0.1, 0.3)
            else:  # AWAKE
                movement = random.uniform(0.5, 1.0)

            time_series.append(
                {
                    "timestamp": current_time.isoformat(),
                    "stage": stage,
                    "heart_rate": round(heart_rate, 1),
                    "movement": round(movement, 2),
                    "respiration_rate": round(random.uniform(12, 16), 1),
                }
            )

            # Move to next time interval
            current_time += timedelta(minutes=interval_minutes)

        return time_series

    def get_sleep_data(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict]:
        """
        Retrieve sleep data for a specific user and date range.

        Args:
            user_id: User identifier
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            List of sleep data records
        """
        if not self.storage_service:
            raise ValueError("Storage service is required to retrieve sleep data")

        return self.storage_service.get_sleep_records(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset,
        )

    def analyze_sleep_data(
        self, user_id: str, start_date: datetime, end_date: datetime
    ) -> Dict:
        """
        Analyze sleep data for a specific user and date range.

        Args:
            user_id: User identifier
            start_date: Start date for analysis
            end_date: End date for analysis

        Returns:
            Dictionary with sleep analysis results
        """
        if not self.storage_service:
            raise ValueError("Storage service is required to analyze sleep data")

        sleep_records = self.storage_service.get_sleep_records(
            user_id=user_id, start_date=start_date, end_date=end_date
        )

        if not sleep_records:
            return {
                "user_id": user_id,
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "error": "No sleep data found for the specified parameters",
            }

        # Calculate basic statistics
        durations = [record["duration_minutes"] for record in sleep_records]
        avg_duration = sum(durations) / len(durations)

        quality_scores = [
            record.get("sleep_quality")
            for record in sleep_records
            if record.get("sleep_quality") is not None
        ]
        avg_quality = (
            sum(quality_scores) / len(quality_scores) if quality_scores else None
        )

        # Add default values for sleep phases if they're missing
        deep_sleep_mins = []
        rem_sleep_mins = []
        light_sleep_mins = []

        for record in sleep_records:
            if "sleep_phases" in record and record["sleep_phases"]:
                phases = record["sleep_phases"]
                if (
                    phases
                    and "deep_sleep_minutes" in phases
                    and phases["deep_sleep_minutes"] is not None
                ):
                    deep_sleep_mins.append(phases["deep_sleep_minutes"])
                if (
                    phases
                    and "rem_sleep_minutes" in phases
                    and phases["rem_sleep_minutes"] is not None
                ):
                    rem_sleep_mins.append(phases["rem_sleep_minutes"])
                if (
                    phases
                    and "light_sleep_minutes" in phases
                    and phases["light_sleep_minutes"] is not None
                ):
                    light_sleep_mins.append(phases["light_sleep_minutes"])

        avg_deep = (
            sum(deep_sleep_mins) / len(deep_sleep_mins) if deep_sleep_mins else None
        )
        avg_rem = sum(rem_sleep_mins) / len(rem_sleep_mins) if rem_sleep_mins else None
        avg_light = (
            sum(light_sleep_mins) / len(light_sleep_mins) if light_sleep_mins else None
        )

        # Calculate date range in days
        date_range_days = (end_date - start_date).days + 1

        # Calculate trends - wrap this in try-except to handle potential errors
        try:
            trends = self.calculate_sleep_trends(sleep_records)
        except Exception as e:
            import logging

            logging.error(f"Error calculating trends: {str(e)}")
            trends = {"note": "Error calculating trends", "error": str(e)}

        return {
            "user_id": user_id,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "stats": {
                "average_duration_minutes": round(avg_duration, 1),
                "average_sleep_quality": round(avg_quality, 1) if avg_quality else None,
                "average_deep_sleep_minutes": round(avg_deep, 1) if avg_deep else None,
                "average_rem_sleep_minutes": round(avg_rem, 1) if avg_rem else None,
                "average_light_sleep_minutes": round(avg_light, 1)
                if avg_light
                else None,
                "total_records": len(sleep_records),
                "date_range_days": date_range_days,
            },
            "trends": trends,
            "recommendations": [
                "Maintain a consistent sleep schedule",
                "Ensure your bedroom is dark and quiet",
                "Avoid caffeine and large meals before bedtime",
            ],
        }

    def calculate_sleep_trends(self, sleep_records: List[Dict]) -> Dict[str, Any]:
        """
        Calculate trends in sleep data.

        Args:
            sleep_records: List of sleep records

        Returns:
            Dictionary with trend analysis
        """
        if not sleep_records:
            return {
                "note": "Insufficient data to calculate trends",
                "duration_trend": None,
                "quality_trend": None,
                "schedule_consistency": None,
                "duration_variability": None,
            }

        # Sort records by date
        sorted_records = sorted(sleep_records, key=lambda x: x["date"])

        # Extract data for trend analysis
        durations = [record["duration_minutes"] for record in sorted_records]
        qualities = [record.get("sleep_quality", None) for record in sorted_records]
        qualities = [q for q in qualities if q is not None]  # Remove None values

        # Calculate trends only if we have enough data points
        if len(durations) < 2:
            return {
                "note": "Need at least two data points to calculate trends",
                "duration_trend": None,
                "quality_trend": None,
                "schedule_consistency": None,
                "duration_variability": None,
            }

        # Simple linear trend calculation for duration
        duration_trend = self._calculate_trend(durations)

        # Simple linear trend calculation for quality if available
        quality_trend = (
            self._calculate_trend(qualities) if len(qualities) >= 2 else None
        )

        # Sleep schedule consistency
        try:
            start_times = [
                datetime.fromisoformat(record["sleep_start"]).time()
                if isinstance(record["sleep_start"], str)
                else record["sleep_start"].time()
                for record in sorted_records
            ]
            start_time_minutes = [
                (t.hour * 60 + t.minute) % (24 * 60) for t in start_times
            ]  # Convert to minutes past midnight
            schedule_consistency = self._calculate_consistency(start_time_minutes)
        except Exception as e:
            import logging

            logging.error(f"Error calculating schedule consistency: {str(e)}")
            schedule_consistency = None

        # Day-to-day variability in duration
        try:
            if len(durations) > 1:
                duration_differences = [
                    abs(durations[i] - durations[i + 1])
                    for i in range(len(durations) - 1)
                ]
                avg_duration_difference = sum(duration_differences) / len(
                    duration_differences
                )
                duration_variability = avg_duration_difference / (
                    sum(durations) / len(durations)
                )  # Normalized
            else:
                duration_variability = 0
        except Exception as e:
            import logging

            logging.error(f"Error calculating duration variability: {str(e)}")
            duration_variability = None

        return {
            "duration_trend": {
                "direction": "increasing"
                if duration_trend > 0.01
                else "decreasing"
                if duration_trend < -0.01
                else "stable",
                "strength": abs(duration_trend),
                "average_change_per_day": duration_trend
                * 60,  # Convert back to minutes
            }
            if duration_trend is not None
            else None,
            "quality_trend": {
                "direction": "improving"
                if quality_trend > 0.01
                else "declining"
                if quality_trend < -0.01
                else "stable",
                "strength": abs(quality_trend),
                "average_change_per_day": quality_trend,
            }
            if quality_trend is not None
            else None,
            "schedule_consistency": {
                "score": 100
                - min(
                    100, schedule_consistency
                ),  # Convert to a 0-100 score where 100 is perfectly consistent
                "rating": "excellent"
                if schedule_consistency < 30
                else "good"
                if schedule_consistency < 60
                else "fair"
                if schedule_consistency < 90
                else "poor",
            }
            if schedule_consistency is not None
            else None,
            "duration_variability": {
                "score": 100 - min(100, duration_variability * 100),
                "rating": "excellent"
                if duration_variability < 0.1
                else "good"
                if duration_variability < 0.2
                else "fair"
                if duration_variability < 0.3
                else "poor",
            }
            if duration_variability is not None
            else None,
        }

    def _calculate_trend(self, values: List[float]) -> float:
        """
        Calculate a simple linear trend from a list of values.

        Returns:
            float: average change per step
            (positive for increasing, negative for decreasing)
        """
        if len(values) < 2:
            return 0

        diffs = [values[i + 1] - values[i] for i in range(len(values) - 1)]
        return sum(diffs) / len(diffs)

    def _calculate_consistency(self, time_minutes: List[int]) -> float:
        """
        Calculate consistency of times (in minutes past midnight).
        Lower values indicate more consistent times.

        Returns:
            float: standard deviation in minutes
        """
        if len(time_minutes) < 2:
            return 0

        # Handle time wrapping (e.g., 11pm vs 1am should be considered close)
        adjusted_times = time_minutes.copy()
        mean_time = sum(time_minutes) / len(time_minutes)

        for i in range(len(adjusted_times)):
            # If the time is more than 12 hours away from the mean, adjust it
            if abs(adjusted_times[i] - mean_time) > 12 * 60:
                if adjusted_times[i] < mean_time:
                    adjusted_times[i] += 24 * 60
                else:
                    adjusted_times[i] -= 24 * 60

        # Recalculate mean
        adjusted_mean = sum(adjusted_times) / len(adjusted_times)

        # Calculate standard deviation
        variance = sum((t - adjusted_mean) ** 2 for t in adjusted_times) / len(
            adjusted_times
        )
        return variance**0.5  # standard deviation in minutes
