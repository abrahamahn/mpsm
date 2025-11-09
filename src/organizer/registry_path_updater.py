"""Registry path updater for file moves."""

from pathlib import Path
from typing import List, Dict, Optional

from ..core.logger import get_logger
from ..registry.manager import RegistryManager
from ..registry.registry_reader import RegistryReader
from ..models.registry import PathUpdate


class RegistryPathUpdater:
    """Updates registry paths after file moves."""

    def __init__(self, auto_backup: bool = True):
        """
        Initialize registry path updater.

        Args:
            auto_backup: Automatically backup before updates
        """
        self.logger = get_logger()
        self.registry_manager = RegistryManager(auto_backup=auto_backup)
        self.registry_reader = RegistryReader()

    def create_update_plan_for_move(
        self,
        old_path: Path,
        new_path: Path,
        plugin_name: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """
        Create registry update plan for a file move.

        Args:
            old_path: Original file path
            new_path: New file path
            plugin_name: Optional plugin name to narrow search

        Returns:
            List of update dictionaries

        Example:
            >>> updates = updater.create_update_plan_for_move(
            ...     Path('C:\\Old\\plugin.dll'),
            ...     Path('C:\\New\\plugin.dll'),
            ...     'MyPlugin'
            ... )
        """
        updates = []

        self.logger.info(f"Creating registry update plan for: {old_path} -> {new_path}")

        # Search for registry entries containing the old path
        all_entries = self.registry_reader.scan_all_music_production_keys()

        old_path_str = str(old_path).lower()
        new_path_str = str(new_path)

        for key_path, entries in all_entries.items():
            for entry in entries:
                # Check if this entry contains the old path
                if entry.is_path_value() and old_path_str in entry.value_data.lower():
                    updates.append({
                        'key_path': key_path,
                        'value_name': entry.value_name,
                        'old_path': entry.value_data,
                        'new_path': entry.value_data.replace(str(old_path), new_path_str),
                    })

        self.logger.info(f"Found {len(updates)} registry entries to update")
        return updates

    def create_batch_update_plan(
        self,
        move_operations: List[tuple]
    ) -> List[Dict[str, str]]:
        """
        Create registry update plan for batch moves.

        Args:
            move_operations: List of (old_path, new_path, is_folder) tuples

        Returns:
            List of update dictionaries
        """
        all_updates = []

        for old_path, new_path, is_folder in move_operations:
            updates = self.create_update_plan_for_move(
                Path(old_path),
                Path(new_path)
            )
            all_updates.extend(updates)

        # Remove duplicates (same key and value name)
        unique_updates = []
        seen = set()

        for update in all_updates:
            key = (update['key_path'], update['value_name'])
            if key not in seen:
                seen.add(key)
                unique_updates.append(update)

        self.logger.info(f"Created batch update plan with {len(unique_updates)} unique updates")
        return unique_updates

    def execute_updates(
        self,
        updates: List[Dict[str, str]],
        dry_run: bool = False
    ) -> Dict[str, PathUpdate]:
        """
        Execute registry updates.

        Args:
            updates: List of update dictionaries
            dry_run: Don't actually update, just simulate

        Returns:
            Dictionary mapping key path to PathUpdate result
        """
        if dry_run:
            self.logger.info(f"[DRY RUN] Would update {len(updates)} registry entries")
            return {}

        return self.registry_manager.batch_update(
            updates,
            description="File consolidation registry updates"
        )

    def verify_updates(
        self,
        updates: List[Dict[str, str]]
    ) -> List[Dict[str, any]]:
        """
        Verify that registry updates were successful.

        Args:
            updates: List of update dictionaries that were applied

        Returns:
            List of verification results
        """
        results = []

        for update in updates:
            current_value = self.registry_reader.read_value(
                update['key_path'],
                update['value_name']
            )

            verified = current_value == update['new_path']

            results.append({
                'key_path': update['key_path'],
                'value_name': update['value_name'],
                'expected': update['new_path'],
                'actual': current_value,
                'verified': verified,
            })

        verified_count = sum(1 for r in results if r['verified'])
        self.logger.info(f"Verified {verified_count}/{len(results)} registry updates")

        return results

    def find_affected_registry_entries(
        self,
        file_path: Path
    ) -> List[Dict[str, str]]:
        """
        Find all registry entries that reference a file.

        Args:
            file_path: File path to search for

        Returns:
            List of registry entry info dictionaries
        """
        affected = []
        file_path_str = str(file_path).lower()

        all_entries = self.registry_reader.scan_all_music_production_keys()

        for key_path, entries in all_entries.items():
            for entry in entries:
                if entry.is_path_value() and file_path_str in entry.value_data.lower():
                    affected.append({
                        'key_path': key_path,
                        'value_name': entry.value_name,
                        'value_data': entry.value_data,
                    })

        return affected

    def update_plugin_paths(
        self,
        plugin_name: str,
        old_install_path: Path,
        new_install_path: Path
    ) -> int:
        """
        Update all registry paths for a plugin installation.

        Args:
            plugin_name: Plugin name
            old_install_path: Old installation root
            new_install_path: New installation root

        Returns:
            Number of entries updated

        Example:
            >>> count = updater.update_plugin_paths(
            ...     'Serum',
            ...     Path('C:\\Program Files\\Xfer\\Serum'),
            ...     Path('C:\\MusicProduction\\Plugins\\Xfer\\Serum')
            ... )
        """
        self.logger.info(f"Updating paths for {plugin_name}")

        # Find plugin-specific registry keys
        plugin_keys = self.registry_reader.find_plugin_registry_keys(plugin_name)

        if not plugin_keys:
            self.logger.warning(f"No registry keys found for {plugin_name}")
            return 0

        updates = []
        old_path_str = str(old_install_path)
        new_path_str = str(new_install_path)

        # Read all entries from plugin keys
        for key_path in plugin_keys:
            entries = self.registry_reader.read_key(key_path)

            for entry in entries:
                if entry.is_path_value() and old_path_str in entry.value_data:
                    new_value = entry.value_data.replace(old_path_str, new_path_str)

                    updates.append({
                        'key_path': key_path,
                        'value_name': entry.value_name,
                        'old_path': entry.value_data,
                        'new_path': new_value,
                    })

        if updates:
            results = self.registry_manager.batch_update(updates)
            successful = sum(1 for r in results.values() if r.updated)
            self.logger.info(f"Updated {successful} registry entries for {plugin_name}")
            return successful

        return 0

    def rollback_updates(self, backup_id: str) -> bool:
        """
        Rollback registry updates using backup.

        Args:
            backup_id: Backup ID to restore

        Returns:
            True if rollback successful
        """
        return self.registry_manager.rollback(backup_id)

    def get_last_backup_id(self) -> Optional[str]:
        """
        Get ID of last backup created.

        Returns:
            Backup ID or None
        """
        return self.registry_manager.last_backup_id
