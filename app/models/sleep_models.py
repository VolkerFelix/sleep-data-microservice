"""Models for the sleep data microservice."""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator


class SleepStage(str, Enum):
    """Enum for sleep stages."""

    DEEP = "deep"
    REM = "rem"
    LIGHT = "light"
    AWAKE = "awake"


class SleepPhases(BaseModel):
    """Model for sleep phases data."""

    deep_sleep_minutes: int = Field(..., description="Minutes spent in deep sleep")
    rem_sleep_minutes: int = Field(..., description="Minutes spent in REM sleep")
    light_sleep_minutes: int = Field(..., description="Minutes spent in light sleep")
    awake_minutes: Optional[int] = Field(
        0, description="Minutes spent awake during sleep period"
    )


class HeartRateData(BaseModel):
    """Model for heart rate data during sleep."""

    average: float = Field(..., description="Average heart rate during sleep")
    minimum: float = Field(..., description="Minimum heart rate during sleep")
    maximum: float = Field(..., description="Maximum heart rate during sleep")
    resting: Optional[float] = Field(None, description="Resting heart rate")


class BreathingData(BaseModel):
    """Model for breathing data during sleep."""

    average_rate: Optional[float] = Field(
        None, description="Average breathing rate (breaths per minute)"
    )
    disruptions: Optional[int] = Field(
        None, description="Number of breathing disruptions/irregularities"
    )


class Sleepmeta_data(BaseModel):
    """Model for sleep data meta_data."""

    source: str = Field(default="generated", description="Source of the sleep data")
    generated_at: Optional[Union[datetime, str]] = Field(
        default_factory=datetime.now, description="When the data was generated"
    )
    imported_at: Optional[Union[datetime, str]] = Field(
        None, description="When the data was imported"
    )
    device: Optional[str] = Field(None, description="Device that recorded the data")
    source_name: Optional[str] = Field(
        None, description="Name of the source application"
    )
    version: Optional[str] = Field(
        None, description="Version of the source application"
    )
    raw_data: Optional[Dict[str, Any]] = Field(
        None, description="Raw data from the source"
    )

    @validator("generated_at", pre=True, always=True)
    def convert_generated_at(cls, v):
        """Ensure generated_at is a datetime or ISO format string."""
        if isinstance(v, str):
            return datetime.fromisoformat(v)
        return v or datetime.now()


class SleepEnvironment(BaseModel):
    """Model for sleep environment data."""

    temperature: Optional[float] = Field(None, description="Ambient temperature")
    humidity: Optional[float] = Field(None, description="Ambient humidity")
    noise_level: Optional[float] = Field(None, description="Ambient noise level")
    light_level: Optional[float] = Field(None, description="Ambient light level")


class SleepTimeSeries(BaseModel):
    """Model for time series data during sleep."""

    timestamp: datetime = Field(..., description="Timestamp of the measurement")
    stage: Optional[SleepStage] = Field(None, description="Sleep stage at this time")
    heart_rate: Optional[float] = Field(None, description="Heart rate at this time")
    movement: Optional[float] = Field(None, description="Movement level at this time")
    respiration_rate: Optional[float] = Field(
        None, description="Respiration rate at this time"
    )


class SleepRecord(BaseModel):
    """Model for a sleep record."""

    record_id: str = Field(..., description="Unique identifier for the sleep record")
    user_id: str = Field(..., description="User identifier")
    date: str = Field(..., description="Date of the sleep record (YYYY-MM-DD)")
    sleep_start: datetime = Field(..., description="Start time of sleep")
    sleep_end: datetime = Field(..., description="End time of sleep")
    duration_minutes: int = Field(..., description="Total duration of sleep in minutes")
    sleep_phases: Optional[SleepPhases] = Field(
        None, description="Breakdown of sleep phases"
    )
    sleep_quality: Optional[int] = Field(
        None, description="Sleep quality score (0-100)"
    )
    heart_rate: Optional[HeartRateData] = Field(
        None, description="Heart rate data during sleep"
    )
    breathing: Optional[BreathingData] = Field(
        None, description="Breathing data during sleep"
    )
    environment: Optional[SleepEnvironment] = Field(
        None, description="Sleep environment data"
    )
    time_series: Optional[List[SleepTimeSeries]] = Field(
        None, description="Time series data for the sleep session"
    )
    tags: Optional[List[str]] = Field(
        None, description="Tags associated with this sleep record"
    )
    notes: Optional[str] = Field(None, description="Notes about this sleep record")
    meta_data: Sleepmeta_data = Field(
        ..., description="meta_data about the sleep record"
    )


class SleepRecordCreate(BaseModel):
    """Model for creating a sleep record."""

    user_id: str = Field(..., description="User identifier")
    date: str = Field(..., description="Date of the sleep record (YYYY-MM-DD)")
    sleep_start: datetime = Field(..., description="Start time of sleep")
    sleep_end: datetime = Field(..., description="End time of sleep")
    duration_minutes: int = Field(..., description="Total duration of sleep in minutes")
    sleep_phases: Optional[SleepPhases] = Field(
        None, description="Breakdown of sleep phases"
    )
    sleep_quality: Optional[int] = Field(
        None, description="Sleep quality score (0-100)"
    )
    heart_rate: Optional[HeartRateData] = Field(
        None, description="Heart rate data during sleep"
    )
    breathing: Optional[BreathingData] = Field(
        None, description="Breathing data during sleep"
    )
    environment: Optional[SleepEnvironment] = Field(
        None, description="Sleep environment data"
    )
    time_series: Optional[List[SleepTimeSeries]] = Field(
        None, description="Time series data for the sleep session"
    )
    tags: Optional[List[str]] = Field(
        None, description="Tags associated with this sleep record"
    )
    notes: Optional[str] = Field(None, description="Notes about this sleep record")
    meta_data: Sleepmeta_data = Field(
        ..., description="meta_data about the sleep record"
    )


