import uuid
from datetime import datetime
from typing import Dict, List, Optional

from loguru import logger
from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config.settings import settings

Base = declarative_base()


class SleepRecord(Base):  # type: ignore
    """SQLAlchemy model for sleep records."""

    __tablename__ = "sleep_records"

    id = Column(String, primary_key=True)
    user_id = Column(String, index=True, nullable=False)
    date = Column(String, index=True, nullable=False)
    sleep_start = Column(DateTime, nullable=False)
    sleep_end = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    sleep_phases = Column(JSON, nullable=True)
    sleep_quality = Column(Integer, nullable=True)
    heart_rate = Column(JSON, nullable=True)
    breathing = Column(JSON, nullable=True)
    environment = Column(JSON, nullable=True)
    tags = Column(JSON, nullable=True)
    notes = Column(String, nullable=True)
    meta_data = Column(JSON, nullable=False)  # Changed from 'meta_data' to 'meta_data'
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self) -> Dict:
        """Convert the record to a dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "date": self.date,
            "sleep_start": self.sleep_start.isoformat(),
            "sleep_end": self.sleep_end.isoformat(),
            "duration_minutes": self.duration_minutes,
            "sleep_phases": self.sleep_phases,
            "sleep_quality": self.sleep_quality,
            "heart_rate": self.heart_rate,
            "breathing": self.breathing,
            "environment": self.environment,
            "tags": self.tags,
            "notes": self.notes,
            "meta_data": self.meta_data,  # Return as 'meta_data' for API consistency
        }


class SleepTimeSeriesPoint(Base):  # type: ignore
    """SQLAlchemy model for sleep time series data points."""

    __tablename__ = "sleep_time_series"

    id = Column(String, primary_key=True)
    sleep_record_id = Column(
        String, ForeignKey("sleep_records.id", ondelete="CASCADE"), index=True
    )
    timestamp = Column(DateTime, nullable=False)
    stage = Column(String, nullable=True)
    heart_rate = Column(Float, nullable=True)
    movement = Column(Float, nullable=True)
    respiration_rate = Column(Float, nullable=True)

    def to_dict(self) -> Dict:
        """Convert the time series point to a dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "stage": self.stage,
            "heart_rate": self.heart_rate,
            "movement": self.movement,
            "respiration_rate": self.respiration_rate,
        }


class DatabaseStorage:
    """PostgreSQL and SQLite database storage service for sleep data."""

    def __init__(self, db_url: Optional[str] = None):
        """
        Initialize the database storage service.

        Args:
            db_url: Optional database connection URL.
                    If not provided, uses settings.DATABASE_URL.
        """
        # Use provided URL or fall back to settings
        self.db_url = db_url or settings.DATABASE_URL

        # For testing with SQLite, use a static connection pool
        if self.db_url.startswith("sqlite"):
            self.engine = create_engine(
                self.db_url,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
            )
        # For PostgreSQL, regular connection
        elif self.db_url.startswith("postgresql"):
            self.engine = create_engine(self.db_url)
        else:
            raise ValueError(
                "Database URL must start with 'sqlite://' or 'postgresql://'"
            )

        self.Session = sessionmaker(bind=self.engine)

        # Create tables if they don't exist
        Base.metadata.create_all(self.engine)

    def save_sleep_records(self, user_id: str, records: List[Dict]) -> bool:
        """Save sleep records to the database."""
        session = self.Session()
        try:
            for record in records:
                # Check if record already exists
                existing = (
                    session.query(SleepRecord)
                    .filter(SleepRecord.id == record.get("id"))
                    .first()
                )

                if existing:
                    # Update existing record
                    for key, value in record.items():
                        if key != "id" and key != "time_series":
                            if key == "meta_data":  # Handle meta_data conversion
                                setattr(existing, "meta_data", value)
                            else:
                                setattr(existing, key, value)
                else:
                    # Create new record
                    if "id" not in record:
                        record["id"] = str(uuid.uuid4())

                    # Extract time series data
                    time_series = record.pop("time_series", [])

                    # Handle meta_data conversion
                    if "meta_data" in record:
                        meta_data = record.pop("meta_data")
                        # Convert datetime objects in meta_data to ISO format strings
                        if isinstance(meta_data, dict):
                            for key, value in meta_data.items():
                                if isinstance(value, datetime):
                                    meta_data[key] = value.isoformat()
                        record["meta_data"] = meta_data

                    # Convert datetime strings to datetime objects
                    if isinstance(record["sleep_start"], str):
                        record["sleep_start"] = datetime.fromisoformat(
                            record["sleep_start"]
                        )
                    if isinstance(record["sleep_end"], str):
                        record["sleep_end"] = datetime.fromisoformat(
                            record["sleep_end"]
                        )

                    # Create record
                    sleep_record = SleepRecord(**record)
                    session.add(sleep_record)

                    # Add time series data
                    for ts_point in time_series:
                        ts_point_id = str(uuid.uuid4())
                        if isinstance(ts_point["timestamp"], str):
                            timestamp = datetime.fromisoformat(ts_point["timestamp"])
                        else:
                            timestamp = ts_point["timestamp"]

                        time_series_record = SleepTimeSeriesPoint(
                            id=ts_point_id,
                            sleep_record_id=record["id"],
                            timestamp=timestamp,
                            stage=ts_point.get("stage"),
                            heart_rate=ts_point.get("heart_rate"),
                            movement=ts_point.get("movement"),
                            respiration_rate=ts_point.get("respiration_rate"),
                        )
                        session.add(time_series_record)

            session.commit()
            return True

        except Exception as e:
            session.rollback()
            logger.error(f"Error saving sleep records to database: {e}")
            return False

        finally:
            session.close()

    def get_sleep_records(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict]:
        """Get sleep records from the database."""
        session = self.Session()
        try:
            query = session.query(SleepRecord).filter(SleepRecord.user_id == user_id)

            if start_date:
                query = query.filter(
                    SleepRecord.date >= start_date.strftime("%Y-%m-%d")
                )

            if end_date:
                query = query.filter(SleepRecord.date <= end_date.strftime("%Y-%m-%d"))

            # Sort by date (newest first)
            query = query.order_by(SleepRecord.date.desc())

            # Apply pagination
            records = query.limit(limit).offset(offset).all()

            # Convert to dictionaries
            result = []
            for record in records:
                record_dict = record.to_dict()

                # Get time series data
                time_series_query = (
                    session.query(SleepTimeSeriesPoint)
                    .filter(SleepTimeSeriesPoint.sleep_record_id == record.id)
                    .order_by(SleepTimeSeriesPoint.timestamp)
                )

                time_series = [ts.to_dict() for ts in time_series_query.all()]
                record_dict["time_series"] = time_series

                result.append(record_dict)

            return result

        except Exception as e:
            logger.error(f"Error getting sleep records from database: {e}")
            return []

        finally:
            session.close()

    def delete_sleep_record(self, user_id: str, record_id: str) -> bool:
        """Delete a sleep record from the database."""
        session = self.Session()
        try:
            # First check if the record exists and belongs to the user
            record = (
                session.query(SleepRecord)
                .filter(SleepRecord.id == record_id, SleepRecord.user_id == user_id)
                .first()
            )

            if not record:
                return False

            # Delete the record (cascade will handle time series data)
            session.delete(record)
            session.commit()

            return True

        except Exception as e:
            session.rollback()
            logger.error(f"Error deleting sleep record from database: {e}")
            return False

        finally:
            session.close()
