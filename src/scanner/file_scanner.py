"""Filesystem scanner for music production components."""

import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Iterator, List, Optional, Set
from tqdm import tqdm

from ..core.logger import get_logger
from ..core.exceptions import ScanException


class FileScanner:
    """Comprehensive filesystem scanner for all music production components."""

    def __init__(
        self,
        exclude_paths: Optional[List[str]] = None,
        max_workers: int = 4,
        verbose: bool = True
    ):
        """
        Initialize file scanner.

        Args:
            exclude_paths: List of paths to exclude from scanning
            max_workers: Maximum number of parallel workers
            verbose: Show progress bars
        """
        self.exclude_paths: Set[Path] = set()
        if exclude_paths:
            self.exclude_paths = {Path(p) for p in exclude_paths}

        self.max_workers = max_workers
        self.verbose = verbose
        self.logger = get_logger()

        self.files_scanned = 0
        self.total_size = 0

    def should_exclude(self, path: Path) -> bool:
        """
        Check if path should be excluded from scanning.

        Args:
            path: Path to check

        Returns:
            True if path should be excluded
        """
        path = Path(path).resolve()

        for exclude_path in self.exclude_paths:
            try:
                exclude_path = exclude_path.resolve()
                # Check if path is under excluded directory
                if path == exclude_path or exclude_path in path.parents:
                    return True
            except (OSError, RuntimeError):
                # Handle cases where path resolution fails
                continue

        return False

    def scan_directory(
        self,
        path: str,
        extensions: List[str],
        recursive: bool = True
    ) -> List[Path]:
        """
        Scan directory for files with specific extensions.

        Args:
            path: Directory path to scan
            extensions: List of file extensions to find (e.g., ['.dll', '.vst3'])
            recursive: Whether to scan subdirectories

        Returns:
            List of matching file paths

        Raises:
            ScanException: If scanning fails
        """
        path = Path(path)

        if not path.exists():
            raise ScanException(f"Path does not exist: {path}")

        if not path.is_dir():
            raise ScanException(f"Path is not a directory: {path}")

        if self.should_exclude(path):
            self.logger.debug(f"Skipping excluded path: {path}")
            return []

        self.logger.info(f"Scanning directory: {path}")

        found_files: List[Path] = []
        extensions_lower = [ext.lower() for ext in extensions]

        try:
            if recursive:
                # Recursive scan
                for root, dirs, files in os.walk(path):
                    root_path = Path(root)

                    # Skip excluded directories
                    if self.should_exclude(root_path):
                        dirs.clear()  # Don't descend into this directory
                        continue

                    # Filter excluded subdirectories
                    dirs[:] = [d for d in dirs if not self.should_exclude(root_path / d)]

                    # Find matching files
                    for file in files:
                        file_path = root_path / file
                        if file_path.suffix.lower() in extensions_lower:
                            found_files.append(file_path)
                            self.files_scanned += 1

                            if file_path.exists():
                                self.total_size += file_path.stat().st_size

            else:
                # Non-recursive scan
                for item in path.iterdir():
                    if item.is_file() and item.suffix.lower() in extensions_lower:
                        found_files.append(item)
                        self.files_scanned += 1

                        if item.exists():
                            self.total_size += item.stat().st_size

        except PermissionError as e:
            self.logger.warning(f"Permission denied: {path} - {e}")
        except Exception as e:
            self.logger.error(f"Error scanning {path}: {e}")
            raise ScanException(f"Failed to scan {path}", {'error': str(e)})

        self.logger.info(f"Found {len(found_files)} files in {path}")
        return found_files

    def scan_for_executables(self, path: str) -> List[Path]:
        """
        Scan for executable files (.exe).

        Args:
            path: Directory path to scan

        Returns:
            List of executable file paths
        """
        return self.scan_directory(path, ['.exe'], recursive=True)

    def scan_parallel(
        self,
        root_paths: List[str],
        extensions: List[str]
    ) -> List[Path]:
        """
        Scan multiple root paths in parallel.

        Args:
            root_paths: List of root directories to scan
            extensions: File extensions to find

        Returns:
            Combined list of all found files

        Example:
            >>> scanner = FileScanner()
            >>> files = scanner.scan_parallel(['C:\\Program Files'], ['.dll', '.vst3'])
        """
        all_files: List[Path] = []

        self.logger.info(f"Starting parallel scan of {len(root_paths)} paths")

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit scan tasks
            future_to_path = {
                executor.submit(self.scan_directory, path, extensions): path
                for path in root_paths
                if Path(path).exists()
            }

            # Progress bar
            if self.verbose:
                futures = tqdm(
                    as_completed(future_to_path),
                    total=len(future_to_path),
                    desc="Scanning directories",
                    unit="dir"
                )
            else:
                futures = as_completed(future_to_path)

            # Collect results
            for future in futures:
                path = future_to_path[future]
                try:
                    files = future.result()
                    all_files.extend(files)
                except ScanException as e:
                    self.logger.error(f"Scan failed for {path}: {e}")
                except Exception as e:
                    self.logger.error(f"Unexpected error scanning {path}: {e}")

        self.logger.info(f"Parallel scan complete. Found {len(all_files)} total files.")
        return all_files

    def find_files_by_pattern(
        self,
        root_path: str,
        pattern: str
    ) -> List[Path]:
        """
        Find files matching a glob pattern.

        Args:
            root_path: Root directory to search
            pattern: Glob pattern (e.g., "**/*.vst3", "**/Presets/**")

        Returns:
            List of matching file paths

        Example:
            >>> scanner = FileScanner()
            >>> presets = scanner.find_files_by_pattern('C:\\', '**/Presets/**/*.vstpreset')
        """
        root = Path(root_path)

        if not root.exists():
            return []

        if self.should_exclude(root):
            return []

        self.logger.info(f"Searching for pattern: {pattern} in {root}")

        matches = []
        try:
            for path in root.glob(pattern):
                if not self.should_exclude(path) and path.is_file():
                    matches.append(path)
        except PermissionError:
            self.logger.warning(f"Permission denied accessing: {root}")
        except Exception as e:
            self.logger.error(f"Error searching pattern {pattern}: {e}")

        self.logger.info(f"Found {len(matches)} files matching pattern")
        return matches

    def get_directory_size(self, path: Path) -> int:
        """
        Calculate total size of directory.

        Args:
            path: Directory path

        Returns:
            Total size in bytes
        """
        total_size = 0

        try:
            for root, dirs, files in os.walk(path):
                root_path = Path(root)

                # Skip excluded directories
                if self.should_exclude(root_path):
                    dirs.clear()
                    continue

                for file in files:
                    try:
                        file_path = root_path / file
                        if file_path.exists() and not file_path.is_symlink():
                            total_size += file_path.stat().st_size
                    except (OSError, PermissionError):
                        continue

        except (PermissionError, OSError) as e:
            self.logger.warning(f"Could not calculate size for {path}: {e}")

        return total_size

    def get_statistics(self) -> dict:
        """
        Get scan statistics.

        Returns:
            Dictionary with scan statistics
        """
        return {
            'files_scanned': self.files_scanned,
            'total_size_bytes': self.total_size,
            'total_size_mb': round(self.total_size / (1024 * 1024), 2),
            'total_size_gb': round(self.total_size / (1024 ** 3), 2),
        }

    def reset_statistics(self) -> None:
        """Reset scan statistics."""
        self.files_scanned = 0
        self.total_size = 0
