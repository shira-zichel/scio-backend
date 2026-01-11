"""
API Layer for SCiO Backend
FastAPI endpoints for Scan Analysis Reports.
"""

from datetime import datetime
from functools import lru_cache
from typing import List, Optional

from fastapi import FastAPI, Query, HTTPException, Depends

from config import settings
from models import ScanReport
from repository import InMemoryRepository, ScanRepository
from service import ScanReportService
from exceptions import (
    ScanResultsNotFoundError,
    WidgetNotFoundError,
    AlgoNotFoundError,
    InvalidDateRangeError,
    DataLoadError
)


# =============================================================================
# App Initialization
# =============================================================================

app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version
)


# =============================================================================
# Dependency Injection Functions
# =============================================================================

@lru_cache()
def get_repository() -> ScanRepository:
    
    return InMemoryRepository(settings.data_dir)


def get_service(repository: ScanRepository = Depends(get_repository)) -> ScanReportService:
    
    return ScanReportService(repository)


# =============================================================================
# Endpoints
# =============================================================================

@app.get("/")
def root():
    """Health check endpoint."""
    return {"status": "ok", "message": "SCiO Backend API is running"}


@app.get("/scan-reports", response_model=List[ScanReport])
def get_scan_reports(
    user_id: Optional[str] = Query(
        default=None,
        description="Filter by user ID"
    ),
    device_id: Optional[str] = Query(
        default=None,
        description="Filter by device ID"
    ),
    from_date: Optional[datetime] = Query(
        default=None,
        description="Filter scans from this date (ISO format: 2025-11-20T00:00:00)"
    ),
    to_date: Optional[datetime] = Query(
        default=None,
        description="Filter scans until this date (ISO format: 2025-11-30T23:59:59)"
    ),
    # NEW: Service is now injected as a parameter!
    service: ScanReportService = Depends(get_service)
) -> List[ScanReport]:
    
    try:
        # Get reports from service - now injected via Depends()
        reports = service.get_scan_reports(
            user_id=user_id,
            device_id=device_id,
            from_date=from_date,
            to_date=to_date
        )
        
        return reports
    
    except InvalidDateRangeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    except (ScanResultsNotFoundError, WidgetNotFoundError, AlgoNotFoundError) as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    except DataLoadError as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
