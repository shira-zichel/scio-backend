"""
Service Layer for SCiO Backend
Contains business logic for generating Scan Analysis Reports.
"""

import re
from datetime import datetime
from typing import Dict, List, Optional

from models import Algo, Scan, ScanReport, ScanResult, Widget
from repository import ScanRepository
from exceptions import (
    ScanResultsNotFoundError,
    WidgetNotFoundError,
    AlgoNotFoundError,
    InvalidDateRangeError
)


class ScanReportService:
    """
    Business logic for generating Scan Analysis Reports.
    Uses repository for data access (dependency injection).
    """
    
    def __init__(self, repository: ScanRepository):
        """
        Initialize service with a repository.
        """
        self._repository = repository
    
    def get_scan_reports(
        self,
        user_id: Optional[str] = None,
        device_id: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None
    ) -> List[ScanReport]:
        """
        Get scan analysis reports with optional filters.
       """
        # Validate date range
        if from_date and to_date and from_date > to_date:
            raise InvalidDateRangeError()
        
        # Step 1: Get filtered scans from repository
        scans = self._repository.get_scans_filtered(
            user_id=user_id,
            device_id=device_id,
            from_date=from_date,
            to_date=to_date
        )
        # Collect all needed IDs
        widget_ids = {s.widget_id for s in scans}
        algo_ids = {s.algo_id for s in scans}
        scan_ids = {s.id for s in scans}
    
        # Batch load
        widgets = self._repository.get_widgets_by_ids(widget_ids)
        algos = self._repository.get_algos_by_ids(algo_ids)
        results = self._repository.get_scan_results_by_scan_ids(scan_ids)

        # Validate that all required data exists
        for scan in scans:
            if scan.widget_id not in widgets:
                raise WidgetNotFoundError(scan.widget_id)
            if scan.algo_id not in algos:
                raise AlgoNotFoundError(scan.algo_id)
            if scan.id not in results:
                raise ScanResultsNotFoundError(scan.id)
        
        # Step 2: Build report for each scan
        reports = []
        for scan in scans:
            report = self._build_scan_report(
                scan,
                widgets[scan.widget_id],
                algos[scan.algo_id],
                results[scan.id]
            )
            reports.append(report)  # Now INSIDE the loop
        
        # Step 3: Sort by sampled_at (newest first)
        reports.sort(key=lambda r: r.sampled_at, reverse=True)
        
        return reports
    
    def _build_scan_report(
        self, 
        scan: Scan, 
        widget: Widget, 
        algo: Algo, 
        results: List[ScanResult]
    ) -> ScanReport:
        """
        Build a complete ScanReport from a Scan object.
        Combines scan data with results, widget, and algo info.
        
        Note: Validation that widget, algo, and results exist is done
        in get_scan_reports() before calling this method.
        """
    
        
        # Build results dictionary {display_name: formatted_value}
        results_dict = self._build_results_dict(results, widget)
        
        # Create the report (field order matches expected structure)
        return ScanReport(
            sampled_at=scan.sampled_at.strftime("%Y-%m-%d %H:%M:%S"),
            user_id=scan.user_id,
            device_id=scan.device_id,
            widget_name=widget.name,
            algo_name=algo.name,
            results=results_dict
        )
    
    def _build_results_dict(self, scan_results, widget) -> Dict[str, str]:
        """
        Build results dictionary with formatted values.
        
        Output format: {"Protein": "22.10", "Oil": "14.5 %"}
        """
        # Parse widget parameters for display info
        param_display_info = self._parse_widget_parameters(widget.parameters)
        
        # Parse param_order from widget
        param_order = self._parse_param_order(widget.param_order)
        
        # Create temporary dict with results
        temp_results = {}
        for result in scan_results:
            param_name = result.parameter_name.strip()  # Remove any whitespace
            display_info = param_display_info.get(param_name, {})
            
            display_name = display_info.get('display_name', param_name.capitalize())
            unit = display_info.get('unit', '')
            
            # Format the value based on unit
            formatted_value = self._format_value(result.predicted_value, unit)
            
            temp_results[param_name] = {
                'display_name': display_name,
                'formatted_value': formatted_value
            }
        
        # Build ordered results dictionary
        results_dict = {}
        
        # First, add results in param_order
        for param_name in param_order:
            if param_name in temp_results:
                info = temp_results[param_name]
                results_dict[info['display_name']] = info['formatted_value']
        
        # Then, add any remaining results not in param_order
        for param_name, info in temp_results.items():
            if param_name not in param_order:
                results_dict[info['display_name']] = info['formatted_value']
        
        return results_dict
    
    # Mapping of unit types to format functions (cleaner than if/elif chain)
    _FORMAT_MAP = {
        '%': lambda v: f"{v} %",
        'float_1_dig': lambda v: f"{v:.1f}",
        'float_2_dig': lambda v: f"{v:.2f}",
    }
    
    def _format_value(self, value: float, unit: str) -> str:
        """
        Format value based on unit specification.
        
        - "%" -> "16.5 %"
        - "float_1_dig" -> "14.5"
        - "float_2_dig" -> "22.10"
        """
        formatter = self._FORMAT_MAP.get(unit)
        if formatter:
            return formatter(value)
        return str(value)  # Default: return as-is
    
    def _parse_widget_parameters(self, parameters) -> dict:
        """
        Parse widget parameters string into a lookup dictionary.
        
        Input: "[ {name: moisture, display_name: Moisture, unit: %} ]"
        Output: {"moisture": {"display_name": "Moisture", "unit": "%"}}
        """
        result = {}
        
        if not parameters or not isinstance(parameters, str):
            return result
        
        # Find all parameter blocks
        blocks = re.findall(r'\{([^}]+)\}', parameters)
        
        for block in blocks:
            # Extract fields
            name_match = re.search(r'name:\s*(\w+)', block)
            display_match = re.search(r'display_name:\s*(\w+)', block)
            unit_match = re.search(r'unit:\s*([^,}\s]+)', block)
            
            if name_match:
                name = name_match.group(1)
                result[name] = {
                    'display_name': display_match.group(1) if display_match else name.capitalize(),
                    'unit': unit_match.group(1) if unit_match else ''
                }
        
        return result
    
    def _parse_param_order(self, param_order) -> List[str]:
        """
        Parse param_order string into a list.
        
        Input: "[protein, moisture]"
        Output: ["protein", "moisture"]
        """
        if not param_order or not isinstance(param_order, str):
            return []
        
        # Extract words from the string
        return re.findall(r'\w+', param_order)
