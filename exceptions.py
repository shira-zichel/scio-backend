"""
Custom Exceptions for SCiO Backend

These exceptions are raised in the Service layer and caught in the API layer
to provide meaningful HTTP error responses.
"""


class SCiOBaseException(Exception):
    """Base exception for all SCiO-specific errors."""
    pass


# =============================================================================
# Not Found Exceptions (404)
# =============================================================================

class ScanResultsNotFoundError(SCiOBaseException):
    """Raised when a requested scan does not exist."""
    def __init__(self, scan_id: int):
        self.scan_id = scan_id
        super().__init__(f"Scan results with id {scan_id} not found")


class WidgetNotFoundError(SCiOBaseException):
    """Raised when a widget associated with a scan does not exist."""
    def __init__(self, widget_id: int):
        self.widget_id = widget_id
        super().__init__(f"Widget with id {widget_id} not found")


class AlgoNotFoundError(SCiOBaseException):
    """Raised when an algo associated with a scan does not exist."""
    def __init__(self, algo_id: int):
        self.algo_id = algo_id
        super().__init__(f"Algo with id {algo_id} not found")


# =============================================================================
# Validation Exceptions (400)
# =============================================================================

class InvalidDateRangeError(SCiOBaseException):
    """Raised when from_date is after to_date."""
    def __init__(self):
        super().__init__("from_date cannot be after to_date")


class InvalidParameterError(SCiOBaseException):
    """Raised when a request parameter is invalid."""
    def __init__(self, param_name: str, message: str):
        self.param_name = param_name
        super().__init__(f"Invalid parameter '{param_name}': {message}")


# =============================================================================
# Data Loading Exceptions (500)
# =============================================================================

class DataLoadError(SCiOBaseException):
    """Raised when data cannot be loaded from files."""
    def __init__(self, file_path: str, message: str):
        self.file_path = file_path
        super().__init__(f"Failed to load data from '{file_path}': {message}")
