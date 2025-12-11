"""Registry manager with backup and update capabilities."""

import platform
from pathlib import Path
from typing import Dict, List, Optional

from ..core.exceptions import RegistryException
from ..core.logger import get_logger
from ..models.registry import PathUpdate
from .backup import RegistryBackupManager
from .registry_reader import RegistryReader

IS_WINDOWS = platform.system() == "Windows"

if IS_WINDOWS:
    try:
        import winreg
    except ImportError:
        winreg = None
else:
    winreg = None


class RegistryManager:
    """Manages registry operations with backup and rollback."""

    def __init__(self, backup_dir: Optional[Path] = None, auto_backup: bool = True):
        """
        Initialize registry manager.

        Args:
            backup_dir: Directory for backups
            auto_backup: Automatically backup before modifications
        """
        self.logger = get_logger()
        self.reader = RegistryReader()
        self.backup_manager = RegistryBackupManager(backup_dir)
        self.auto_backup = auto_backup
        self.is_windows = IS_WINDOWS

        self.last_backup_id: Optional[str] = None

    def backup_key(self, key_path: str, description: str = "") -> str:
        """
        Backup a single registry key.

        Args:
            key_path: Registry key path
            description: Optional backup description

        Returns:
            Backup ID

        Raises:
            RegistryException: If backup fails
        """
        backup = self.backup_manager.create_backup([key_path], description)
        self.last_backup_id = backup.backup_id
        return backup.backup_id

    def backup_keys(self, key_paths: List[str], description: str = "") -> str:
        """
        Backup multiple registry keys.

        Args:
            key_paths: List of registry key paths
            description: Optional backup description

        Returns:
            Backup ID
        """
        backup = self.backup_manager.create_backup(key_paths, description)
        self.last_backup_id = backup.backup_id
        return backup.backup_id

    def update_path(
        self, key_path: str, value_name: str, old_path: str, new_path: str
    ) -> PathUpdate:
        """
        Update a registry path value.

        Args:
            key_path: Registry key path
            value_name: Value name to update
            old_path: Old path (for verification)
            new_path: New path

        Returns:
            PathUpdate object with result

        Raises:
            RegistryException: If update fails
        """
        self.logger.info(f"Updating registry path: {key_path}\\{value_name}")

        # Create backup if auto_backup is enabled
        if self.auto_backup:
            try:
                self.backup_key(key_path, f"Before updating {value_name}")
            except Exception as e:
                self.logger.warning(f"Backup failed: {e}")

        update = PathUpdate(
            key_path=key_path, value_name=value_name, old_path=old_path, new_path=new_path
        )

        if not self.is_windows:
            self.logger.warning("Not on Windows - mock path update")
            update.updated = True
            return update

        try:
            # Parse key path
            hive, subkey = self.reader._parse_key_path(key_path)
            hive_const = self.reader.HIVE_CONSTANTS[hive]

            # Open key with write access
            with winreg.OpenKey(
                hive_const, subkey, 0, winreg.KEY_SET_VALUE | winreg.KEY_READ
            ) as key:
                # Read current value to verify
                try:
                    current_value, value_type = winreg.QueryValueEx(key, value_name)
                except FileNotFoundError:
                    update.error = f"Value not found: {value_name}"
                    return update

                # Verify old path matches (optional but recommended)
                if str(current_value) != old_path:
                    self.logger.warning(
                        f"Current value doesn't match old_path. "
                        f"Current: {current_value}, Expected: {old_path}"
                    )

                # Write new value
                winreg.SetValueEx(key, value_name, 0, value_type, new_path)

                # Verify update
                new_value, _ = winreg.QueryValueEx(key, value_name)
                if str(new_value) == new_path:
                    update.updated = True
                    self.logger.info(f"✓ Updated {key_path}\\{value_name}")
                else:
                    update.error = "Verification failed after update"

        except PermissionError as e:
            update.error = f"Permission denied: {e}"
            self.logger.error(f"Permission denied updating {key_path}: {e}")
        except Exception as e:
            update.error = str(e)
            self.logger.error(f"Failed to update {key_path}: {e}")

        return update

    def batch_update(
        self, updates: List[Dict[str, str]], description: str = ""
    ) -> Dict[str, PathUpdate]:
        """
        Perform batch registry updates with transaction-like behavior.

        Args:
            updates: List of update dictionaries with keys: key_path, value_name, old_path, new_path
            description: Backup description

        Returns:
            Dictionary mapping key path to PathUpdate result

        Example:
            >>> updates = [
            ...     {'key_path': 'HKLM\\SOFTWARE\\Plugin', 'value_name': 'Path',
            ...      'old_path': 'C:\\Old', 'new_path': 'C:\\New'},
            ... ]
            >>> results = manager.batch_update(updates)
        """
        results = {}

        # Collect all keys that will be modified
        keys_to_backup = list(set(u["key_path"] for u in updates))

        # Create backup
        if self.auto_backup:
            try:
                backup_id = self.backup_keys(keys_to_backup, description or "Batch update")
                self.logger.info(f"Created backup {backup_id} before batch update")
            except Exception as e:
                self.logger.warning(f"Backup failed: {e}")

        # Perform updates
        successful = 0
        failed = 0

        for update_dict in updates:
            try:
                result = self.update_path(
                    key_path=update_dict["key_path"],
                    value_name=update_dict["value_name"],
                    old_path=update_dict["old_path"],
                    new_path=update_dict["new_path"],
                )

                key = f"{update_dict['key_path']}\\{update_dict['value_name']}"
                results[key] = result

                if result.updated:
                    successful += 1
                else:
                    failed += 1

            except Exception as e:
                self.logger.error(f"Error in batch update: {e}")
                failed += 1

        self.logger.info(f"Batch update complete: {successful} successful, {failed} failed")

        # If any failed and we have a backup, offer to rollback
        if failed > 0 and self.last_backup_id:
            self.logger.warning(
                f"Some updates failed. You can rollback using backup {self.last_backup_id}"
            )

        return results

    def rollback(self, backup_id: Optional[str] = None) -> bool:
        """
        Rollback registry to previous backup.

        Args:
            backup_id: Backup ID to restore. If None, uses last backup.

        Returns:
            True if rollback successful

        Raises:
            RegistryException: If rollback fails
        """
        if backup_id is None:
            backup_id = self.last_backup_id

        if not backup_id:
            raise RegistryException("No backup ID specified and no recent backup found")

        self.logger.info(f"Rolling back to backup: {backup_id}")

        return self.backup_manager.restore_backup(backup_id)

    def verify_update(self, key_path: str, value_name: str, expected_path: str) -> bool:
        """
        Verify a registry value matches expected value.

        Args:
            key_path: Registry key path
            value_name: Value name
            expected_path: Expected value

        Returns:
            True if value matches expected
        """
        current_value = self.reader.read_value(key_path, value_name)

        if current_value == expected_path:
            self.logger.debug(f"✓ Verified {key_path}\\{value_name}")
            return True
        else:
            self.logger.warning(
                f"Verification failed for {key_path}\\{value_name}. "
                f"Expected: {expected_path}, Got: {current_value}"
            )
            return False

    def list_backups(self) -> List[dict]:
        """Get list of all backups."""
        return self.backup_manager.list_backups()

    def cleanup_old_backups(self, retention_days: int = 30) -> int:
        """
        Clean up old backups.

        Args:
            retention_days: Days to retain backups

        Returns:
            Number of backups deleted
        """
        return self.backup_manager.cleanup_old_backups(retention_days)
