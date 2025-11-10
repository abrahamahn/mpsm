"""Base scanner class for all scanner types.

Provides common functionality for folder_scanner and application_scanner.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, TypeVar, Generic, Callable
from concurrent.futures import ThreadPoolExecutor
import platform

from ..core.logger import get_logger
from ..core.config import ConfigManager


# Type variable for the item being scanned (DataFolder, Application, etc.)
T = TypeVar('T')

IS_WINDOWS = platform.system() == 'Windows'


class BaseScanner(ABC, Generic[T]):
    """
    Abstract base class for all scanners.

    Provides common initialization, scanning patterns, and error handling
    that is shared across folder_scanner, application_scanner, etc.

    Type parameter T represents the type of item being scanned
    (e.g., DataFolder, Application).
    """

    def __init__(
        self,
        config: Optional[ConfigManager] = None,
        max_workers: int = 4
    ):
        """
        Initialize scanner.

        Args:
            config: Configuration manager
            max_workers: Maximum parallel scan workers
        """
        self.logger = get_logger()
        self.config = config or ConfigManager()
        self.max_workers = max_workers

        # Discovered items (subclasses should use this)
        self.items: List[T] = []

    @abstractmethod
    def _get_default_scan_paths(self) -> List[str]:
        """
        Get default paths to scan.

        Subclasses must implement this to return appropriate default paths
        (e.g., common application directories, data folders, etc.).

        Returns:
            List of default paths to scan
        """
        pass

    @abstractmethod
    def _identify_item(self, path: Path) -> Optional[T]:
        """
        Identify if path is a valid item.

        Subclasses must implement this to determine if a file/folder
        matches what they're looking for.

        Args:
            path: File or folder path to check

        Returns:
            Item object if identified, None otherwise
        """
        pass

    def scan(
        self,
        scan_paths: Optional[List[str]] = None,
        progress_callback: Optional[Callable[[int], None]] = None
    ) -> List[T]:
        """
        Generic scan implementation.

        Provides common scanning logic:
        - Default path resolution
        - Progress reporting
        - Error handling
        - Parallel processing (if needed by subclass)

        Args:
            scan_paths: Paths to scan. If None, uses default paths.
            progress_callback: Optional callback for progress updates

        Returns:
            List of discovered items
        """
        if scan_paths is None:
            scan_paths = self._get_default_scan_paths()

        self.logger.info(f"Scanning {len(scan_paths)} paths...")
        self.items = []

        for path_str in scan_paths:
            path = Path(path_str)
            if path.exists() and path.is_dir():
                items = self._scan_path(path)
                self.items.extend(items)

                if progress_callback:
                    progress_callback(len(self.items))

        self.logger.info(f"Found {len(self.items)} items")
        return self.items

    def _scan_path(self, path: Path, depth: int = 0, max_depth: int = 4) -> List[T]:
        """
        Scan a single path for items.

        Provides common directory traversal with depth limiting and error handling.

        Args:
            path: Path to scan
            depth: Current recursion depth
            max_depth: Maximum recursion depth

        Returns:
            List of items found in this path
        """
        items = []

        if depth > max_depth:
            return items

        try:
            for item_path in path.iterdir():
                # Try to identify this path
                identified = self._identify_item(item_path)
                if identified:
                    items.append(identified)

                # Recurse into subdirectories
                if item_path.is_dir():
                    sub_items = self._scan_path(item_path, depth + 1, max_depth)
                    items.extend(sub_items)

        except PermissionError:
            self.logger.debug(f"Permission denied: {path}")
        except OSError as e:
            self.logger.debug(f"OS error scanning {path}: {e}")
        except Exception as e:
            self.logger.warning(f"Error scanning {path}: {e}")

        return items

    def get_items(self) -> List[T]:
        """
        Get all discovered items.

        Returns:
            List of discovered items
        """
        return self.items

    def item_count(self) -> int:
        """
        Get count of discovered items.

        Returns:
            Number of items found
        """
        return len(self.items)

    def clear(self):
        """Clear discovered items."""
        self.items = []

    def __len__(self) -> int:
        """Get count of discovered items."""
        return len(self.items)

    def __repr__(self) -> str:
        """String representation."""
        return f"{self.__class__.__name__}(items={len(self.items)})"
