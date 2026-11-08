"""Registry-based metadata extraction for plugins.

Extracts plugin information stored in Windows registry by DAWs
and plugin managers.
"""

import platform
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..core.logger import get_logger

IS_WINDOWS = platform.system() == "Windows"
winreg: Any = None
if IS_WINDOWS:
    try:
        import winreg as _winreg

        winreg = _winreg
    except ImportError:
        pass

HKEY_CLASSES_ROOT = winreg.HKEY_CLASSES_ROOT if winreg is not None else 0x80000000
HKEY_CURRENT_USER = winreg.HKEY_CURRENT_USER if winreg is not None else 0x80000001
HKEY_LOCAL_MACHINE = winreg.HKEY_LOCAL_MACHINE if winreg is not None else 0x80000002


def _query_optional_str(key: Any, value_name: str) -> Optional[str]:
    """Read an optional string value from an open registry key."""
    try:
        val, _ = winreg.QueryValueEx(key, value_name)
        return str(val) if val else None
    except OSError:
        return None


class RegistryMetadataScanner:
    """Extract plugin metadata from Windows registry."""

    # Common registry locations for plugin information
    VST_REGISTRY_PATHS = [
        (HKEY_LOCAL_MACHINE, r"SOFTWARE\VST"),
        (HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\VST"),
        (HKEY_CURRENT_USER, r"Software\VST"),
        (HKEY_LOCAL_MACHINE, r"SOFTWARE\VST3"),
        (HKEY_CURRENT_USER, r"Software\VST3"),
    ]

    DAW_PLUGIN_PATHS = [
        # Steinberg/Cubase
        (HKEY_CURRENT_USER, r"Software\Steinberg\Vst2x"),
        (HKEY_CURRENT_USER, r"Software\Steinberg\VST3Preferences"),
        # Image-Line/FL Studio
        (HKEY_CURRENT_USER, r"Software\Image-Line\FL Studio\Locations"),
        (HKEY_CURRENT_USER, r"Software\Image-Line\Shared\Paths"),
        # Ableton Live
        (HKEY_CURRENT_USER, r"Software\Ableton\Live"),
        # Reaper
        (HKEY_CURRENT_USER, r"Software\REAPER"),
    ]

    UNINSTALL_PATHS = [
        (HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        (
            HKEY_LOCAL_MACHINE,
            r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall",
        ),
        (HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Uninstall"),
    ]

    LICENSE_PATHS = [
        # iLok/PACE
        (HKEY_LOCAL_MACHINE, r"SOFTWARE\PACE Anti-Piracy"),
        (HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\PACE Anti-Piracy"),
        # Waves
        (HKEY_LOCAL_MACHINE, r"SOFTWARE\Waves"),
        (HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Waves"),
        # Native Instruments
        (HKEY_LOCAL_MACHINE, r"SOFTWARE\Native Instruments"),
    ]

    def __init__(self) -> None:
        """Initialize registry scanner."""
        self.logger = get_logger()
        self.is_windows = IS_WINDOWS and winreg is not None

    def find_plugin_metadata(
        self, plugin_path: Path, plugin_name: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Find plugin metadata in registry by file path."""
        return self.find_plugin_in_registry(plugin_path, plugin_name or plugin_path.stem)

    def find_plugin_in_registry(
        self, plugin_path: Path, plugin_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Find plugin information in registry.

        Args:
            plugin_path: Path to plugin file
            plugin_name: Plugin name

        Returns:
            Dictionary with registry metadata or None
        """
        if not self.is_windows:
            return None

        metadata: Dict[str, Any] = {
            "registry_key": None,
            "install_date": None,
            "description": None,
            "website": None,
            "license_status": "unknown",
        }

        # Search in DAW plugin databases
        daw_info = self._search_daw_databases(plugin_path, plugin_name)
        if daw_info:
            metadata.update(daw_info)

        # Search in uninstall registry
        uninstall_info = self._search_uninstall_registry(plugin_name)
        if uninstall_info:
            metadata.update(uninstall_info)

        # Search for license information
        license_info = self._search_license_registry(plugin_name)
        if license_info:
            metadata["license_status"] = license_info.get("status", "unknown")

        return metadata

    def _search_daw_databases(
        self, plugin_path: Path, plugin_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Search DAW plugin databases for information.

        Args:
            plugin_path: Path to plugin
            plugin_name: Plugin name

        Returns:
            Metadata dict or None
        """
        name_lower = plugin_name.lower()

        for hkey, subkey_path in self.DAW_PLUGIN_PATHS:
            try:
                key = winreg.OpenKey(hkey, subkey_path, 0, winreg.KEY_READ)

                i = 0
                while True:
                    try:
                        subkey_name = winreg.EnumKey(key, i)

                        if name_lower in subkey_name.lower():
                            full_path = (
                                f"{self._hkey_to_string(hkey)}\\{subkey_path}\\{subkey_name}"
                            )

                            plugin_key = winreg.OpenKey(key, subkey_name, 0, winreg.KEY_READ)
                            info = self._extract_key_values(plugin_key)
                            winreg.CloseKey(plugin_key)

                            if info:
                                info["registry_key"] = full_path
                                winreg.CloseKey(key)
                                return info

                        i += 1
                    except OSError:
                        break

                winreg.CloseKey(key)

            except (FileNotFoundError, PermissionError):
                continue
            except Exception as e:
                self.logger.debug(f"Error searching DAW registry: {e}")
                continue

        return None

    def _search_uninstall_registry(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """
        Search Windows uninstall registry for plugin info.

        Args:
            plugin_name: Plugin name

        Returns:
            Metadata dict or None
        """
        name_lower = plugin_name.lower()

        for hkey, subkey_path in self.UNINSTALL_PATHS:
            try:
                key = winreg.OpenKey(hkey, subkey_path, 0, winreg.KEY_READ)

                i = 0
                while True:
                    try:
                        subkey_name = winreg.EnumKey(key, i)
                        entry_key = winreg.OpenKey(key, subkey_name, 0, winreg.KEY_READ)

                        display_name = _query_optional_str(entry_key, "DisplayName")
                        if display_name and name_lower in display_name.lower():
                            metadata: Dict[str, Any] = {}

                            publisher = _query_optional_str(entry_key, "Publisher")
                            if publisher:
                                metadata["publisher"] = publisher

                            install_date = _query_optional_str(entry_key, "InstallDate")
                            if install_date:
                                try:
                                    metadata["install_date"] = datetime.strptime(
                                        install_date, "%Y%m%d"
                                    ).isoformat()
                                except ValueError:
                                    pass

                            website = _query_optional_str(
                                entry_key, "URLInfoAbout"
                            ) or _query_optional_str(entry_key, "HelpLink")
                            if website:
                                metadata["website"] = website

                            version = _query_optional_str(entry_key, "DisplayVersion")
                            if version:
                                metadata["version_string"] = version

                            comments = _query_optional_str(entry_key, "Comments")
                            if comments:
                                metadata["description"] = comments

                            winreg.CloseKey(entry_key)
                            winreg.CloseKey(key)
                            return metadata

                        winreg.CloseKey(entry_key)
                        i += 1

                    except OSError:
                        break

                winreg.CloseKey(key)

            except (FileNotFoundError, PermissionError):
                continue
            except Exception as e:
                self.logger.debug(f"Error searching uninstall registry: {e}")
                continue

        return None

    def _search_license_registry(self, plugin_name: str) -> Optional[Dict[str, str]]:
        """
        Search for license information in registry.

        Args:
            plugin_name: Plugin name

        Returns:
            License info dict or None
        """
        name_lower = plugin_name.lower()

        for hkey, subkey_path in self.LICENSE_PATHS:
            try:
                key = winreg.OpenKey(hkey, subkey_path, 0, winreg.KEY_READ)

                # Check for license-related values
                i = 0
                while True:
                    try:
                        value_name, _, _ = winreg.EnumValue(key, i)
                        if name_lower in value_name.lower():
                            winreg.CloseKey(key)
                            return {"status": "registered"}
                        i += 1
                    except OSError:
                        break

                # Check subkeys
                i = 0
                while True:
                    try:
                        subkey_name = winreg.EnumKey(key, i)
                        if name_lower in subkey_name.lower():
                            winreg.CloseKey(key)
                            return {"status": "registered"}
                        i += 1
                    except OSError:
                        break

                winreg.CloseKey(key)

            except (FileNotFoundError, PermissionError):
                continue
            except Exception as e:
                self.logger.debug(f"Error searching license registry: {e}")
                continue

        return None

    def _extract_key_values(self, key: Any) -> Dict[str, Any]:
        """
        Extract all values from a registry key.

        Args:
            key: Open registry key

        Returns:
            Dictionary of values
        """
        values: Dict[str, Any] = {}

        try:
            i = 0
            while True:
                try:
                    value_name, value_data, _ = winreg.EnumValue(key, i)
                    if value_name and value_data:
                        values[value_name] = value_data
                    i += 1
                except OSError:
                    break
        except Exception as e:
            self.logger.debug(f"Error extracting key values: {e}")

        return values

    def _hkey_to_string(self, hkey: int) -> str:
        """Convert HKEY constant to string."""
        if hkey == HKEY_LOCAL_MACHINE:
            return "HKLM"
        if hkey == HKEY_CURRENT_USER:
            return "HKCU"
        if hkey == HKEY_CLASSES_ROOT:
            return "HKCR"
        return "HK??"

    def get_vst_install_paths(self) -> List[str]:
        """
        Get VST installation paths from registry.

        Returns:
            List of VST plugin directories
        """
        if not self.is_windows:
            return []

        paths: List[str] = []

        for hkey, subkey_path in self.VST_REGISTRY_PATHS:
            try:
                key = winreg.OpenKey(hkey, subkey_path, 0, winreg.KEY_READ)

                vst_path = _query_optional_str(key, "VSTPluginsPath")
                if vst_path and vst_path not in paths:
                    paths.append(vst_path)

                i = 0
                while True:
                    try:
                        _, value_data, _ = winreg.EnumValue(key, i)

                        if isinstance(value_data, str) and "\\" in value_data:
                            if Path(value_data).exists() and value_data not in paths:
                                paths.append(value_data)

                        i += 1
                    except OSError:
                        break

                winreg.CloseKey(key)

            except (FileNotFoundError, PermissionError):
                continue

        return paths
