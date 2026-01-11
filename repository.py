"""
Repository Layer for SCiO Backend
Abstracts data access - can be swapped between InMemory, SQLite, etc.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional
import pandas as pd

from pydantic import ValidationError

from models import Scan, ScanResult, Algo, Widget
from exceptions import DataLoadError


# =============================================================================
# Abstract Repository Interface
# =============================================================================

class ScanRepository(ABC):
    """
    Abstract interface for scan data access.
    Any implementation (InMemory, SQLite, PostgreSQL) must implement these methods.
    """
    
    @abstractmethod
    def get_all_scans(self) -> List[Scan]:
        """Get all scans."""
        pass
    
    @abstractmethod
    def get_scans_filtered(
        self,
        user_id: Optional[str] = None,
        device_id: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None
    ) -> List[Scan]:
        """Get scans with optional filters."""
        pass
    
    @abstractmethod
    def get_scan_results_by_scan_ids(self, scan_ids: set[int]) -> dict[int, list[ScanResult]]:
        pass
    
    @abstractmethod
    def get_widgets_by_ids(self, widget_ids: set[int]) -> dict[int, Widget]:
        pass
    
    @abstractmethod
    def get_algos_by_ids(self, algo_ids: set[int]) -> dict[int, Algo]:
        pass


# =============================================================================
# In-Memory Implementation (loads from Excel files)
# =============================================================================

class InMemoryRepository(ScanRepository):
    """
    In-memory implementation that loads data from Excel files.
    Data is stored in dictionaries for fast lookup.
    Uses LAZY LOADING - data is only loaded when first accessed.
    """
    
    def __init__(self, data_dir: str = "."):
        """
        Initialize repository. Data is NOT loaded here (lazy loading).
        
        Args:
            data_dir: Directory containing the Excel files
        """
        self._data_dir = data_dir
        self._loaded = False  # Flag to track if data was loaded
        
        # Data containers (empty until _ensure_loaded is called)
        self._scans: dict[int, Scan] = {}
        self._scan_results: dict[int, List[ScanResult]] = {}
        self._widgets: dict[int, Widget] = {}
        self._algos: dict[int, Algo] = {}
    
    def _ensure_loaded(self) -> None:
        """
        Ensure data is loaded. Only loads once (lazy loading).
        Called automatically before any data access.
        """
        if not self._loaded:
            self._load_data(self._data_dir)
            self._loaded = True
    
    def _load_data(self, data_dir: str) -> None:
        """Load all data from Excel files."""
        self._load_algos(f"{data_dir}/Algo data.xlsx")
        self._load_widgets(f"{data_dir}/Widget data.xlsx")
        self._load_scans(f"{data_dir}/Scan data.xlsx")
        self._load_scan_results(f"{data_dir}/Scan Results data.xlsx")
    
    def _load_algos(self, file_path: str) -> None:
        """Load Algo data from Excel."""
        try:
            df = pd.read_excel(file_path)
            for _, row in df.iterrows():
                algo = Algo(
                    id=row['id'],
                    name=row['name'],
                    parameters=row['parameters'],
                    version=row['version']
                )
                self._algos[algo.id] = algo
        except FileNotFoundError:
            raise DataLoadError(file_path, "File not found")
        except KeyError as e:
            raise DataLoadError(file_path, f"Missing required column: {e}")
        except ValidationError as e:
            raise DataLoadError(file_path, f"Invalid data format: {e}")
        except Exception as e:
            raise DataLoadError(file_path, str(e))
    
    def _load_widgets(self, file_path: str) -> None:
        """Load Widget data from Excel."""
        try:
            df = pd.read_excel(file_path)
            for _, row in df.iterrows():
                widget = Widget(
                    id=row['id'],
                    name=row['name'],
                    algo_id=row['algo_id'],
                    parameters=row['parameters'],
                    param_order=row['param_order'],
                    version=row['version']
                )
                self._widgets[widget.id] = widget
        except FileNotFoundError:
            raise DataLoadError(file_path, "File not found")
        except KeyError as e:
            raise DataLoadError(file_path, f"Missing required column: {e}")
        except ValidationError as e:
            raise DataLoadError(file_path, f"Invalid data format: {e}")
        except Exception as e:
            raise DataLoadError(file_path, str(e))
    
    def _load_scans(self, file_path: str) -> None:
        """Load Scan data from Excel."""
        try:
            df = pd.read_excel(file_path)
            for _, row in df.iterrows():
                gps_location = None
                if 'gps_location' in df.columns:
                    gps_value = row['gps_location']
                    if pd.notna(gps_value):
                        gps_location = str(gps_value)
                
                scan = Scan(
                    id=row['id'],
                    device_id=row['device_id'],
                    user_id=row['user_id'],
                    widget_id=row['widget_id'],
                    algo_id=row['algo_id'],
                    sampled_at=row['sampled_at'],
                    gps_location=gps_location
                )
                self._scans[scan.id] = scan
        except FileNotFoundError:
            raise DataLoadError(file_path, "File not found")
        except KeyError as e:
            raise DataLoadError(file_path, f"Missing required column: {e}")
        except ValidationError as e:
            raise DataLoadError(file_path, f"Invalid data format: {e}")
        except Exception as e:
            raise DataLoadError(file_path, str(e))
    
    def _load_scan_results(self, file_path: str) -> None:
        """Load ScanResult data from Excel."""
        try:
            df = pd.read_excel(file_path)
            for _, row in df.iterrows():
                result = ScanResult(
                    scan_id=row['scan_id'],
                    parameter_name=row['parameter_name'],
                    predicted_value=row['predicted_value']
                )
                if result.scan_id not in self._scan_results:
                    self._scan_results[result.scan_id] = []
                self._scan_results[result.scan_id].append(result)
        except FileNotFoundError:
            raise DataLoadError(file_path, "File not found")
        except KeyError as e:
            raise DataLoadError(file_path, f"Missing required column: {e}")
        except ValidationError as e:
            raise DataLoadError(file_path, f"Invalid data format: {e}")
        except Exception as e:
            raise DataLoadError(file_path, str(e))
    
    # -------------------------------------------------------------------------
    # Interface Implementation (all methods call _ensure_loaded first)
    # -------------------------------------------------------------------------
    
    def get_all_scans(self) -> List[Scan]:
        """Get all scans."""
        self._ensure_loaded()  # Lazy load
        return list(self._scans.values())
    
    def get_scans_filtered(
        self,
        user_id: Optional[str] = None,
        device_id: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None
    ) -> List[Scan]:
        """
        Get scans with optional filters.
        All filters are optional - if not provided, that filter is ignored.
        """
        results = self.get_all_scans()
        
        if user_id is not None:
            results = [s for s in results if s.user_id == user_id]
        
        if device_id is not None:
            results = [s for s in results if s.device_id == device_id]
        
        if from_date is not None:
            results = [s for s in results if s.sampled_at >= from_date]
        
        if to_date is not None:
            results = [s for s in results if s.sampled_at <= to_date]
        
        return results
    
    def get_scan_results_by_scan_ids(self, scan_ids: set[int]) -> dict[int, list[ScanResult]]:
        """Get all results for a specific scan."""
        self._ensure_loaded()  # Lazy load
        return {
            scan_id: self._scan_results[scan_id]
            for scan_id in scan_ids
            if scan_id in self._scan_results
        }
    
    def get_widgets_by_ids(self, widget_ids: set[int]) -> dict[int, Widget]:
        """Get widget by ID."""
        self._ensure_loaded()  # Lazy load
        return {
            widget_id: self._widgets[widget_id]
            for widget_id in widget_ids
            if widget_id in self._widgets
        }
    
    def get_algos_by_ids(self, algo_ids: set[int]) -> dict[int, Algo]:
        """Get algo by ID."""
        self._ensure_loaded()  # Lazy load
        return {
            algo_id: self._algos[algo_id]
            for algo_id in algo_ids
            if algo_id in self._algos
        }
