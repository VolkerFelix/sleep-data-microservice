"""This module contains the routes for the sleep data API."""

import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import (
    APIRouter,
    Body,
    Depends,
    File,
    HTTPException,
    Path,
    Query,
    UploadFile,
    status,
)
from fastapi.responses import JSONResponse
from loguru import logger

from app.models.sleep_models import (
    GenerateSleepDataRequest,
    SleepAnalyticsResponse,
    SleepDataResponse,
    SleepRecord,
    SleepRecordCreate,
    SleepRecordUpdate,
    UsersResponse,
)
from app.services.extern.apple_health import AppleHealthImporter
from app.services.sleep_service import SleepDataService

router = APIRouter(prefix="/sleep", tags=["sleep"])


def get_storage_service():
    """Get the appropriate storage service based on environment."""
    import os

    from app.config.settings import settings

    # Use the environment variable if available, otherwise use settings
    db_url = os.environ.get("DATABASE_URL", settings.DATABASE_URL)
    logger.debug(f"Creating storage service with DB URL: {db_url}")

    # Create database storage with this URL
    from app.services.storage.db_storage import DatabaseStorage

    return DatabaseStorage(db_url=db_url)


def get_sleep_service(storage_service=Depends(get_storage_service)):
    """Get the sleep data service."""
    return SleepDataService(storage_service=storage_service)


def get_apple_health_importer(storage_service=Depends(get_storage_service)):
    """Get the Apple Health importer."""
    return AppleHealthImporter(storage_service=storage_service)