class SleepRecordUpdate(BaseModel):
    """Model for updating a sleep record."""

    date: Optional[str] = Field(
        None, description="Date of the sleep record (YYYY-MM-DD)"
    )
    sleep_start: Optional[datetime] = Field(None, description="Start time of sleep")
    sleep_end: Optional[datetime] = Field(None, description="End time of sleep")
    duration_minutes: Optional[int] = Field(
        None, description="Total duration of sleep in minutes"
    )
    sleep_phases: Optional[SleepPhases] = Field(
        None, description="Breakdown of sleep phases"
    )
    sleep_quality: Optional[int] = Field(
        None, description="Sleep quality score (0-100)"
    )
    heart_rate: Optional[HeartRateData] = Field(
        None, description="Heart rate data during sleep"
    )
    breathing: Optional[BreathingData] = Field(
        None, description="Breathing data during sleep"
    )
    environment: Optional[SleepEnvironment] = Field(
        None, description="Sleep environment data"
    )
    time_series: Optional[List[SleepTimeSeries]] = Field(
        None, description="Time series data for the sleep session"
    )
    tags: Optional[List[str]] = Field(
        None, description="Tags associated with this sleep record"
    )
    notes: Optional[str] = Field(None, description="Notes about this sleep record")


class SleepDataResponse(BaseModel):
    """Response model for sleep data."""

    records: List[SleepRecord] = Field(..., description="List of sleep records")
    count: int = Field(..., description="Total number of records")


class GenerateSleepDataRequest(BaseModel):
    """Request model for generating sleep data."""

    user_id: str = Field(
        ..., description="User ID to associate with the generated data"
    )
    start_date: datetime = Field(..., description="Start date for generating data")
    end_date: datetime = Field(..., description="End date for generating data")
    include_time_series: bool = Field(
        False, description="Whether to include detailed time series data"
    )
    sleep_quality_trend: Optional[str] = Field(
        None,
        description="""Trend for sleep quality:
        'improving', 'declining', 'stable', 'random'""",
    )
    sleep_duration_trend: Optional[str] = Field(
        None,
        description="""Trend for sleep duration:
        'increasing', 'decreasing', 'stable', 'random'""",
    )


class SleepStats(BaseModel):
    """Model for sleep statistics."""

    average_duration_minutes: float = Field(
        ..., description="Average sleep duration in minutes"
    )
    average_sleep_quality: Optional[float] = Field(
        None, description="Average sleep quality score"
    )
    average_deep_sleep_minutes: Optional[float] = Field(
        None, description="Average deep sleep duration in minutes"
    )
    average_rem_sleep_minutes: Optional[float] = Field(
        None, description="Average REM sleep duration in minutes"
    )
    average_light_sleep_minutes: Optional[float] = Field(
        None, description="Average light sleep duration in minutes"
    )
    total_records: int = Field(..., description="Total number of sleep records")
    date_range_days: int = Field(..., description="Number of days in the date range")


class SleepAnalyticsResponse(BaseModel):
    """Response model for sleep analytics."""

    user_id: str = Field(..., description="User ID")
    start_date: str = Field(..., description="Start date of the analysis")
    end_date: str = Field(..., description="End date of the analysis")
    stats: SleepStats = Field(..., description="Sleep statistics")
    trends: Dict[str, Any] = Field(..., description="Sleep trends analysis")
    recommendations: Optional[List[str]] = Field(
        None, description="Sleep recommendations based on the analysis"
    )


class AppleHealthImportRequest(BaseModel):
    """Request model for importing Apple Health data."""

    user_id: str = Field(..., description="User ID to associate with the imported data")
    data_type: Optional[str] = Field(
        "export_xml", description="Type of Apple Health data: 'export_xml' or 'direct'"
    )


class SleepDurationStats(BaseModel):
    """Model for sleep duration statistics."""

    minutes: float = Field(..., description="Duration in minutes")
    hours: float = Field(..., description="Duration in hours")


class SleepTrend(BaseModel):
    """Model for sleep trend information."""

    metric: str = Field(..., description="Metric name (e.g., 'duration', 'quality')")
    trend_direction: str = Field(
        ..., description="Trend direction ('increasing', 'decreasing', 'stable')"
    )
    trend_strength: float = Field(..., description="Strength of the trend (0.0 to 1.0)")
    period: str = Field(..., description="Period of analysis (e.g., '7d', '30d')")


class SleepTrendsResponse(BaseModel):
    """Response model for sleep trends analysis."""

    user_id: str = Field(..., description="User ID")
    trends: List[SleepTrend] = Field(..., description="List of identified trends")
    start_date: str = Field(..., description="Start date of analysis")
    end_date: str = Field(..., description="End date of analysis")


class UserInfo(BaseModel):
    """Model for user information."""

    user_id: str = Field(..., description="User identifier")
    record_count: int = Field(..., description="Number of sleep records for this user")
    latest_record_date: Optional[str] = Field(
        None, description="Date of the latest sleep record"
    )


class UsersResponse(BaseModel):
    """Response model for users list."""

    users: List[UserInfo] = Field(..., description="List of users")
    count: int = Field(..., description="Total number of users returned")
