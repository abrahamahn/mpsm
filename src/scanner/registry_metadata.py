"""Registry-based metadata extraction for plugins.

Extracts plugin information stored in Windows registry by DAWs
and plugin managers.
"""

import platform
from pathlib import Path
from typing import Optional, Dict, List, Any
from datetime import datetime

from ..core.logger import get_logger


if platform.system() == 'Windows':
    import winreg


class RegistryMetadataScanner:
    """Extract plugin metadata from Windows registry."""

    # Common registry locations for plugin information
    VST_REGISTRY_PATHS = [
        (winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\VST'),
        (winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\WOW6432Node\VST'),
        (winreg.HKEY_CURRENT_USER, r'Software\VST'),
        (winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\VST3'),
        (winreg.HKEY_CURRENT_USER, r'Software\VST3'),
    ]

    DAW_PLUGIN_PATHS = [
        # Steinberg/Cubase
        (winreg.HKEY_CURRENT_USER, r'Software\Steinberg\Vst2x'),
        (winreg.HKEY_CURRENT_USER, r'Software\Steinberg\VST3Preferences'),
        # Image-Line/FL Studio
        (winreg.HKEY_CURRENT_USER, r'Software\Image-Line\FL Studio\Locations'),
        (winreg.HKEY_CURRENT_USER, r'Software\Image-Line\Shared\Paths'),
        # Ableton Live
        (winreg.HKEY_CURRENT_USER, r'Software\Ableton\Live'),
        # Reaper
        (winreg.HKEY_CURRENT_USER, r'Software\REAPER'),
    ]

    UNINSTALL_PATHS = [
        (winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall'),
        (winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall'),
        (winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Uninstall'),
    ]

    LICENSE_PATHS = [
        # iLok/PACE
        (winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\PACE Anti-Piracy'),
        (winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\WOW6432Node\PACE Anti-Piracy'),
        # Waves
        (winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\Waves'),
        (winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\WOW6432Node\Waves'),
        # Native Instruments
        (winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\Native Instruments'),
    ]

    def __init__(self):
        """Initialize registry scanner."""
        self.logger = get_logger()
        self.is_windows = platform.system() == 'Windows'

    def find_plugin_in_registry(
        self,
        plugin_path: Path,
        plugin_name: str
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

        metadata = {
            'registry_key': None,
            'install_date': None,
            'description': None,
            'website': None,
            'license_status': 'unknown',
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
            metadata['license_status'] = license_info.get('status', 'unknown')

        return metadata

    def _search_daw_databases(
        self,
        plugin_path: Path,
        plugin_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Search DAW plugin databases for information.

        Args:
            plugin_path: Path to plugin
            plugin_name: Plugin name

        Returns:
            Metadata dict or None
        """
        path_str = str(plugin_path).lower()
        name_lower = plugin_name.lower()

        for hkey, subkey_path in self.DAW_PLUGIN_PATHS:
            try:
                key = winreg.OpenKey(hkey, subkey_path, 0, winreg.KEY_READ)

                # Enumerate all subkeys
                i = 0
                while True:
                    try:
                        subkey_name = winreg.EnumKey(key, i)

                        # Check if this subkey relates to our plugin
                        if name_lower in subkey_name.lower():
                            full_path = f"{self._hkey_to_string(hkey)}\\{subkey_path}\\{subkey_name}"

                            # Try to get more info from this key
                            plugin_key = winreg.OpenKey(key, subkey_name, 0, winreg.KEY_READ)
                            info = self._extract_key_values(plugin_key)
                            winreg.CloseKey(plugin_key)

                            if info:
                                info['registry_key'] = full_path
                                winreg.CloseKey(key)
                                return info

                        i += 1
                    except OSError:
                        break

                winreg.CloseKey(key)

            except FileNotFoundError:
                continue
            except PermissionError:
                continue
            except Exception as e:
                self.logger.debug(f"Error searching DAW registry: {e}")
                continue

        return None

    def _search_uninstall_registry(
        self,
        plugin_name: str
    ) -> Optional[Dict[str, Any]]:
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

                        # Open the uninstall entry
                        entry_key = winreg.OpenKey(key, subkey_name, 0, winreg.KEY_READ)

                        # Check DisplayName
                        try:
                            display_name, _ = winreg.QueryValueEx(entry_key, 'DisplayName')
                            if name_lower in display_name.lower():
                                # Extract useful info
                                metadata = {}

                                # Publisher
                                try:
                                    publisher, _ = winreg.QueryValueEx(entry_key, 'Publisher')
                                    metadata['publisher'] = publisher
                                except:
                                    pass

                                # Install date
                                try:
                                    install_date, _ = winreg.QueryValueEx(entry_key, 'InstallDate')
                                    # Format: YYYYMMDD
                                    if install_date:
                                        metadata['install_date'] = datetime.strptime(
                                            install_date, '%Y%m%d'
                                        ).isoformat()
                                except:
                                    pass

                                # Website
                                try:
                                    url, _ = winreg.QueryValueEx(entry_key, 'URLInfoAbout')
                                    metadata['website'] = url
                                except:
                                    pass

                                # Help link (alternative to website)
                                try:
                                    help_link, _ = winreg.QueryValueEx(entry_key, 'HelpLink')
                                    if 'website' not in metadata:
                                        metadata['website'] = help_link
                                except:
                                    pass

                                # Version
                                try:
                                    version, _ = winreg.QueryValueEx(entry_key, 'DisplayVersion')
                                    metadata['version_string'] = version
                                except:
                                    pass

                                # Description
                                try:
                                    comments, _ = winreg.QueryValueEx(entry_key, 'Comments')
                                    metadata['description'] = comments
                                except:
                                    pass

                                winreg.CloseKey(entry_key)
                                winreg.CloseKey(key)
                                return metadata

                        except:
                            pass

                        winreg.CloseKey(entry_key)
                        i += 1

                    except OSError:
                        break

                winreg.CloseKey(key)

            except FileNotFoundError:
                continue
            except PermissionError:
                continue
            except Exception as e:
                self.logger.debug(f"Error searching uninstall registry: {e}")
                continue

        return None

    def _search_license_registry(
        self,
        plugin_name: str
    ) -> Optional[Dict[str, str]]:
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
                        value_name, value_data, value_type = winreg.EnumValue(key, i)

                        if name_lower in value_name.lower():
                            # Found something related to this plugin
                            winreg.CloseKey(key)
                            return {'status': 'registered'}

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
                            return {'status': 'registered'}

                        i += 1
                    except OSError:
                        break

                winreg.CloseKey(key)

            except FileNotFoundError:
                continue
            except PermissionError:
                continue
            except Exception as e:
                self.logger.debug(f"Error searching license registry: {e}")
                continue

        return None

    def _extract_key_values(self, key) -> Dict[str, Any]:
        """
        Extract all values from a registry key.

        Args:
            key: Open registry key

        Returns:
            Dictionary of values
        """
        values = {}

        try:
            i = 0
            while True:
                try:
                    value_name, value_data, value_type = winreg.EnumValue(key, i)
                    if value_name and value_data:
                        values[value_name] = value_data
                    i += 1
                except OSError:
                    break
        except Exception as e:
            self.logger.debug(f"Error extracting key values: {e}")

        return values

    def _hkey_to_string(self, hkey) -> str:
        """Convert HKEY constant to string."""
        if hkey == winreg.HKEY_LOCAL_MACHINE:
            return 'HKLM'
        elif hkey == winreg.HKEY_CURRENT_USER:
            return 'HKCU'
        elif hkey == winreg.HKEY_CLASSES_ROOT:
            return 'HKCR'
        else:
            return 'HK??'

    def get_vst_install_paths(self) -> List[str]:
        """
        Get VST installation paths from registry.

        Returns:
            List of VST plugin directories
        """
        if not self.is_windows:
            return []

        paths = []

        for hkey, subkey_path in self.VST_REGISTRY_PATHS:
            try:
                key = winreg.OpenKey(hkey, subkey_path, 0, winreg.KEY_READ)

                try:
                    # Try to get VSTPluginsPath value
                    path, _ = winreg.QueryValueEx(key, 'VSTPluginsPath')
                    if path and path not in paths:
                        paths.append(path)
                except:
                    pass

                # Enumerate all values
                i = 0
                while True:
                    try:
                        value_name, value_data, value_type = winreg.EnumValue(key, i)

                        if isinstance(value_data, str) and '\\' in value_data:
                            # Looks like a path
                            if Path(value_data).exists() and value_data not in paths:
                                paths.append(value_data)

                        i += 1
                    except OSError:
                        break

                winreg.CloseKey(key)

            except FileNotFoundError:
                continue
            except PermissionError:
                continue

        return paths
