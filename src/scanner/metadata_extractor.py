"""Metadata extraction from plugin files and executables."""

import hashlib
from pathlib import Path
from typing import Optional, Dict, Any
import struct

from ..core.logger import get_logger
from ..core.exceptions import MetadataExtractionException
from ..models.plugin import PluginType, Version


class MetadataExtractor:
    """Extracts metadata from all file types."""

    def __init__(self):
        """Initialize metadata extractor."""
        self.logger = get_logger()

    def extract_file_metadata(self, file_path: Path) -> Dict[str, Any]:
        """
        Extract basic file metadata.

        Args:
            file_path: Path to file

        Returns:
            Dictionary with file metadata

        Raises:
            MetadataExtractionException: If extraction fails
        """
        if not file_path.exists():
            raise MetadataExtractionException(
                f"File not found: {file_path}"
            )

        try:
            stat = file_path.stat()

            metadata = {
                'file_name': file_path.name,
                'file_path': str(file_path),
                'file_size': stat.st_size,
                'file_size_mb': round(stat.st_size / (1024 * 1024), 2),
                'modified_time': stat.st_mtime,
                'created_time': stat.st_ctime,
                'extension': file_path.suffix.lower(),
            }

            # Calculate file hash
            metadata['file_hash'] = self.calculate_file_hash(file_path)

            return metadata

        except Exception as e:
            self.logger.error(f"Failed to extract metadata from {file_path}: {e}")
            raise MetadataExtractionException(
                f"Failed to extract metadata",
                {'file': str(file_path), 'error': str(e)}
            )

    def calculate_file_hash(self, file_path: Path, algorithm: str = 'sha256') -> str:
        """
        Calculate file hash.

        Args:
            file_path: Path to file
            algorithm: Hash algorithm (md5, sha1, sha256)

        Returns:
            Hex digest of file hash
        """
        hash_func = hashlib.new(algorithm)

        try:
            with open(file_path, 'rb') as f:
                # Read file in chunks to handle large files
                for chunk in iter(lambda: f.read(8192), b''):
                    hash_func.update(chunk)

            return hash_func.hexdigest()

        except Exception as e:
            self.logger.warning(f"Could not calculate hash for {file_path}: {e}")
            return ""

    def detect_plugin_type(self, file_path: Path) -> PluginType:
        """
        Detect plugin type from file extension and structure.

        Args:
            file_path: Path to plugin file

        Returns:
            PluginType enum value
        """
        extension = file_path.suffix.lower()

        if extension == '.vst3':
            return PluginType.VST3
        elif extension == '.dll':
            # Could be VST2 - would need deeper inspection to confirm
            return PluginType.VST2
        elif extension == '.aax':
            return PluginType.AAX
        elif extension == '.clap':
            return PluginType.CLAP
        elif extension in ['.component', '.vst']:
            return PluginType.AU
        else:
            return PluginType.UNKNOWN

    def extract_dll_metadata(self, file_path: Path) -> Dict[str, Any]:
        """
        Extract metadata from DLL file (VST2).

        Args:
            file_path: Path to DLL file

        Returns:
            Dictionary with metadata

        Note:
            This is a simplified version. Full implementation would use
            pefile library to extract detailed PE header information.
        """
        metadata = self.extract_file_metadata(file_path)
        metadata['plugin_type'] = PluginType.VST2.value

        try:
            # Try to extract basic PE information
            with open(file_path, 'rb') as f:
                # Read DOS header
                dos_header = f.read(64)
                if len(dos_header) < 64:
                    return metadata

                # Check for MZ signature
                if dos_header[0:2] != b'MZ':
                    return metadata

                # Get PE header offset
                pe_offset = struct.unpack('<I', dos_header[60:64])[0]
                f.seek(pe_offset)

                # Read PE signature
                pe_sig = f.read(4)
                if pe_sig != b'PE\0\0':
                    return metadata

                # Read architecture from Machine field
                machine = struct.unpack('<H', f.read(2))[0]

                if machine == 0x014c:  # IMAGE_FILE_MACHINE_I386
                    metadata['architecture'] = 'x86'
                elif machine == 0x8664:  # IMAGE_FILE_MACHINE_AMD64
                    metadata['architecture'] = 'x64'
                elif machine == 0xaa64:  # IMAGE_FILE_MACHINE_ARM64
                    metadata['architecture'] = 'ARM64'
                else:
                    metadata['architecture'] = 'Unknown'

        except Exception as e:
            self.logger.debug(f"Could not extract PE metadata from {file_path}: {e}")
            metadata['architecture'] = 'x64'  # Default assumption

        return metadata

    def extract_vst3_metadata(self, file_path: Path) -> Dict[str, Any]:
        """
        Extract metadata from VST3 file.

        Args:
            file_path: Path to VST3 file

        Returns:
            Dictionary with metadata

        Note:
            VST3 files are bundles (directories) on macOS and packages on Windows.
            This is a simplified implementation.
        """
        metadata = self.extract_file_metadata(file_path)
        metadata['plugin_type'] = PluginType.VST3.value
        metadata['architecture'] = 'x64'  # VST3 is typically 64-bit

        # On Windows, VST3 files are typically in .vst3 folders
        # Could inspect moduleinfo.json inside the bundle for more info
        if file_path.is_dir():
            moduleinfo = file_path / 'Contents' / 'moduleinfo.json'
            if moduleinfo.exists():
                try:
                    import json
                    with open(moduleinfo, 'r') as f:
                        info = json.load(f)
                        metadata['version'] = info.get('version', 'Unknown')
                        metadata['vendor'] = info.get('vendor', 'Unknown')
                        metadata['name'] = info.get('name', file_path.stem)
                except Exception as e:
                    self.logger.debug(f"Could not read moduleinfo.json: {e}")

        return metadata

    def extract_aax_metadata(self, file_path: Path) -> Dict[str, Any]:
        """
        Extract metadata from AAX file (Pro Tools).

        Args:
            file_path: Path to AAX file

        Returns:
            Dictionary with metadata
        """
        metadata = self.extract_file_metadata(file_path)
        metadata['plugin_type'] = PluginType.AAX.value
        metadata['architecture'] = 'x64'

        return metadata

    def extract_exe_metadata(self, file_path: Path) -> Dict[str, Any]:
        """
        Extract metadata from executable file.

        Args:
            file_path: Path to EXE file

        Returns:
            Dictionary with metadata
        """
        metadata = self.extract_file_metadata(file_path)

        # Similar to DLL, could use pefile to extract version info
        # For now, just basic file metadata
        return metadata

    def identify_publisher(self, file_path: Path) -> str:
        """
        Identify publisher from file path or metadata.

        Args:
            file_path: Path to file

        Returns:
            Publisher name or "Unknown"

        Note:
            This is a heuristic-based approach. Looks for known vendor
            names in the path.
        """
        path_str = str(file_path).lower()

        # Known publishers (keyword -> publisher name mapping)
        publishers = {
            # Major vendors
            'waves': 'Waves',
            'izotope': 'iZotope',
            'fabfilter': 'FabFilter',
            'native instruments': 'Native Instruments',
            'arturia': 'Arturia',
            'plugin alliance': 'Plugin Alliance',
            'xfer': 'Xfer Records',
            'serum': 'Xfer Records',
            'sylenth': 'LennarDigital',
            'massive': 'Native Instruments',
            'kontakt': 'Native Instruments',
            'omnisphere': 'Spectrasonics',
            'keyscape': 'Spectrasonics',
            'spectrasonics': 'Spectrasonics',
            # Additional vendors from user's installation
            'zynaptiq': 'Zynaptiq',
            'air music': 'Air Music Technology',
            'baby audio': 'Baby Audio',
            'devious': 'DeviousMachines',
            'discodsp': 'discoDSP',
            'eventide': 'Eventide',
            'fielding': 'Fielding DSP',
            'hofa': 'HOFA',
            'klanghelm': 'Klanghelm',
            'klevgrand': 'Klevgrand',
            'korg': 'KORG',
            'kv331': 'KV331 Audio',
            'lennardigital': 'LenndarDigital',
            'newfangled': 'Newfangled Audio',
            'ohm force': 'Ohm Force',
            'plugin boutique': 'Plugin Boutique',
            'press play': 'Press Play',
            'propellerhead': 'Propellerhead',
            'refx': 'reFX',
            'softube': 'Softube',
            'sonarworks': 'Sonarworks',
            'sonic charge': 'Sonic Charge',
            'sonnox': 'Sonnox',
            'sononym': 'Sononym',
            'tokyo dawn': 'Tokyo Dawn Labs',
            'u-he': 'u-he',
            'vital': 'Vital',
            'voxengo': 'Voxengo',
            'xln audio': 'XLN Audio',
            'youlean': 'Youlean',
            'fl cloud': 'FL Cloud Plugins',
            'image-line': 'Image-Line',
            'fl studio': 'Image-Line',
            'ableton': 'Ableton',
            'steinberg': 'Steinberg',
            'avid': 'Avid',
        }

        for keyword, publisher in publishers.items():
            if keyword in path_str:
                return publisher

        # Try to extract from path
        parts = file_path.parts
        if len(parts) > 2:
            # Check if there's a vendor folder
            for part in parts:
                for keyword, publisher in publishers.items():
                    if keyword in part.lower():
                        return publisher

        return "Unknown"

    def get_product_name(self, file_path: Path) -> str:
        """
        Get product name from file.

        Args:
            file_path: Path to file

        Returns:
            Product name (defaults to filename without extension)
        """
        # Default to stem (filename without extension)
        return file_path.stem

    def parse_version_string(self, version_str: str) -> Optional[Version]:
        """
        Parse version string into Version object.

        Args:
            version_str: Version string (e.g., "1.2.3" or "v1.2.3.4")

        Returns:
            Version object or None if parsing fails
        """
        try:
            # Remove 'v' prefix if present
            version_str = version_str.lower().strip().lstrip('v')

            # Split by dots
            parts = version_str.split('.')

            if len(parts) < 2:
                return None

            major = int(parts[0]) if parts[0].isdigit() else 0
            minor = int(parts[1]) if parts[1].isdigit() else 0
            patch = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0
            build = int(parts[3]) if len(parts) > 3 and parts[3].isdigit() else None

            return Version(major=major, minor=minor, patch=patch, build=build)

        except (ValueError, IndexError) as e:
            self.logger.debug(f"Could not parse version string '{version_str}': {e}")
            return None
