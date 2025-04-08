from datetime import datetime
from typing import List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status, Body, File, UploadFile, Path
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.models.sleep_models import (
    SleepDataResponse,
    SleepRecord, 
    SleepRecordCreate,
    SleepRecordUpdate,
    GenerateSleepDataRequest,
    SleepAnalyticsResponse,
    AppleHealthImportRequest,
    SleepCorrelationResponse,
    SleepTrendsResponse
)
from app.services.sleep_service import SleepDataService
from app.services.import.apple_health import AppleHealthImporter
from app.services.storage.factory import StorageFactory

router = APIRouter(prefix="/sleep", tags=["sleep"])

# Service dependencies
def get_storage_service():
    return StorageFactory.get_storage_service()

def get_sleep_service(storage_service = Depends(get_storage_service)):
    return SleepDataService(storage_service=storage_service)

def get_apple_health_importer(storage_service = Depends(get_storage_service)):
    return AppleHealthImporter(storage_service=storage_service)

def get_correlation_service(storage_service = Depends(get_storage_service)):
    return SleepCalendarCorrelationService(storage_service=storage_service)

@router.post("/generate", response_model=SleepDataResponse, status_code=status.HTTP_201_CREATED)
async def generate_sleep_data(
    request: GenerateSleepDataRequest,
    sleep_service: SleepDataService = Depends(get_sleep_service)
):
    """Generate dummy sleep data for a specified date range."""
    try:
        sleep_data = sleep_service.generate_dummy_data(
            user_id=request.user_id,
            start_date=request.start_date,
            end_date=request.end_date,
            include_time_series=request.include_time_series,
            sleep_quality_trend=request.sleep_quality_trend,
            sleep_duration_trend=request.sleep_duration_trend
        )
        
        return {
            "records": sleep_data,
            "count": len(sleep_data)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating sleep data: {str(e)}"
        )

@router.post("/import/apple_health", status_code=status.HTTP_201_CREATED)
async def import_apple_health_data(
    user_id: str = Query(..., description="User ID to associate with the imported data"),
    file: UploadFile = File(..., description="Apple Health Export XML file"),
    importer: AppleHealthImporter = Depends(get_apple_health_importer)
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
            detail=f"Error importing Apple Health file: {str(e)}"
        )

@router.get("/data", response_model=SleepDataResponse)
async def get_sleep_data(
    user_id: str = Query(..., description="User ID to retrieve sleep data for"),
    start_date: Optional[datetime] = Query(None, description="Start date for data retrieval"),
    end_date: Optional[datetime] = Query(None, description="End date for data retrieval"),
    limit: int = Query(100, description="Maximum number of records to return"),
    offset: int = Query(0, description="Number of records to skip"),
    sleep_service: SleepDataService = Depends(get_sleep_service)
):
    """Get sleep data for a specific user and date range."""
    try:
        sleep_data = sleep_service.get_sleep_data(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset
        )
        
        return {
            "records": sleep_data,
            "count": len(sleep_data)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving sleep data: {str(e)}"
        )

@router.get("/analytics", response_model=SleepAnalyticsResponse)
async def analyze_sleep_data(
    user_id: str = Query(..., description="User ID to analyze sleep data for"),
    start_date: datetime = Query(..., description="Start date for analysis"),
    end_date: datetime = Query(..., description="End date for analysis"),
    sleep_service: SleepDataService = Depends(get_sleep_service)
):
    """Analyze sleep data for a specific user and date range."""
    try:
        analysis = sleep_service.analyze_sleep_data(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date
        )
        
        if "error" in analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=analysis["error"]
            )
        
        return analysis
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing sleep data: {str(e)}"
        )

@router.post("/records", response_model=SleepRecord, status_code=status.HTTP_201_CREATED)
async def create_sleep_record(
    record: SleepRecordCreate,
    storage_service = Depends(get_storage_service)
):
    """Create a new sleep record."""
    try:
        # Convert to dict and add ID
        record_dict = record.dict()
        record_dict["id"] = str(uuid.uuid4())

        # Save to storage
        success = storage_service.save_sleep_records(record.user_id, [record_dict])
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save sleep record"
            )
        
        return record_dict
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating sleep record: {str(e)}"
        )

@router.put("/records/{record_id}", response_model=SleepRecord)
async def update_sleep_record(
    record_id: str = Path(..., description="ID of the sleep record to update"),
    record_update: SleepRecordUpdate = Body(...),
    user_id: str = Query(..., description="User ID the record belongs to"),
    storage_service = Depends(get_storage_service)
):
    """Update an existing sleep record."""
    try:
        # Get existing record
        records = storage_service.get_sleep_records(
            user_id=user_id,
            limit=1,
            offset=0
        )
        
        existing_record = next((r for r in records if r.get("id") == record_id), None)
        
        if not existing_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sleep record with ID {record_id} not found"
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
                detail="Failed to update sleep record"
            )
        
        return existing_record
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating sleep record: {str(e)}"
        )

@router.delete("/records/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sleep_record(
    record_id: str = Path(..., description="ID of the sleep record to delete"),
    user_id: str = Query(..., description="User ID the record belongs to"),
    storage_service = Depends(get_storage_service)
):
    """Delete a sleep record."""
    try:
        success = storage_service.delete_sleep_record(user_id, record_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sleep record with ID {record_id} not found"
            )
        
        return JSONResponse(status_code=status.HTTP_204_NO_CONTENT, content={})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting sleep record: {str(e)}"
        )