"""Filesystem scanner for music production components."""

import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Iterable, List, Optional, Set

from tqdm import tqdm

from ..core.exceptions import ScanException
from ..core.logger import get_logger

if TYPE_CHECKING:
    from ..models.plugin import Plugin
    from .metadata.extractor import MetadataExtractor


class FileScanner:
    """Comprehensive filesystem scanner for all music production components."""

    DEFAULT_PLUGIN_EXTENSIONS = [".dll", ".vst3", ".aax", ".clap"]

    def __init__(
        self, exclude_paths: Optional[List[str]] = None, max_workers: int = 4, verbose: bool = True
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
        resolved_path = Path(path).resolve()

        for exclude_path in self.exclude_paths:
            try:
                resolved_exclude = exclude_path.resolve()
                if resolved_path == resolved_exclude or resolved_exclude in resolved_path.parents:
                    return True
            except (OSError, RuntimeError):
                continue

        return False

    def scan_directory(
        self,
        path: str,
        extensions: List[str],
        recursive: bool = True,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> List[Path]:
        """
        Scan directory for files with specific extensions.

        Args:
            path: Directory path to scan
            extensions: List of file extensions to find (e.g., ['.dll', '.vst3'])
            recursive: Whether to scan subdirectories
            progress_callback: Optional callback function to report current directory being scanned

        Returns:
            List of matching file paths

        Raises:
            ScanException: If scanning fails
        """
        dir_path = Path(path)

        if not dir_path.exists():
            raise ScanException(f"Path does not exist: {dir_path}")

        if not dir_path.is_dir():
            raise ScanException(f"Path is not a directory: {dir_path}")

        if self.should_exclude(dir_path):
            self.logger.debug(f"Skipping excluded path: {dir_path}")
            return []

        self.logger.info(f"Scanning directory: {dir_path}")

        found_files: List[Path] = []
        extensions_lower = [ext.lower() for ext in extensions]

        try:
            if recursive:
                for root, dirs, files in os.walk(dir_path):
                    root_path = Path(root)

                    if progress_callback:
                        progress_callback(str(root_path))

                    if self.should_exclude(root_path):
                        dirs.clear()
                        continue

                    dirs[:] = [d for d in dirs if not self.should_exclude(root_path / d)]

                    for file in files:
                        file_path = root_path / file
                        if file_path.suffix.lower() in extensions_lower:
                            found_files.append(file_path)
                            self.files_scanned += 1

                            if file_path.exists():
                                self.total_size += file_path.stat().st_size
            else:
                for item in dir_path.iterdir():
                    if item.is_file() and item.suffix.lower() in extensions_lower:
                        found_files.append(item)
                        self.files_scanned += 1

                        if item.exists():
                            self.total_size += item.stat().st_size

        except PermissionError as e:
            self.logger.warning(f"Permission denied: {dir_path} - {e}")
        except Exception as e:
            self.logger.error(f"Error scanning {dir_path}: {e}")
            raise ScanException(f"Failed to scan {dir_path}", {"error": str(e)})

        self.logger.info(f"Found {len(found_files)} files in {dir_path}")
        return found_files

    def scan_for_executables(self, path: str) -> List[Path]:
        """
        Scan for executable files (.exe).

        Args:
            path: Directory path to scan

        Returns:
            List of executable file paths
        """
        return self.scan_directory(path, [".exe"], recursive=True)

    def scan_parallel(
        self,
        root_paths: List[str],
        extensions: List[str],
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> List[Path]:
        """
        Scan multiple root paths in parallel.

        Args:
            root_paths: List of root directories to scan
            extensions: File extensions to find
            progress_callback: Optional callback function to report current directory being scanned

        Returns:
            Combined list of all found files
        """
        all_files: List[Path] = []

        self.logger.info(f"Starting parallel scan of {len(root_paths)} paths")

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_path = {
                executor.submit(
                    self.scan_directory, path, extensions, True, progress_callback
                ): path
                for path in root_paths
                if Path(path).exists()
            }

            futures: Iterable = (
                tqdm(
                    as_completed(future_to_path),
                    total=len(future_to_path),
                    desc="Scanning directories",
                    unit="dir",
                )
                if self.verbose
                else as_completed(future_to_path)
            )

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

    def discover_plugins(
        self,
        scan_paths: List[str],
        metadata_extractor: "MetadataExtractor",
        extensions: Optional[List[str]] = None,
        validate: bool = True,
        min_size_mb: float = 0.05,
        max_size_mb: float = 1000.0,
        include_registry: bool = False,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> List["Plugin"]:
        """
        Scan paths for plugin files, validate them, and build Plugin instances.

        Args:
            scan_paths: Directories to scan for plugin files
            metadata_extractor: MetadataExtractor instance
            extensions: Extensions to scan (defaults to DEFAULT_PLUGIN_EXTENSIONS)
            validate: Whether to filter candidates with is_valid_plugin_file
            min_size_mb: Minimum valid plugin size in MB
            max_size_mb: Maximum valid plugin size in MB
            include_registry: Whether to link Windows registry keys
            progress_callback: Optional directory scan progress callback

        Returns:
            List of validated Plugin objects
        """
        target_extensions = extensions or self.DEFAULT_PLUGIN_EXTENSIONS
        candidate_files = self.scan_parallel(scan_paths, target_extensions, progress_callback)

        if validate:
            valid_files = [
                f
                for f in candidate_files
                if metadata_extractor.is_valid_plugin_file(
                    f, min_size_mb=min_size_mb, max_size_mb=max_size_mb
                )
            ]
        else:
            valid_files = candidate_files

        plugins: List["Plugin"] = []
        for file_path in valid_files:
            try:
                plugins.append(
                    metadata_extractor.build_plugin(file_path, include_registry=include_registry)
                )
            except Exception as e:
                self.logger.warning(f"Failed to process {file_path}: {e}")

        return plugins

    def find_files_by_pattern(self, root_path: str, pattern: str) -> List[Path]:
        """
        Find files matching a glob pattern.

        Args:
            root_path: Root directory to search
            pattern: Glob pattern (e.g., "**/*.vst3", "**/Presets/**")

        Returns:
            List of matching file paths
        """
        root = Path(root_path)

        if not root.exists() or self.should_exclude(root):
            return []

        self.logger.info(f"Searching for pattern: {pattern} in {root}")

        matches: List[Path] = []
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
            "files_scanned": self.files_scanned,
            "total_size_bytes": self.total_size,
            "total_size_mb": round(self.total_size / (1024 * 1024), 2),
            "total_size_gb": round(self.total_size / (1024**3), 2),
        }

    def reset_statistics(self) -> None:
        """Reset scan statistics."""
        self.files_scanned = 0
        self.total_size = 0
