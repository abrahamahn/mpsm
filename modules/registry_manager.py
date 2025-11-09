"""
MPSM Registry Manager Module
Handles Windows registry operations for plugin path management
"""

import os
import logging
import subprocess
from typing import Dict, List, Any
from datetime import datetime


class RegistryManager:
    """Manages Windows registry operations for plugin paths"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.backup_dir = config.get('registry_backup_path', 'backups/registry')

    def backup_registry(self, key_path: str) -> str:
        """
        Backup a registry key to .reg file

        Args:
            key_path: Registry key path (e.g., HKCU\\Software\\VST)

        Returns:
            Path to backup file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(self.backup_dir, f"registry_backup_{timestamp}.reg")

        # TODO: Implement registry backup
        # - Use reg export command
        # - Save to backup directory

        self.logger.info(f"Registry backed up to: {backup_file}")
        return backup_file

    def update_paths(self, old_path: str, new_path: str) -> bool:
        """
        Update plugin paths in registry

        Args:
            old_path: Old plugin path
            new_path: New plugin path

        Returns:
            True if successful
        """
        # TODO: Implement path updating
        # - Find all registry entries with old_path
        # - Replace with new_path
        # - Verify changes

        self.logger.info(f"Updated registry path: {old_path} -> {new_path}")
        return True

    def restore_backup(self, backup_file: str) -> bool:
        """
        Restore registry from backup file

        Args:
            backup_file: Path to .reg backup file

        Returns:
            True if successful
        """
        # TODO: Implement registry restore
        # - Use reg import command
        # - Verify restoration

        self.logger.info(f"Registry restored from: {backup_file}")
        return True

    def get_plugin_registry_keys(self) -> List[str]:
        """
        Get common plugin registry keys

        Returns:
            List of registry key paths
        """
        return [
            r"HKEY_LOCAL_MACHINE\SOFTWARE\VST",
            r"HKEY_CURRENT_USER\Software\VST",
            r"HKEY_CURRENT_USER\Software\Image-Line\FL Studio\Locations",
            r"HKEY_CURRENT_USER\Software\Ableton",
            # Add more common keys
        ]


def backup_and_update(config: Dict[str, Any], old_path: str, new_path: str) -> bool:
    """
    Main entry point for registry backup and update

    Args:
        config: Configuration dictionary
        old_path: Old plugin path
        new_path: New plugin path

    Returns:
        True if successful
    """
    manager = RegistryManager(config)
    manager.backup_registry("HKCU\\Software\\VST")
    return manager.update_paths(old_path, new_path)
