"""Safe file mover with backup and verification."""

import hashlib
import shutil
import time
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from ..core.exceptions import DiskSpaceException, FileOperationException
from ..core.logger import get_logger


@dataclass
class MoveOperation:
    """Represents a file/folder move operation."""

    operation_id: str
    source: Path
    destination: Path
    is_folder: bool
    size_bytes: int
    completed: bool = False
    backed_up: bool = False
    backup_path: Optional[Path] = None
    error: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "operation_id": self.operation_id,
            "source": str(self.source),
            "destination": str(self.destination),
            "is_folder": self.is_folder,
            "size_mb": round(self.size_bytes / (1024 * 1024), 2),
            "completed": self.completed,
            "backed_up": self.backed_up,
            "error": self.error or "",
        }


@dataclass
class BatchResult:
    """Results from batch move operation."""

    total_operations: int
    successful: int
    failed: int
    operations: List[MoveOperation]
    total_size_bytes: int
    duration_seconds: float

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "total_operations": self.total_operations,
            "successful": self.successful,
            "failed": self.failed,
            "total_size_mb": round(self.total_size_bytes / (1024 * 1024), 2),
            "duration_seconds": round(self.duration_seconds, 2),
        }


class FileMover:
    """Safely moves files with backup and verification."""

    def __init__(
        self, backup_dir: Optional[Path] = None, verify_moves: bool = True, dry_run: bool = False
    ):
        """
        Initialize file mover.

        Args:
            backup_dir: Directory for backups. If None, uses backups/files in project root
            verify_moves: Verify files after moving
            dry_run: Don't actually move files, just simulate
        """
        if backup_dir is None:
            project_root = Path(__file__).parent.parent.parent
            backup_dir = project_root / "backups" / "files"

        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        self.verify_moves = verify_moves
        self.dry_run = dry_run
        self.logger = get_logger()

        # Track operations
        self.operations: List[MoveOperation] = []

    def move_file(self, source: Path, destination: Path, backup: bool = True) -> MoveOperation:
        """
        Move a single file with optional backup.

        Args:
            source: Source file path
            destination: Destination file path
            backup: Create backup before moving

        Returns:
            MoveOperation result

        Raises:
            FileOperationException: If move fails
        """
        operation = MoveOperation(
            operation_id=str(uuid.uuid4())[:8],
            source=Path(source),
            destination=Path(destination),
            is_folder=False,
            size_bytes=source.stat().st_size if source.exists() else 0,
        )

        try:
            # Validate source
            if not operation.source.exists():
                operation.error = "Source file does not exist"
                return operation

            if not operation.source.is_file():
                operation.error = "Source is not a file"
                return operation

            # Check if destination already exists
            if operation.destination.exists():
                self.logger.warning(f"Destination already exists: {operation.destination}")
                operation.error = "Destination already exists"
                return operation

            # Create backup if requested
            if backup and not self.dry_run:
                backup_path = self._create_file_backup(operation.source)
                operation.backed_up = True
                operation.backup_path = backup_path

            # Create destination directory
            operation.destination.parent.mkdir(parents=True, exist_ok=True)

            if self.dry_run:
                self.logger.info(
                    f"[DRY RUN] Would move: {operation.source} -> {operation.destination}"
                )
                operation.completed = True
            else:
                # Move file
                shutil.move(str(operation.source), str(operation.destination))

                # Verify if requested
                if self.verify_moves:
                    if self.verify_move(operation.source, operation.destination):
                        operation.completed = True
                        self.logger.info(f"✓ Moved: {operation.source.name}")
                    else:
                        operation.error = "Verification failed"
                        self.logger.error(f"✗ Move verification failed: {operation.source.name}")
                else:
                    operation.completed = True

        except PermissionError as e:
            operation.error = f"Permission denied: {e}"
            self.logger.error(f"Permission denied moving {operation.source}: {e}")
        except Exception as e:
            operation.error = str(e)
            self.logger.error(f"Failed to move {operation.source}: {e}")

        self.operations.append(operation)
        return operation

    def move_folder(self, source: Path, destination: Path, backup: bool = True) -> MoveOperation:
        """
        Move an entire folder with optional backup.

        Args:
            source: Source folder path
            destination: Destination folder path
            backup: Create backup before moving

        Returns:
            MoveOperation result
        """
        operation = MoveOperation(
            operation_id=str(uuid.uuid4())[:8],
            source=Path(source),
            destination=Path(destination),
            is_folder=True,
            size_bytes=self._get_folder_size(Path(source)),
        )

        try:
            # Validate source
            if not operation.source.exists():
                operation.error = "Source folder does not exist"
                return operation

            if not operation.source.is_dir():
                operation.error = "Source is not a folder"
                return operation

            # Check if destination already exists
            if operation.destination.exists():
                self.logger.warning(f"Destination already exists: {operation.destination}")
                operation.error = "Destination already exists"
                return operation

            # Create backup if requested
            if backup and not self.dry_run:
                backup_path = self._create_folder_backup(operation.source)
                operation.backed_up = True
                operation.backup_path = backup_path

            if self.dry_run:
                self.logger.info(
                    f"[DRY RUN] Would move folder: {operation.source} -> {operation.destination}"
                )
                operation.completed = True
            else:
                # Move folder
                shutil.move(str(operation.source), str(operation.destination))
                operation.completed = True
                self.logger.info(f"✓ Moved folder: {operation.source.name}")

        except PermissionError as e:
            operation.error = f"Permission denied: {e}"
            self.logger.error(f"Permission denied moving {operation.source}: {e}")
        except Exception as e:
            operation.error = str(e)
            self.logger.error(f"Failed to move {operation.source}: {e}")

        self.operations.append(operation)
        return operation

    def batch_move(self, operations: List[tuple]) -> BatchResult:
        """
        Perform batch move operations.

        Args:
            operations: List of (source, destination, is_folder) tuples

        Returns:
            BatchResult with statistics

        Example:
            >>> operations = [
            ...     (Path('file1.dll'), Path('dest/file1.dll'), False),
            ...     (Path('folder'), Path('dest/folder'), True),
            ... ]
            >>> result = mover.batch_move(operations)
        """
        start_time = time.time()
        results = []
        total_size = 0

        self.logger.info(f"Starting batch move of {len(operations)} items...")

        for source, destination, is_folder in operations:
            if is_folder:
                result = self.move_folder(source, destination)
            else:
                result = self.move_file(source, destination)

            results.append(result)
            total_size += result.size_bytes

        duration = time.time() - start_time
        successful = sum(1 for r in results if r.completed)
        failed = len(results) - successful

        batch_result = BatchResult(
            total_operations=len(operations),
            successful=successful,
            failed=failed,
            operations=results,
            total_size_bytes=total_size,
            duration_seconds=duration,
        )

        self.logger.info(
            f"Batch move complete: {successful} successful, {failed} failed, " f"{duration:.2f}s"
        )

        return batch_result

    def verify_move(self, source: Path, destination: Path) -> bool:
        """
        Verify file was moved successfully.

        Args:
            source: Original source path
            destination: Destination path

        Returns:
            True if move verified
        """
        # Source should no longer exist
        if source.exists():
            self.logger.warning(f"Source still exists after move: {source}")
            return False

        # Destination should exist
        if not destination.exists():
            self.logger.warning(f"Destination does not exist: {destination}")
            return False

        return True

    def rollback_move(self, operation_id: str) -> bool:
        """
        Rollback a move operation using backup.

        Args:
            operation_id: Operation ID to rollback

        Returns:
            True if rollback successful
        """
        # Find operation
        operation = None
        for op in self.operations:
            if op.operation_id == operation_id:
                operation = op
                break

        if not operation:
            self.logger.error(f"Operation not found: {operation_id}")
            return False

        if not operation.backed_up or not operation.backup_path:
            self.logger.error(f"No backup available for operation {operation_id}")
            return False

        try:
            self.logger.info(f"Rolling back operation {operation_id}")

            # Restore from backup
            if operation.backup_path.is_file():
                shutil.copy2(str(operation.backup_path), str(operation.source))
            elif operation.backup_path.is_dir():
                shutil.copytree(str(operation.backup_path), str(operation.source))

            # Remove destination if it exists
            if operation.destination.exists():
                if operation.destination.is_file():
                    operation.destination.unlink()
                else:
                    shutil.rmtree(str(operation.destination))

            self.logger.info(f"✓ Rollback successful for {operation_id}")
            return True

        except Exception as e:
            self.logger.error(f"Rollback failed for {operation_id}: {e}")
            return False

    def _create_file_backup(self, file_path: Path) -> Path:
        """Create backup of a file."""
        backup_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{file_path.stem}_{timestamp}_{backup_id}{file_path.suffix}"
        backup_path = self.backup_dir / backup_name

        shutil.copy2(str(file_path), str(backup_path))
        self.logger.debug(f"Created backup: {backup_path}")

        return backup_path

    def _create_folder_backup(self, folder_path: Path) -> Path:
        """Create backup of a folder."""
        backup_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{folder_path.name}_{timestamp}_{backup_id}"
        backup_path = self.backup_dir / backup_name

        shutil.copytree(str(folder_path), str(backup_path))
        self.logger.debug(f"Created folder backup: {backup_path}")

        return backup_path

    def _get_folder_size(self, folder_path: Path) -> int:
        """Calculate total size of folder."""
        total_size = 0

        try:
            for item in folder_path.rglob("*"):
                if item.is_file():
                    total_size += item.stat().st_size
        except Exception as e:
            self.logger.warning(f"Could not calculate folder size for {folder_path}: {e}")

        return total_size

    def estimate_move_time(self, size_bytes: int, sample_speed_mbps: float = 100.0) -> float:
        """
        Estimate time to move files.

        Args:
            size_bytes: Total size to move
            sample_speed_mbps: Estimated disk speed in MB/s

        Returns:
            Estimated time in seconds
        """
        size_mb = size_bytes / (1024 * 1024)
        estimated_seconds = size_mb / sample_speed_mbps
        return estimated_seconds

    def get_operation_stats(self) -> Dict[str, any]:
        """Get statistics for all operations."""
        total = len(self.operations)
        completed = sum(1 for op in self.operations if op.completed)
        failed = total - completed
        total_size = sum(op.size_bytes for op in self.operations)

        return {
            "total_operations": total,
            "completed": completed,
            "failed": failed,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "total_size_gb": round(total_size / (1024**3), 2),
        }
