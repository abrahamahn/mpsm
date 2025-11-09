"""Comprehensive Windows Registry scanner."""

import platform
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from ..core.logger import get_logger
from ..core.exceptions import RegistryException
from ..models.registry import RegistryEntry

# Platform-specific imports
IS_WINDOWS = platform.system() == 'Windows'

if IS_WINDOWS:
    try:
        import winreg
    except ImportError:
        winreg = None
else:
    winreg = None


class RegistryReader:
    """Comprehensive Windows Registry scanner."""

    # Registry hives mapping
    HIVES = {
        'HKLM': 'HKEY_LOCAL_MACHINE',
        'HKCU': 'HKEY_CURRENT_USER',
        'HKCR': 'HKEY_CLASSES_ROOT',
        'HKU': 'HKEY_USERS',
        'HKCC': 'HKEY_CURRENT_CONFIG',
    }

    # Windows registry constants (if winreg available)
    if IS_WINDOWS and winreg:
        HIVE_CONSTANTS = {
            'HKLM': winreg.HKEY_LOCAL_MACHINE,
            'HKCU': winreg.HKEY_CURRENT_USER,
            'HKCR': winreg.HKEY_CLASSES_ROOT,
            'HKU': winreg.HKEY_USERS,
            'HKCC': winreg.HKEY_CURRENT_CONFIG,
        }
    else:
        HIVE_CONSTANTS = {}

    # Known registry locations for music production software
    KNOWN_KEYS = [
        r"SOFTWARE\VST",
        r"SOFTWARE\VST3",
        r"SOFTWARE\Image-Line",
        r"SOFTWARE\Ableton",
        r"SOFTWARE\Waves",
        r"SOFTWARE\iZotope",
        r"SOFTWARE\Native Instruments",
        r"SOFTWARE\Arturia",
        r"SOFTWARE\FabFilter",
        r"SOFTWARE\Xfer Records",
        r"SOFTWARE\Spectrasonics",
        r"SOFTWARE\u-he",
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
    ]

    def __init__(self):
        """Initialize registry reader."""
        self.logger = get_logger()
        self.is_windows = IS_WINDOWS

        if not self.is_windows:
            self.logger.warning("Not running on Windows - registry operations will be mocked")

    def _parse_key_path(self, key_path: str) -> tuple[str, str]:
        """
        Parse registry key path into hive and subkey.

        Args:
            key_path: Full registry path (e.g., "HKLM\\SOFTWARE\\VST")

        Returns:
            Tuple of (hive, subkey)

        Example:
            >>> _parse_key_path("HKLM\\SOFTWARE\\VST")
            ('HKLM', 'SOFTWARE\\VST')
        """
        parts = key_path.split('\\', 1)
        if len(parts) != 2:
            raise RegistryException(f"Invalid registry path: {key_path}")

        hive = parts[0].upper()
        subkey = parts[1]

        # Handle full names
        for short, full in self.HIVES.items():
            if hive == full.upper() or hive == full:
                hive = short
                break

        if hive not in self.HIVES:
            raise RegistryException(f"Unknown registry hive: {hive}")

        return hive, subkey

    def key_exists(self, key_path: str) -> bool:
        """
        Check if registry key exists.

        Args:
            key_path: Full registry path

        Returns:
            True if key exists
        """
        if not self.is_windows:
            return False

        try:
            hive, subkey = self._parse_key_path(key_path)
            hive_const = self.HIVE_CONSTANTS[hive]

            with winreg.OpenKey(hive_const, subkey, 0, winreg.KEY_READ):
                return True

        except (OSError, FileNotFoundError, RegistryException):
            return False

    def read_key(self, key_path: str) -> List[RegistryEntry]:
        """
        Read all values from a registry key.

        Args:
            key_path: Full registry path

        Returns:
            List of RegistryEntry objects

        Raises:
            RegistryException: If key cannot be read
        """
        if not self.is_windows:
            self.logger.warning(f"Mock registry read for: {key_path}")
            return []

        try:
            hive, subkey = self._parse_key_path(key_path)
            hive_const = self.HIVE_CONSTANTS[hive]

            entries = []

            with winreg.OpenKey(hive_const, subkey, 0, winreg.KEY_READ) as key:
                # Get key info
                num_values = winreg.QueryInfoKey(key)[1]

                # Read all values
                for i in range(num_values):
                    try:
                        value_name, value_data, value_type = winreg.EnumValue(key, i)

                        # Convert value type to string
                        type_map = {
                            winreg.REG_SZ: "REG_SZ",
                            winreg.REG_EXPAND_SZ: "REG_EXPAND_SZ",
                            winreg.REG_BINARY: "REG_BINARY",
                            winreg.REG_DWORD: "REG_DWORD",
                            winreg.REG_MULTI_SZ: "REG_MULTI_SZ",
                        }
                        value_type_str = type_map.get(value_type, f"REG_UNKNOWN_{value_type}")

                        # Create entry
                        entry = RegistryEntry(
                            key_path=key_path,
                            value_name=value_name or "(Default)",
                            value_data=str(value_data),
                            value_type=value_type_str,
                            hive=hive,
                        )

                        entries.append(entry)

                    except Exception as e:
                        self.logger.warning(f"Error reading value {i} from {key_path}: {e}")

            self.logger.debug(f"Read {len(entries)} values from {key_path}")
            return entries

        except FileNotFoundError:
            self.logger.debug(f"Registry key not found: {key_path}")
            return []
        except PermissionError as e:
            raise RegistryException(f"Permission denied reading {key_path}", {'error': str(e)})
        except Exception as e:
            raise RegistryException(f"Failed to read registry key {key_path}", {'error': str(e)})

    def read_value(self, key_path: str, value_name: str) -> Optional[str]:
        """
        Read a specific value from registry.

        Args:
            key_path: Full registry path
            value_name: Value name to read

        Returns:
            Value data as string, or None if not found
        """
        if not self.is_windows:
            return None

        try:
            hive, subkey = self._parse_key_path(key_path)
            hive_const = self.HIVE_CONSTANTS[hive]

            with winreg.OpenKey(hive_const, subkey, 0, winreg.KEY_READ) as key:
                value_data, _ = winreg.QueryValueEx(key, value_name)
                return str(value_data)

        except (FileNotFoundError, OSError):
            return None

    def get_vst_paths(self) -> List[str]:
        """
        Get VST plugin paths from registry.

        Returns:
            List of VST paths
        """
        paths = []

        # Check common VST path locations
        vst_keys = [
            r"HKLM\SOFTWARE\VST",
            r"HKCU\Software\VST",
        ]

        for key_path in vst_keys:
            entries = self.read_key(key_path)
            for entry in entries:
                if entry.is_path_value():
                    paths.append(entry.value_data)

        return paths

    def get_vst3_paths(self) -> List[str]:
        """
        Get VST3 plugin paths from registry.

        Returns:
            List of VST3 paths
        """
        paths = []

        vst3_keys = [
            r"HKLM\SOFTWARE\VST3",
            r"HKCU\Software\VST3",
        ]

        for key_path in vst3_keys:
            entries = self.read_key(key_path)
            for entry in entries:
                if entry.is_path_value():
                    paths.append(entry.value_data)

        return paths

    def get_daw_paths(self) -> Dict[str, str]:
        """
        Get DAW installation paths.

        Returns:
            Dictionary mapping DAW name to path
        """
        daw_paths = {}

        # FL Studio
        fl_keys = [
            r"HKLM\SOFTWARE\Image-Line\FL Studio",
            r"HKCU\Software\Image-Line\FL Studio",
        ]
        for key_path in fl_keys:
            path = self.read_value(key_path, "InstallPath")
            if path:
                daw_paths['FL Studio'] = path
                break

        # Ableton Live
        ableton_keys = [
            r"HKLM\SOFTWARE\Ableton\Live",
            r"HKCU\Software\Ableton\Live",
        ]
        for key_path in ableton_keys:
            path = self.read_value(key_path, "InstallPath")
            if path:
                daw_paths['Ableton Live'] = path
                break

        return daw_paths

    def find_plugin_registry_keys(self, plugin_name: str) -> List[str]:
        """
        Find all registry keys related to a plugin.

        Args:
            plugin_name: Plugin name to search for

        Returns:
            List of registry key paths
        """
        found_keys = []
        plugin_name_lower = plugin_name.lower()

        # Search in known locations
        search_roots = [
            r"HKLM\SOFTWARE",
            r"HKCU\Software",
        ]

        for root in search_roots:
            try:
                keys = self._search_subkeys(root, plugin_name_lower, max_depth=3)
                found_keys.extend(keys)
            except Exception as e:
                self.logger.debug(f"Error searching {root}: {e}")

        return found_keys

    def _search_subkeys(self, key_path: str, search_term: str, max_depth: int = 2, current_depth: int = 0) -> List[str]:
        """
        Recursively search for subkeys containing search term.

        Args:
            key_path: Registry key to search
            search_term: Term to search for (case-insensitive)
            max_depth: Maximum recursion depth
            current_depth: Current recursion depth

        Returns:
            List of matching key paths
        """
        if not self.is_windows or current_depth >= max_depth:
            return []

        found = []

        try:
            hive, subkey = self._parse_key_path(key_path)
            hive_const = self.HIVE_CONSTANTS[hive]

            with winreg.OpenKey(hive_const, subkey, 0, winreg.KEY_READ) as key:
                num_subkeys = winreg.QueryInfoKey(key)[0]

                for i in range(num_subkeys):
                    try:
                        subkey_name = winreg.EnumKey(key, i)

                        # Check if subkey name matches
                        if search_term in subkey_name.lower():
                            full_path = f"{key_path}\\{subkey_name}"
                            found.append(full_path)

                        # Recurse into subkey
                        if current_depth < max_depth - 1:
                            subkey_path = f"{key_path}\\{subkey_name}"
                            found.extend(self._search_subkeys(subkey_path, search_term, max_depth, current_depth + 1))

                    except Exception:
                        # Skip keys we can't access
                        continue

        except Exception as e:
            self.logger.debug(f"Error searching {key_path}: {e}")

        return found

    def get_all_uninstaller_keys(self) -> List[Dict[str, Any]]:
        """
        Get all software uninstaller entries.

        Returns:
            List of uninstaller info dictionaries
        """
        uninstallers = []

        uninstall_keys = [
            r"HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
            r"HKLM\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall",
            r"HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall",
        ]

        for root_key in uninstall_keys:
            if not self.key_exists(root_key):
                continue

            try:
                hive, subkey = self._parse_key_path(root_key)
                hive_const = self.HIVE_CONSTANTS[hive]

                with winreg.OpenKey(hive_const, subkey, 0, winreg.KEY_READ) as key:
                    num_subkeys = winreg.QueryInfoKey(key)[0]

                    for i in range(num_subkeys):
                        try:
                            app_key_name = winreg.EnumKey(key, i)
                            app_key_path = f"{root_key}\\{app_key_name}"

                            # Read application info
                            app_info = {}
                            entries = self.read_key(app_key_path)

                            for entry in entries:
                                app_info[entry.value_name] = entry.value_data

                            if 'DisplayName' in app_info:
                                uninstallers.append({
                                    'name': app_info.get('DisplayName', ''),
                                    'publisher': app_info.get('Publisher', ''),
                                    'version': app_info.get('DisplayVersion', ''),
                                    'install_location': app_info.get('InstallLocation', ''),
                                    'uninstall_string': app_info.get('UninstallString', ''),
                                    'registry_key': app_key_path,
                                })

                        except Exception:
                            continue

            except Exception as e:
                self.logger.debug(f"Error reading uninstaller keys from {root_key}: {e}")

        return uninstallers

    def scan_all_music_production_keys(self) -> Dict[str, List[RegistryEntry]]:
        """
        Scan all known music production registry keys.

        Returns:
            Dictionary mapping key path to list of entries
        """
        all_entries = {}

        for base_key in self.KNOWN_KEYS:
            for hive in ['HKLM', 'HKCU']:
                key_path = f"{hive}\\{base_key}"

                if self.key_exists(key_path):
                    try:
                        entries = self.read_key(key_path)
                        if entries:
                            all_entries[key_path] = entries
                            self.logger.info(f"Found {len(entries)} entries in {key_path}")
                    except RegistryException as e:
                        self.logger.warning(f"Could not read {key_path}: {e}")

        return all_entries

    def map_registry_to_files(self, file_paths: List[Path]) -> Dict[Path, List[str]]:
        """
        Map file paths to registry keys that reference them.

        Args:
            file_paths: List of file paths to check

        Returns:
            Dictionary mapping file path to list of registry keys
        """
        mapping = {}

        # Get all registry entries
        all_entries = self.scan_all_music_production_keys()

        # Check each file
        for file_path in file_paths:
            file_str = str(file_path)
            related_keys = []

            # Search for this path in registry entries
            for key_path, entries in all_entries.items():
                for entry in entries:
                    if entry.is_path_value() and file_str.lower() in entry.value_data.lower():
                        related_keys.append(key_path)

            if related_keys:
                mapping[file_path] = related_keys

        return mapping

    def export_registry_snapshot(self, output_path: Path) -> None:
        """
        Export registry snapshot to file.

        Args:
            output_path: Where to save snapshot
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        all_entries = self.scan_all_music_production_keys()

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"# MPSM Registry Snapshot\n")
            f.write(f"# Date: {datetime.now().isoformat()}\n")
            f.write(f"# Total keys: {len(all_entries)}\n\n")

            for key_path, entries in all_entries.items():
                f.write(f"\n[{key_path}]\n")
                for entry in entries:
                    f.write(f'"{entry.value_name}" = "{entry.value_data}" ({entry.value_type})\n')

        self.logger.info(f"Exported registry snapshot to {output_path}")