def _complete_sleep_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensure a sleep record has all required fields and meta_data.

    Args:
        record: Input sleep record dictionary

    Returns:
        Completed sleep record dictionary
    """
    # Ensure original ID is preserved
    original_id = record.get("id")

    # Ensure meta_data is complete
    if "meta_data" not in record or not record["meta_data"]:
        record["meta_data"] = {
            "source": "generated",
            "generated_at": datetime.now().isoformat(),
            "source_name": "Sleep Service",
            "device": None,
            "version": None,
            "imported_at": None,
            "raw_data": None,
        }

    # Ensure all other required fields are present
    required_fields = [
        "user_id",
        "date",
        "sleep_start",
        "sleep_end",
        "duration_minutes",
        "meta_data",
    ]

    for field in required_fields:
        if field not in record:
            # Generate default values for missing fields
            if field == "user_id":
                record[field] = "unknown_user"
            elif field == "date":
                record[field] = datetime.now().strftime("%Y-%m-%d")
            elif field in ["sleep_start", "sleep_end"]:
                record[field] = datetime.now().isoformat()
            elif field == "duration_minutes":
                record[field] = 0

    # Always use the original ID if it exists
    if original_id:
        record["record_id"] = original_id
    else:
        # Generate ID only if not present
        record["record_id"] = str(uuid.uuid4())

    return record


@router.post(
    "/generate", response_model=SleepDataResponse, status_code=status.HTTP_201_CREATED
)
async def generate_sleep_data(
    request: GenerateSleepDataRequest,
    sleep_service: SleepDataService = Depends(get_sleep_service),
    storage_service=Depends(get_storage_service),
):
    """Generate dummy sleep data for a specified date range."""
    try:
        # Print out the request for debugging
        logger.debug(f"Generate sleep data request: {request}")
        logger.debug(f"Include Time Series: {request.include_time_series}")

        sleep_data = sleep_service.generate_dummy_data(
            user_id=request.user_id,
            start_date=request.start_date,
            end_date=request.end_date,
            include_time_series=request.include_time_series,
            sleep_quality_trend=request.sleep_quality_trend,
            sleep_duration_trend=request.sleep_duration_trend,
        )

        # Explicitly log the generated data
        logger.debug(f"Generated Sleep Data: {sleep_data}")

        # Ensure time series is present when requested
        if request.include_time_series:
            for record in sleep_data:
                if "time_series" not in record or record["time_series"] is None:
                    # Forcibly generate time series if missing
                    from app.services.sleep_service import SleepDataService

                    service = SleepDataService()
                    record["time_series"] = service._generate_time_series(
                        record.get("sleep_start", datetime.now()),
                        record.get("sleep_end", datetime.now()),
                        record.get("duration_minutes", 480),
                    )

        # Save the generated data to the database
        success = storage_service.save_sleep_records(request.user_id, sleep_data)
        if not success:
            logger.error("Failed to save generated sleep data to the database")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save generated sleep data to the database",
            )

        return {"records": sleep_data, "count": len(sleep_data)}
    except Exception as e:
        logger.error(f"Error generating sleep data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating sleep data: {str(e)}",
        )


@router.post("/import/apple_health", status_code=status.HTTP_201_CREATED)
async def import_apple_health_data(
    user_id: str = Query(
        ..., description="User ID to associate with the imported data"
    ),
    file: UploadFile = File(..., description="Apple Health Export XML file"),
    importer: AppleHealthImporter = Depends(get_apple_health_importer),
):
    """Import sleep data from an Apple Health export file."""
    try:
        contents = await file.read()
        apple_health_data = contents.decode("utf-8")

        import_result = importer.import_from_xml(user_id, apple_health_data)

        return import_result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error importing Apple Health file: {str(e)}",
        )


@router.get("/data", response_model=SleepDataResponse)
async def get_sleep_data(
    user_id: str = Query(..., description="User ID to retrieve sleep data for"),
    start_date: Optional[datetime] = Query(
        None, description="Start date for data retrieval"
    ),
    end_date: Optional[datetime] = Query(
        None, description="End date for data retrieval"
    ),
    limit: int = Query(100, description="Maximum number of records to return"),
    offset: int = Query(0, description="Number of records to skip"),
    sleep_service: SleepDataService = Depends(get_sleep_service),
):
    """Get sleep data for a specific user and date range."""
    try:
        sleep_data = sleep_service.get_sleep_data(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset,
        )

        return {"records": sleep_data, "count": len(sleep_data)}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving sleep data: {str(e)}",
        )


@router.get("/analytics", response_model=SleepAnalyticsResponse)
async def analyze_sleep_data(
    user_id: str = Query(..., description="User ID to analyze sleep data for"),
    start_date: datetime = Query(..., description="Start date for analysis"),
    end_date: datetime = Query(..., description="End date for analysis"),
    sleep_service: SleepDataService = Depends(get_sleep_service),
):
    """Analyze sleep data for a specific user and date range."""
    try:
        analysis = sleep_service.analyze_sleep_data(
            user_id=user_id, start_date=start_date, end_date=end_date
        )

        if "error" in analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=analysis["error"]
            )

        return analysis
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing sleep data: {str(e)}",
        )


@router.post(
    "/records", response_model=SleepRecord, status_code=status.HTTP_201_CREATED
)
async def create_sleep_record(
    record: SleepRecordCreate, storage_service=Depends(get_storage_service)
):
    """Create a new sleep record."""
    try:
        # Convert to dict and add ID
        record_dict = record.dict()
        record_dict["record_id"] = str(uuid.uuid4())

        # Save to storage
        success = storage_service.save_sleep_records(record.user_id, [record_dict])

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save sleep record",
            )

        return record_dict
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating sleep record: {str(e)}",
        )


@router.put("/records/{record_id}", response_model=SleepRecord)
async def update_sleep_record(
    record_id: str = Path(..., description="ID of the sleep record to update"),
    record_update: SleepRecordUpdate = Body(...),
    user_id: str = Query(..., description="User ID the record belongs to"),
    storage_service=Depends(get_storage_service),
):
    """Update an existing sleep record."""
    try:
        # Get existing record
        records = storage_service.get_sleep_records(user_id=user_id, limit=1, offset=0)

        existing_record = next(
            (r for r in records if r.get("record_id") == record_id), None
        )

        if not existing_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sleep record with ID {record_id} not found",
            )

        # Update fields
        update_data = record_update.dict(exclude_unset=True)
        for key, value in update_data.items():
            if value is not None:
                existing_record[key] = value

        # Save updated record
        success = storage_service.save_sleep_records(user_id, [existing_record])

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update sleep record",
            )

        return existing_record
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating sleep record: {str(e)}",
        )


@router.delete("/records/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sleep_record(
    record_id: str = Path(..., description="ID of the sleep record to delete"),
    user_id: str = Query(..., description="User ID the record belongs to"),
    storage_service=Depends(get_storage_service),
):
    """Delete a sleep record."""
    try:
        success = storage_service.delete_sleep_record(user_id, record_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sleep record with ID {record_id} not found",
            )

        return JSONResponse(status_code=status.HTTP_204_NO_CONTENT, content={})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting sleep record: {str(e)}",
        )


@router.get("/debug")
async def debug_storage(
    user_id: str = Query(..., description="User ID to retrieve sleep data for"),
    storage_service=Depends(get_storage_service),
):
    """Debug endpoint to directly check the storage service."""
    try:
        # Try to get records for this user
        records = storage_service.get_sleep_records(user_id=user_id)

        # Return diagnostic information
        return {
            "service_type": type(storage_service).__name__,
            "db_url": getattr(storage_service, "db_url", "Unknown"),
            "records_count": len(records),
            "record_ids": [r.get("record_id") for r in records],
            "success": True,
        }
    except Exception as e:
        return {
            "service_type": type(storage_service).__name__,
            "error": str(e),
            "success": False,
        }


@router.get("/users", response_model=UsersResponse)
async def get_users(
    limit: int = Query(100, description="Maximum number of users to return"),
    offset: int = Query(0, description="Number of users to skip"),
    storage_service=Depends(get_storage_service),
):
    """Get a list of unique users with their record counts."""
    try:
        users = storage_service.get_users(limit=limit, offset=offset)

        # Add metadata about the latest sleep record date for each user
        for user in users:
            user_id = user["user_id"]
            # Get the most recent record for this user
            recent_records = storage_service.get_sleep_records(
                user_id=user_id, limit=1, offset=0
            )
            if recent_records:
                user["latest_record_date"] = recent_records[0].get("date")
            else:
                user["latest_record_date"] = None

        return {"users": users, "count": len(users)}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving users: {str(e)}",
        )
