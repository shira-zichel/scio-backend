"""
Unit Tests for SCiO Backend
Tests for the get_scan_reports() business logic method.
"""

import pytest
from datetime import datetime

from repository import InMemoryRepository
from service import ScanReportService
from exceptions import InvalidDateRangeError


@pytest.fixture
def service():
    """Create a service instance with test data."""
    repo = InMemoryRepository("data")
    return ScanReportService(repo)


class TestGetScanReports:
    """
    Unit tests for the get_scan_reports() business logic method.
    This method filters scans and builds reports with formatted results.
    """
    
    def test_get_all_reports_no_filters(self, service):
        reports = service.get_scan_reports()
        
        assert len(reports) == 8
        assert all(hasattr(r, 'user_id') for r in reports)
        assert all(hasattr(r, 'results') for r in reports)
    
    def test_filter_by_user_id(self, service):
        reports = service.get_scan_reports(user_id="ariel")
        
        assert len(reports) == 5
        assert all(r.user_id == "ariel" for r in reports)
    
    def test_filter_by_device_id(self, service):
        reports = service.get_scan_reports(device_id="d2")
        
        assert len(reports) == 3
        assert all(r.device_id == "d2" for r in reports)
    
    def test_filter_by_multiple_criteria(self, service):
        reports = service.get_scan_reports(user_id="ariel", device_id="d2")
        
        assert len(reports) == 2
        assert all(r.user_id == "ariel" for r in reports)
        assert all(r.device_id == "d2" for r in reports)
    
    def test_filter_by_date_range(self, service):
        from_date = datetime(2025, 11, 25)
        reports = service.get_scan_reports(from_date=from_date)
        
        assert len(reports) == 3
        # sampled_at is now a formatted string, so compare as strings
        from_date_str = from_date.strftime("%Y-%m-%d %H:%M:%S")
        assert all(r.sampled_at >= from_date_str for r in reports)


class TestDateValidation:
    """
    Unit tests for date range validation.
    """
    
    def test_invalid_date_range_raises_error(self, service):
        """Test that InvalidDateRangeError is raised when from_date > to_date."""
        from_date = datetime(2025, 11, 30)
        to_date = datetime(2025, 11, 20)
        
        with pytest.raises(InvalidDateRangeError):
            service.get_scan_reports(from_date=from_date, to_date=to_date)
    
    def test_valid_date_range_works(self, service):
        """Test that valid date range does not raise error."""
        from_date = datetime(2025, 11, 20)
        to_date = datetime(2025, 11, 30)
        
        reports = service.get_scan_reports(from_date=from_date, to_date=to_date)
        assert isinstance(reports, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
