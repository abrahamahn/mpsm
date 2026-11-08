"""Registry backup system."""

import json
import platform
import subprocess
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..core.exceptions import RegistryException
from ..core.logger import get_logger
from ..models.registry import RegistryBackup

IS_WINDOWS = platform.system() == "Windows"


class RegistryBackupManager:
    """Handles registry backup operations."""

    def __init__(self, backup_dir: Optional[Path] = None):
        """
        Initialize registry backup manager.

        Args:
            backup_dir: Directory for backups. If None, uses backups/registry in project root
        """
        if backup_dir is None:
            project_root = Path(__file__).parent.parent.parent
            backup_dir = project_root / "backups" / "registry"

        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        self.logger = get_logger()
        self.is_windows = IS_WINDOWS

        # Metadata file
        self.metadata_file = self.backup_dir / "backups.json"
        self.metadata: dict = self._load_metadata()

    def _load_metadata(self) -> Dict[str, Any]:
        """Load backup metadata from file."""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, "r") as f:
                    data: Dict[str, Any] = json.load(f)
                    return data
            except Exception as e:
                self.logger.warning(f"Could not load backup metadata: {e}")

        return {"backups": []}

    def _save_metadata(self) -> None:
        """Save backup metadata to file."""
        try:
            with open(self.metadata_file, "w") as f:
                json.dump(self.metadata, f, indent=2, default=str)
        except Exception as e:
            self.logger.error(f"Could not save backup metadata: {e}")

    def create_backup(self, keys: List[str], description: str = "") -> RegistryBackup:
        """
        Create backup of registry keys.

        Args:
            keys: List of registry key paths to backup
            description: Optional description of backup

        Returns:
            RegistryBackup object

        Raises:
            RegistryException: If backup fails
        """
        if not self.is_windows:
            self.logger.warning("Not on Windows - creating mock backup")
            return self._create_mock_backup(keys, description)

        backup_id = str(uuid.uuid4())[:8]
        backup_date = datetime.now()
        backup_filename = f"backup_{backup_date.strftime('%Y%m%d_%H%M%S')}_{backup_id}.reg"
        backup_path = self.backup_dir / backup_filename

        self.logger.info(f"Creating registry backup: {backup_id}")

        try:
            # Export each key to .reg file
            with open(backup_path, "w", encoding="utf-16le") as f:
                # Write .reg file header
                f.write("\ufeff")  # BOM for UTF-16LE
                f.write("Windows Registry Editor Version 5.00\n\n")

                for key in keys:
                    try:
                        # Use reg.exe to export key
                        temp_file = self.backup_dir / f"temp_{backup_id}.reg"

                        result = subprocess.run(
                            ["reg", "export", key, str(temp_file), "/y"],
                            capture_output=True,
                            text=True,
                            check=False,
                        )

                        if result.returncode == 0 and temp_file.exists():
                            # Read exported content (skip header)
                            with open(temp_file, "r", encoding="utf-16le") as temp_f:
                                lines = temp_f.readlines()
                                # Skip first 2 lines (header)
                                content = "".join(lines[2:])
                                f.write(content)
                                f.write("\n")

                            temp_file.unlink()
                            self.logger.debug(f"Backed up key: {key}")
                        else:
                            self.logger.warning(f"Could not backup key {key}: {result.stderr}")

                    except Exception as e:
                        self.logger.warning(f"Error backing up key {key}: {e}")

            # Create backup metadata
            backup = RegistryBackup(
                backup_id=backup_id,
                backup_date=backup_date,
                backup_path=self.backup_dir,
                keys_backed_up=keys,
                registry_file=backup_path,
            )

            # Save metadata
            self.metadata["backups"].append(
                {
                    "backup_id": backup_id,
                    "backup_date": backup_date.isoformat(),
                    "description": description,
                    "keys_count": len(keys),
                    "keys": keys,
                    "file": str(backup_path),
                }
            )
            self._save_metadata()

            self.logger.info(f"✓ Created backup {backup_id} with {len(keys)} keys")
            return backup

        except Exception as e:
            self.logger.error(f"Failed to create backup: {e}")
            raise RegistryException("Backup failed", {"error": str(e)})

    def _create_mock_backup(self, keys: List[str], description: str = "") -> RegistryBackup:
        """Create a mock backup for testing on non-Windows systems."""
        backup_id = str(uuid.uuid4())[:8]
        backup_date = datetime.now()
        backup_filename = f"mock_backup_{backup_date.strftime('%Y%m%d_%H%M%S')}_{backup_id}.json"
        backup_path = self.backup_dir / backup_filename

        # Save mock backup
        mock_data = {
            "backup_id": backup_id,
            "backup_date": backup_date.isoformat(),
            "description": description,
            "keys": keys,
            "mock": True,
        }

        with open(backup_path, "w") as f:
            json.dump(mock_data, f, indent=2)

        backup = RegistryBackup(
            backup_id=backup_id,
            backup_date=backup_date,
            backup_path=self.backup_dir,
            keys_backed_up=keys,
            registry_file=backup_path,
        )

        # Save metadata
        self.metadata["backups"].append(
            {
                "backup_id": backup_id,
                "backup_date": backup_date.isoformat(),
                "description": description,
                "keys_count": len(keys),
                "keys": keys,
                "file": str(backup_path),
                "mock": True,
            }
        )
        self._save_metadata()

        return backup

    def restore_backup(self, backup_id: str) -> bool:
        """
        Restore registry from backup.

        Args:
            backup_id: Backup ID to restore

        Returns:
            True if restore successful

        Raises:
            RegistryException: If restore fails
        """
        # Find backup
        backup_info = None
        for backup in self.metadata["backups"]:
            if backup["backup_id"] == backup_id:
                backup_info = backup
                break

        if not backup_info:
            raise RegistryException(f"Backup not found: {backup_id}")

        if not self.is_windows:
            self.logger.warning("Not on Windows - mock restore")
            return True

        backup_file = Path(backup_info["file"])
        if not backup_file.exists():
            raise RegistryException(f"Backup file not found: {backup_file}")

        self.logger.info(f"Restoring backup: {backup_id}")

        try:
            # Use reg.exe to import .reg file
            result = subprocess.run(
                ["reg", "import", str(backup_file)], capture_output=True, text=True, check=False
            )

            if result.returncode == 0:
                self.logger.info(f"✓ Restored backup {backup_id}")
                return True
            else:
                error_msg = result.stderr or "Unknown error"
                raise RegistryException(f"Restore failed: {error_msg}")

        except Exception as e:
            self.logger.error(f"Failed to restore backup: {e}")
            raise RegistryException("Restore failed", {"error": str(e)})

    def list_backups(self) -> List[Dict[str, Any]]:
        """
        List all backups.

        Returns:
            List of backup information dictionaries
        """
        backups: List[Dict[str, Any]] = self.metadata.get("backups", [])
        return backups

    def get_backup_info(self, backup_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific backup.

        Args:
            backup_id: Backup ID

        Returns:
            Backup info dictionary or None if not found
        """
        for backup in self.metadata["backups"]:
            if backup["backup_id"] == backup_id:
                result: Dict[str, Any] = backup
                return result
        return None

    def delete_backup(self, backup_id: str) -> bool:
        """
        Delete a backup.

        Args:
            backup_id: Backup ID to delete

        Returns:
            True if deleted successfully
        """
        backup_info = self.get_backup_info(backup_id)
        if not backup_info:
            self.logger.warning(f"Backup not found: {backup_id}")
            return False

        try:
            # Delete backup file
            backup_file = Path(backup_info["file"])
            if backup_file.exists():
                backup_file.unlink()

            # Remove from metadata
            self.metadata["backups"] = [
                b for b in self.metadata["backups"] if b["backup_id"] != backup_id
            ]
            self._save_metadata()

            self.logger.info(f"Deleted backup: {backup_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to delete backup {backup_id}: {e}")
            return False

    def cleanup_old_backups(self, retention_days: int = 30) -> int:
        """
        Remove backups older than retention period.

        Args:
            retention_days: Number of days to keep backups

        Returns:
            Number of backups deleted
        """
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        deleted_count = 0

        backups_to_delete = []

        for backup in self.metadata["backups"]:
            backup_date = datetime.fromisoformat(backup["backup_date"])

            if backup_date < cutoff_date:
                backups_to_delete.append(backup["backup_id"])

        for backup_id in backups_to_delete:
            if self.delete_backup(backup_id):
                deleted_count += 1

        if deleted_count > 0:
            self.logger.info(f"Cleaned up {deleted_count} old backups")

        return deleted_count

    def verify_backup(self, backup_id: str) -> bool:
        """
        Verify backup file integrity.

        Args:
            backup_id: Backup ID to verify

        Returns:
            True if backup is valid
        """
        backup_info = self.get_backup_info(backup_id)
        if not backup_info:
            return False

        backup_file = Path(backup_info["file"])
        if not backup_file.exists():
            self.logger.error(f"Backup file missing: {backup_file}")
            return False

        # Check file is not empty
        if backup_file.stat().st_size == 0:
            self.logger.error(f"Backup file is empty: {backup_file}")
            return False

        return True
