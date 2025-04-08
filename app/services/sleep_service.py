import random
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from loguru import logger

from app.models.sleep_models import SleepStage


class SleepDataService:
    """Service for handling sleep data, including generation and analysis."""

    def __init__(self, storage_service=None):
        """Initialize the sleep data service with an optional storage service."""
        self.storage_service = storage_service

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
                    quality_modifier = (
                        progress_factor * 15
                    )  # Improve by up to 15 points
                elif sleep_quality_trend == "declining":
                    quality_modifier = (
                        -progress_factor * 15
                    )  # Decline by up to 15 points
                elif sleep_quality_trend == "stable":
                    quality_modifier = 0
                else:  # random
                    quality_modifier = random.uniform(-5, 5)
            else:
                quality_modifier = random.uniform(-5, 5)

            if sleep_duration_trend:
                if sleep_duration_trend == "increasing":
                    duration_modifier = progress_factor * 2  # Increase by up to 2 hours
                elif sleep_duration_trend == "decreasing":
                    duration_modifier = (
                        -progress_factor * 2
                    )  # Decrease by up to 2 hours
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

            # Sleep phases vary based on quality
            quality_factor = sleep_quality / 100.0
            deep_sleep_percentage = 0.15 + (quality_factor * 0.15)  # 15-30%
            rem_sleep_percentage = 0.15 + (quality_factor * 0.20)  # 15-35%

            # Ensure percentages don't exceed 100%
            total_percentage = deep_sleep_percentage + rem_sleep_percentage
            if total_percentage > 0.8:  # Cap at 80% to leave room for light sleep
                scale_factor = 0.8 / total_percentage
                deep_sleep_percentage *= scale_factor
                rem_sleep_percentage *= scale_factor

            1 - deep_sleep_percentage - rem_sleep_percentage

            # Calculate durations for each sleep phase
            total_minutes = sleep_duration_hours * 60
            deep_sleep_minutes = int(total_minutes * deep_sleep_percentage)
            rem_sleep_minutes = int(total_minutes * rem_sleep_percentage)
            light_sleep_minutes = int(
                total_minutes - deep_sleep_minutes - rem_sleep_minutes
            )

            # Generate heart rate data that correlates with sleep quality
            # Higher quality sleep tends to have lower and more stable heart rates
            avg_heart_rate = 70 - (quality_factor * 15) + random.uniform(-3, 3)
            min_heart_rate = (
                avg_heart_rate - (5 + (quality_factor * 10)) + random.uniform(-2, 2)
            )
            max_heart_rate = (
                avg_heart_rate + (15 - (quality_factor * 5)) + random.uniform(-2, 2)
            )

            sleep_record = {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "date": current_date.strftime("%Y-%m-%d"),
                "sleep_start": sleep_start.isoformat(),
                "sleep_end": sleep_end.isoformat(),
                "duration_minutes": int(total_minutes),
                "sleep_phases": {
                    "deep_sleep_minutes": deep_sleep_minutes,
                    "rem_sleep_minutes": rem_sleep_minutes,
                    "light_sleep_minutes": light_sleep_minutes,
                    "awake_minutes": int(random.uniform(5, 20)),
                },
                "sleep_quality": sleep_quality,
                "heart_rate": {
                    "average": round(avg_heart_rate, 1),
                    "min": round(min_heart_rate, 1),
                    "max": round(max_heart_rate, 1),
                },
                "breathing": {
                    "average_rate": round(12 + random.uniform(-2, 2), 1),
                    "disruptions": int(random.uniform(0, 5) * (1 - quality_factor)),
                },
                "tags": [],
                "metadata": {
                    "source": "generated",
                    "generated_at": datetime.now().isoformat(),
                },
            }

            # Add environmental data occasionally
            if random.random() > 0.3:
                sleep_record["environment"] = {
                    "temperature": round(20 + random.uniform(-3, 3), 1),
                    "humidity": round(50 + random.uniform(-15, 15), 1),
                    "noise_level": round(20 + random.uniform(0, 15), 1),
                    "light_level": round(random.uniform(0, 5), 1),
                }

            # Generate time series data if requested
            if include_time_series:
                time_series = []
                current_time = sleep_start
                interval_minutes = 10  # Data points every 10 minutes

                # Determine sleep stage transitions based on
                # normal sleep cycle patterns
                # Typical sleep cycle: light → deep → light → REM,
                # repeating every ~90 minutes
                cycle_minutes = 90

                while current_time < sleep_end:
                    # Calculate minutes into sleep and position in the sleep cycle
                    minutes_into_sleep = (
                        current_time - sleep_start
                    ).total_seconds() / 60
                    cycle_position = (
                        minutes_into_sleep % cycle_minutes
                    ) / cycle_minutes

                    # Determine sleep stage based on cycle position
                    if cycle_position < 0.1:  # First ~9 minutes typically light sleep
                        stage = SleepStage.LIGHT
                    elif cycle_position < 0.4:  # Next ~27 minutes typically deep sleep
                        stage = SleepStage.DEEP
                    elif cycle_position < 0.7:  # Next ~27 minutes back to light sleep
                        stage = SleepStage.LIGHT
                    else:  # Last ~27 minutes typically REM sleep
                        stage = SleepStage.REM

                    # Briefly awake occasionally
                    if random.random() < 0.03:  # 3% chance of being briefly awake
                        stage = SleepStage.AWAKE

                    # Heart rate varies by sleep stage
                    if stage == SleepStage.DEEP:
                        hr = min_heart_rate + random.uniform(0, 5)
                    elif stage == SleepStage.REM:
                        hr = avg_heart_rate + random.uniform(-5, 10)
                    elif stage == SleepStage.LIGHT:
                        hr = avg_heart_rate + random.uniform(-7, 3)
                    else:  # AWAKE
                        hr = avg_heart_rate + random.uniform(5, 15)

                    # Movement varies by sleep stage
                    if stage == SleepStage.DEEP:
                        movement = random.uniform(0, 0.1)
                    elif stage == SleepStage.REM:
                        movement = random.uniform(0.1, 0.5)
                    elif stage == SleepStage.LIGHT:
                        movement = random.uniform(0.1, 0.3)
                    else:  # AWAKE
                        movement = random.uniform(0.5, 1.0)

                    # Add time series entry
                    time_series.append(
                        {
                            "timestamp": current_time.isoformat(),
                            "stage": stage,
                            "heart_rate": round(hr, 1),
                            "movement": round(movement, 2),
                            "respiration_rate": round(12 + random.uniform(-2, 2), 1),
                        }
                    )

                    # Move to next time interval
                    current_time += timedelta(minutes=interval_minutes)

                sleep_record["time_series"] = time_series

            sleep_data.append(sleep_record)
            current_date += timedelta(days=1)

        # If storage service is available, store the generated records
        if self.storage_service:
            try:
                self.storage_service.save_sleep_records(user_id, sleep_data)
            except Exception as e:
                logger.error(f"Failed to store generated sleep records: {str(e)}")

        return sleep_data

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

        deep_sleep_mins = []
        rem_sleep_mins = []
        light_sleep_mins = []

        for record in sleep_records:
            if "sleep_phases" in record:
                phases = record["sleep_phases"]
                if "deep_sleep_minutes" in phases:
                    deep_sleep_mins.append(phases["deep_sleep_minutes"])
                if "rem_sleep_minutes" in phases:
                    rem_sleep_mins.append(phases["rem_sleep_minutes"])
                if "light_sleep_minutes" in phases:
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

        # Calculate trends
        trends = self.calculate_sleep_trends(sleep_records)

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
            return {}

        # Sort records by date
        sorted_records = sorted(sleep_records, key=lambda x: x["date"])

        # Extract data for trend analysis
        [record["date"] for record in sorted_records]
        durations = [record["duration_minutes"] for record in sorted_records]
        qualities = [record.get("sleep_quality", None) for record in sorted_records]
        qualities = [q for q in qualities if q is not None]  # Remove None values

        # Simple linear trend calculation for duration
        duration_trend = self._calculate_trend(durations)

        # Simple linear trend calculation for quality if available
        quality_trend = self._calculate_trend(qualities) if qualities else None

        # Sleep schedule consistency
        start_times = [
            datetime.fromisoformat(record["sleep_start"]).time()
            for record in sorted_records
        ]
        start_time_minutes = [
            (t.hour * 60 + t.minute) % (24 * 60) for t in start_times
        ]  # Convert to minutes past midnight
        schedule_consistency = self._calculate_consistency(start_time_minutes)

        # Day-to-day variability in duration
        if len(durations) > 1:
            duration_differences = [
                abs(durations[i] - durations[i + 1]) for i in range(len(durations) - 1)
            ]
            avg_duration_difference = sum(duration_differences) / len(
                duration_differences
            )
            duration_variability = avg_duration_difference / (
                sum(durations) / len(durations)
            )  # Normalized
        else:
            duration_variability = 0

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
            },
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
            },
            "duration_variability": {
                "score": 100 - min(100, duration_variability * 100),
                "rating": "excellent"
                if duration_variability < 0.1
                else "good"
                if duration_variability < 0.2
                else "fair"
                if duration_variability < 0.3
                else "poor",
            },
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
