"""
Data Models for SCiO Backend
These are the 4 main classes that represent our data,
plus report structures for API responses.

All models use Pydantic for validation and serialization.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class Scan(BaseModel):
    """
    Represents a single scan event.
    Stores WHO scanned, WHEN, and with WHICH device/settings.
    """
    id: int = Field(..., gt=0, description="Unique scan identifier")
    device_id: str = Field(..., min_length=1, description="Device identifier")
    user_id: str = Field(..., min_length=1, description="User identifier")
    widget_id: int = Field(..., gt=0, description="Widget reference")
    algo_id: int = Field(..., gt=0, description="Algorithm reference")
    sampled_at: datetime = Field(..., description="When the scan occurred")
    gps_location: Optional[str] = Field(default=None, description="GPS coordinates 'lat, lon'")
    
    model_config = ConfigDict(frozen=True)


class ScanResult(BaseModel):
    """
    Represents one prediction result from a scan.
    One Scan can have multiple ScanResults (one per parameter).
    """
    scan_id: int = Field(..., gt=0, description="Reference to parent scan")
    parameter_name: str = Field(..., min_length=1, description="Name of the parameter")
    predicted_value: float = Field(..., description="Predicted value from ML model")
    
    model_config = ConfigDict(frozen=True)


class Algo(BaseModel):
    """
    Contains ML models for a specific crop.
    Defines HOW to calculate predictions.
    """
    id: int = Field(..., gt=0, description="Unique algo identifier")
    name: str = Field(..., min_length=1, description="Algorithm name")
    parameters: Any = Field(..., description="Algorithm parameters [{name, model}, ...]")
    version: int = Field(..., ge=1, description="Version number")
    
    model_config = ConfigDict(frozen=True)


class Widget(BaseModel):
    """
    Contains display settings for a crop.
    Defines HOW to display results to user.
    """
    id: int = Field(..., gt=0, description="Unique widget identifier")
    name: str = Field(..., min_length=1, description="Widget name")
    algo_id: int = Field(..., gt=0, description="Reference to algorithm")
    parameters: Any = Field(..., description="Display parameters [{name, display_name, unit}, ...]")
    param_order: Any = Field(..., description="Order of parameters for display")
    version: int = Field(..., ge=1, description="Version number")
    
    model_config = ConfigDict(frozen=True)


# =============================================================================
# Report Structures (for API responses)
# =============================================================================

class ScanReport(BaseModel):
    """
    Complete scan analysis report for API response.
    Matches expected structure:
    - sampled_at, user_id, device_id, widget_name, algo_name
    - results: {display_name: formatted_value}
    """
    sampled_at: str = Field(..., description="Timestamp in format: YYYY-MM-DD HH:MM:SS")
    user_id: str = Field(..., description="User who performed the scan")
    device_id: str = Field(..., description="Device used for scanning")
    widget_name: str = Field(..., description="Name of the widget")
    algo_name: str = Field(..., description="Name of the algorithm")
    results: Dict[str, str] = Field(..., description="Results as {display_name: 'value unit'}")
