"""Metadata extraction from plugin files and executables."""

import hashlib
import struct
from pathlib import Path
from typing import Any, Dict, Optional

from ..core.exceptions import MetadataExtractionException
from ..core.logger import get_logger
from ..models.plugin import PluginType, Version


class MetadataExtractor:
    """Extracts metadata from all file types."""

    # Blacklisted DLL patterns (NOT plugins - helper libs, installers, etc.)
    BLACKLISTED_PATTERNS = [
        # Waves internal libraries
        "waveshell",
        "waveslib",
        "libmmd",
        "innerprocess",
        "wavesinit",
        # Microsoft / Visual Studio
        "microsoft.",
        "visualstudio",
        "vs_layout",
        ".resources.dll",
        # ReWire / bridging
        "rewire",
        "jbridge",
        "vst-bridge",
        # Installers / setup
        "setup",
        "installer",
        "unins",
        "install",
        # Temp / cache indicators
        "cache",
        "temp",
        "tmp",
        # Generic helper libs
        "helper",
        "util",
        "common.dll",
        "shared.dll",
    ]

    def __init__(
        self,
        enable_vst_host: bool = False,
        enable_registry: bool = True,
        juce_host_path: Optional[Path] = None,
    ):
        """
        Initialize metadata extractor.

        Args:
            enable_vst_host: Enable external JUCE VST host for plugin_id extraction (safe)
            enable_registry: Enable Windows registry scanning
            juce_host_path: Path to JUCE VST scanner executable (optional)
        """
        self.logger = get_logger()
        self.enable_vst_host = enable_vst_host
        self.enable_registry = enable_registry
        self.juce_host_path = juce_host_path

        # Lazy-load optional components
        self._external_vst_host = None
        self._registry_scanner = None

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
            raise MetadataExtractionException(f"File not found: {file_path}")

        try:
            stat = file_path.stat()

            metadata = {
                "file_name": file_path.name,
                "file_path": str(file_path),
                "file_size": stat.st_size,
                "file_size_mb": round(stat.st_size / (1024 * 1024), 2),
                "modified_time": stat.st_mtime,
                "created_time": stat.st_ctime,
                "extension": file_path.suffix.lower(),
            }

            # Calculate file hash
            metadata["file_hash"] = self.calculate_file_hash(file_path)

            return metadata

        except Exception as e:
            self.logger.error(f"Failed to extract metadata from {file_path}: {e}")
            raise MetadataExtractionException(
                f"Failed to extract metadata", {"file": str(file_path), "error": str(e)}
            )

    def calculate_file_hash(self, file_path: Path, algorithm: str = "sha256") -> str:
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
            with open(file_path, "rb") as f:
                # Read file in chunks to handle large files
                for chunk in iter(lambda: f.read(8192), b""):
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

        if extension == ".vst3":
            return PluginType.VST3
        elif extension == ".dll":
            # Could be VST2 - would need deeper inspection to confirm
            return PluginType.VST2
        elif extension == ".aax":
            return PluginType.AAX
        elif extension == ".clap":
            return PluginType.CLAP
        elif extension in [".component", ".vst"]:
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
        metadata["plugin_type"] = PluginType.VST2.value

        try:
            # Try to extract basic PE information
            with open(file_path, "rb") as f:
                # Read DOS header
                dos_header = f.read(64)
                if len(dos_header) < 64:
                    return metadata

                # Check for MZ signature
                if dos_header[0:2] != b"MZ":
                    return metadata

                # Get PE header offset
                pe_offset = struct.unpack("<I", dos_header[60:64])[0]
                f.seek(pe_offset)

                # Read PE signature
                pe_sig = f.read(4)
                if pe_sig != b"PE\0\0":
                    return metadata

                # Read architecture from Machine field
                machine = struct.unpack("<H", f.read(2))[0]

                if machine == 0x014C:  # IMAGE_FILE_MACHINE_I386
                    metadata["architecture"] = "x86"
                elif machine == 0x8664:  # IMAGE_FILE_MACHINE_AMD64
                    metadata["architecture"] = "x64"
                elif machine == 0xAA64:  # IMAGE_FILE_MACHINE_ARM64
                    metadata["architecture"] = "ARM64"
                else:
                    metadata["architecture"] = "Unknown"

        except Exception as e:
            self.logger.debug(f"Could not extract PE metadata from {file_path}: {e}")
            metadata["architecture"] = "x64"  # Default assumption

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
        metadata["plugin_type"] = PluginType.VST3.value
        metadata["architecture"] = "x64"  # VST3 is typically 64-bit

        # On Windows, VST3 files are typically in .vst3 folders
        # Could inspect moduleinfo.json inside the bundle for more info
        if file_path.is_dir():
            moduleinfo = file_path / "Contents" / "moduleinfo.json"
            if moduleinfo.exists():
                try:
                    import json

                    with open(moduleinfo, "r") as f:
                        info = json.load(f)
                        metadata["version"] = info.get("version", "Unknown")
                        metadata["vendor"] = info.get("vendor", "Unknown")
                        metadata["name"] = info.get("name", file_path.stem)
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
        metadata["plugin_type"] = PluginType.AAX.value
        metadata["architecture"] = "x64"

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

    def detect_architecture(self, file_path: Path) -> str:
        """
        Detect architecture from file path and PE header.

        Args:
            file_path: Path to file

        Returns:
            Architecture string: 'x86', 'x64', 'ARM64', or 'Unknown'

        Note:
            For DLL files, reads PE header. Otherwise checks path for indicators.
        """
        # For DLL files, extract from PE header
        if file_path.suffix.lower() == ".dll":
            dll_metadata = self.extract_dll_metadata(file_path)
            return dll_metadata.get("architecture", "x64")

        # Check path for 32-bit indicators
        path_str = str(file_path).lower()
        if "program files (x86)" in path_str or "x86" in path_str:
            return "x86"

        # Default to x64 for modern plugins
        return "x64"

    def is_blacklisted(self, file_path: Path) -> bool:
        """
        Check if file matches blacklist patterns.

        Args:
            file_path: Path to check

        Returns:
            True if file should be excluded
        """
        filename_lower = file_path.name.lower()
        path_str_lower = str(file_path).lower()

        for pattern in self.BLACKLISTED_PATTERNS:
            if pattern in filename_lower or pattern in path_str_lower:
                self.logger.debug(f"Blacklisted: {file_path.name} (matches pattern: {pattern})")
                return True

        return False

    def is_valid_plugin_file(
        self, file_path: Path, min_size_mb: float = 0.1, max_size_mb: float = 500
    ) -> bool:
        """
        Validate if file is likely a real plugin.

        Args:
            file_path: Path to file
            min_size_mb: Minimum acceptable size in MB
            max_size_mb: Maximum acceptable size in MB

        Returns:
            True if file passes validation checks
        """
        # Check blacklist
        if self.is_blacklisted(file_path):
            return False

        # Check file size
        try:
            file_size_mb = file_path.stat().st_size / (1024 * 1024)
            if file_size_mb < min_size_mb:
                self.logger.debug(f"Too small ({file_size_mb:.2f} MB): {file_path.name}")
                return False
            if file_size_mb > max_size_mb:
                self.logger.debug(f"Too large ({file_size_mb:.2f} MB): {file_path.name}")
                return False
        except:
            return False

        # Type-specific validation
        extension = file_path.suffix.lower()

        # VST2 (DLL): Check for VST signatures
        if extension == ".dll":
            # Lightweight check: scan file for VST signatures
            if not self.has_vst_signature(file_path):
                return False

        # VST3: Always valid (folder or bundle)
        elif extension == ".vst3":
            return True

        # AAX: Always valid (Pro Tools plugins)
        elif extension == ".aax":
            return True

        # CLAP: Always valid (CLAP format)
        elif extension == ".clap":
            return True

        return True

    def has_vst_signature(self, dll_path: Path) -> bool:
        """
        Check if DLL contains VST plugin signatures.

        Args:
            dll_path: Path to DLL file

        Returns:
            True if VST signatures found

        Note:
            Looks for common VST-related strings in the file.
            Not 100% accurate but catches most false positives.
        """
        try:
            with open(dll_path, "rb") as f:
                # Read first 128KB for better coverage (many VST2 plugins have signatures further in)
                data = f.read(131072)

                # Check for VST-related signatures
                vst_signatures = [
                    b"VSTPluginMain",
                    b"VstPlugin",
                    b"VST",
                    b"VSTXML",
                    b"AudioEffect",
                    b"AEffect",
                    b"VSTi",
                    b"VSTx",
                    # Additional common VST2 exports
                    b"main",
                    b"MAIN",
                ]

                for sig in vst_signatures:
                    if sig in data:
                        return True

            # If no signatures found in first 128KB, likely not a plugin
            return False

        except Exception as e:
            self.logger.debug(f"Could not check VST signature for {dll_path}: {e}")
            return True  # Benefit of the doubt

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
            "waves": "Waves",
            "izotope": "iZotope",
            "fabfilter": "FabFilter",
            "native instruments": "Native Instruments",
            "arturia": "Arturia",
            "plugin alliance": "Plugin Alliance",
            "xfer": "Xfer Records",
            "serum": "Xfer Records",
            "sylenth": "LennarDigital",
            "massive": "Native Instruments",
            "kontakt": "Native Instruments",
            "omnisphere": "Spectrasonics",
            "keyscape": "Spectrasonics",
            "spectrasonics": "Spectrasonics",
            # Additional vendors from user's installation
            "zynaptiq": "Zynaptiq",
            "air music": "Air Music Technology",
            "baby audio": "Baby Audio",
            "devious": "DeviousMachines",
            "discodsp": "discoDSP",
            "eventide": "Eventide",
            "fielding": "Fielding DSP",
            "hofa": "HOFA",
            "klanghelm": "Klanghelm",
            "klevgrand": "Klevgrand",
            "korg": "KORG",
            "kv331": "KV331 Audio",
            "lennardigital": "LenndarDigital",
            "newfangled": "Newfangled Audio",
            "ohm force": "Ohm Force",
            "plugin boutique": "Plugin Boutique",
            "press play": "Press Play",
            "propellerhead": "Propellerhead",
            "refx": "reFX",
            "softube": "Softube",
            "sonarworks": "Sonarworks",
            "sonic charge": "Sonic Charge",
            "sonnox": "Sonnox",
            "sononym": "Sononym",
            "tokyo dawn": "Tokyo Dawn Labs",
            "u-he": "u-he",
            "vital": "Vital",
            "voxengo": "Voxengo",
            "xln audio": "XLN Audio",
            "youlean": "Youlean",
            "fl cloud": "FL Cloud Plugins",
            "image-line": "Image-Line",
            "fl studio": "Image-Line",
            "ableton": "Ableton",
            "steinberg": "Steinberg",
            "avid": "Avid",
            # Additional vendors from user's comprehensive plugin list
            "aberrant dsp": "Aberrant DSP",
            "acustica": "Acustica Audio",
            "antelope audio": "Antelope Audio",
            "audiothing": "AudioThing",
            "black rooster": "Black Rooster Audio",
            "boz digital": "Boz Digital Labs",
            "cableguys": "Cableguys",
            "caelum audio": "Caelum Audio",
            "d16": "D16",
            "dada life": "Dada Life",
            "fiedler audio": "Fiedler Audio",
            "future audio workshop": "Future Audio Workshop",
            "faw": "Future Audio Workshop",
            "ignite amps": "Ignite Amps",
            "kilohearts": "Kilohearts",
            "meldaproduction": "MeldaProduction",
            "mixed in key": "Mixed In Key",
            "oeksound": "Oeksound",
            "output": "Output",
            "polyverse": "Polyverse",
            "presonus": "PreSonus",
            "reason studios": "Reason Studios",
            "reveal sound": "Reveal Sound",
            "schrammel": "Schrammel",
            "serato": "Serato",
            "shattered glass": "Shattered Glass Audio",
            "slate digital": "Slate Digital",
            "sonible": "Sonible",
            "sonic academy": "Sonic Academy",
            "soundtheory": "Soundtheory",
            "soundtoys": "Soundtoys",
            "tal": "TAL",
            "tokyo dawn records": "Tokyo Dawn Records",
            "tdr": "Tokyo Dawn Records",
            "united plugins": "United Plugins",
            "valhalla": "Valhalla",
            "vengeance": "Vengeance",
            "wavesfactory": "Wavesfactory",
            "wavetracing": "waveTracing",
            "reaper": "Reaper",
            "cockos": "Cockos",
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
            version_str = version_str.lower().strip().lstrip("v")

            # Split by dots
            parts = version_str.split(".")

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

    def extract_version_from_pe(self, file_path: Path) -> Optional[Version]:
        """
        Extract version information from PE file (DLL/EXE).

        Args:
            file_path: Path to PE file

        Returns:
            Version object or None if extraction fails
        """
        try:
            # Try to use pefile if available
            try:
                import pefile

                pe = pefile.PE(str(file_path), fast_load=True)
                pe.parse_data_directories(
                    directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_RESOURCE"]]
                )

                if hasattr(pe, "FileInfo"):
                    for file_info in pe.FileInfo:
                        for entry in file_info:
                            if hasattr(entry, "StringTable"):
                                for st_entry in entry.StringTable:
                                    for key, value in st_entry.entries.items():
                                        if key.decode("utf-8", errors="ignore").lower() in [
                                            "fileversion",
                                            "productversion",
                                        ]:
                                            version_str = value.decode("utf-8", errors="ignore")
                                            version = self.parse_version_string(version_str)
                                            if version:
                                                return version

            except ImportError:
                # pefile not available, use alternative method
                pass
            except Exception as e:
                self.logger.debug(f"Could not extract version from PE: {e}")

            # Fallback: try to extract from filename
            filename = file_path.stem
            import re

            # Look for version patterns like v1.2.3, 1.2.3, etc.
            version_pattern = r"[vV]?(\d+)[\._](\d+)[\._]?(\d+)?[\._]?(\d+)?"
            match = re.search(version_pattern, filename)
            if match:
                major = int(match.group(1))
                minor = int(match.group(2))
                patch = int(match.group(3)) if match.group(3) else 0
                build = int(match.group(4)) if match.group(4) else None
                return Version(major=major, minor=minor, patch=patch, build=build)

        except Exception as e:
            self.logger.debug(f"Could not extract version from {file_path}: {e}")

        return None

    def generate_plugin_id(self, file_path: Path, publisher: str, name: str) -> str:
        """
        Generate unique plugin ID.

        Args:
            file_path: Path to plugin file
            publisher: Publisher name
            name: Plugin name

        Returns:
            Unique plugin ID string
        """
        # Create ID based on publisher + name + file hash (first 8 chars)
        try:
            file_hash = self.calculate_file_hash(file_path)
            plugin_id = f"{publisher}_{name}_{file_hash[:8]}".replace(" ", "_").replace("-", "_")
            return plugin_id
        except:
            # Fallback to name-based ID
            return f"{publisher}_{name}".replace(" ", "_").replace("-", "_")

    def detect_plugin_category(self, file_path: Path, name: str, publisher: str) -> str:
        """
        Detect plugin category based on name and characteristics.

        Args:
            file_path: Path to plugin file
            name: Plugin name
            publisher: Publisher name

        Returns:
            Category string (e.g., 'fx_compressor', 'inst_synth', 'fx_reverb')
        """
        name_lower = name.lower()
        path_lower = str(file_path).lower()

        # Instrument categories
        if any(
            keyword in name_lower
            for keyword in ["piano", "keys", "keyboard", "electric piano", "grand", "upright"]
        ):
            return "inst_piano"

        if any(
            keyword in name_lower
            for keyword in [
                "synth",
                "synthesizer",
                "analog",
                "wavetable",
                "fm",
                "additive",
                "serum",
                "sylenth",
                "massive",
                "omnisphere",
                "diva",
                "repro",
            ]
        ):
            return "inst_synth"

        if any(
            keyword in name_lower
            for keyword in [
                "drum",
                "beat",
                "percussion",
                "kick",
                "snare",
                "hat",
                "battery",
                "superior drummer",
                "addictive drums",
            ]
        ):
            return "inst_drums"

        if any(
            keyword in name_lower
            for keyword in [
                "strings",
                "orchestra",
                "violin",
                "cello",
                "brass",
                "woodwind",
                "kontakt",
                "spitfire",
                "orchestral",
            ]
        ):
            return "inst_orchestral"

        if any(keyword in name_lower for keyword in ["bass", "sub", "trilian", "scarbee"]):
            return "inst_bass"

        if any(
            keyword in name_lower for keyword in ["guitar", "strum", "acoustic", "electric guitar"]
        ):
            return "inst_guitar"

        if any(
            keyword in name_lower
            for keyword in ["rompler", "sample", "sampler", "library", "multisample"]
        ):
            return "inst_rompler"

        # Effect categories
        if any(
            keyword in name_lower
            for keyword in ["eq", "equalizer", "equalization", "filter", "pro-q", "fabfilter q"]
        ):
            return "fx_eq"

        if any(
            keyword in name_lower
            for keyword in [
                "compressor",
                "compression",
                "dynamics",
                "limiter",
                "pro-c",
                "pro-l",
                "1176",
                "la-2a",
                "ssl comp",
                "vca",
                "opto",
            ]
        ):
            return "fx_compressor"

        if any(
            keyword in name_lower
            for keyword in [
                "reverb",
                "room",
                "hall",
                "chamber",
                "plate",
                "spring",
                "valhalla",
                "convolution",
                "altiverb",
            ]
        ):
            return "fx_reverb"

        if any(
            keyword in name_lower
            for keyword in ["delay", "echo", "repeat", "tape delay", "ping pong"]
        ):
            return "fx_delay"

        if any(
            keyword in name_lower
            for keyword in [
                "distortion",
                "saturation",
                "overdrive",
                "fuzz",
                "clipper",
                "decapitator",
                "saturn",
            ]
        ):
            return "fx_distortion"

        if any(
            keyword in name_lower
            for keyword in ["modulation", "chorus", "flanger", "phaser", "tremolo", "vibrato"]
        ):
            return "fx_modulation"

        if any(
            keyword in name_lower for keyword in ["gate", "noise gate", "expander", "transient"]
        ):
            return "fx_gate"

        if any(
            keyword in name_lower
            for keyword in ["pitch", "autotune", "melodyne", "pitch correct", "tuning"]
        ):
            return "fx_pitch"

        if any(
            keyword in name_lower
            for keyword in ["master", "mastering", "finalizer", "ozone", "isotope mastering"]
        ):
            return "fx_mastering"

        if any(
            keyword in name_lower
            for keyword in ["utility", "tool", "meter", "analyzer", "spectrum", "phase"]
        ):
            return "fx_utility"

        # Check if it's likely an instrument or effect based on common patterns
        if (
            any(keyword in name_lower for keyword in ["vsti", "instrument", "inst", "player"])
            or "vsti" in path_lower
        ):
            return "inst_other"

        if any(keyword in name_lower for keyword in ["fx", "effect", "process"]):
            return "fx_other"

        # Default
        return "unknown"

    def find_registry_key_for_plugin(
        self, file_path: Path, plugin_name: str, plugin_type: PluginType
    ) -> Optional[str]:
        """
        Find registry key associated with a plugin.

        Args:
            file_path: Path to plugin file
            plugin_name: Plugin name
            plugin_type: Plugin type (VST2, VST3, etc.)

        Returns:
            Registry key path or None if not found
        """
        try:
            # Only works on Windows
            import platform

            if platform.system() != "Windows":
                return None

            import winreg

            # Common registry locations for plugins
            registry_locations = []

            if plugin_type == PluginType.VST2:
                registry_locations = [
                    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\VST"),
                    (winreg.HKEY_CURRENT_USER, r"Software\VST"),
                ]
            elif plugin_type == PluginType.VST3:
                registry_locations = [
                    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\VST3"),
                    (winreg.HKEY_CURRENT_USER, r"Software\VST3"),
                ]

            # Search for plugin in registry
            file_path_str = str(file_path).lower()
            plugin_name_lower = plugin_name.lower()

            for hkey, subkey_path in registry_locations:
                try:
                    key = winreg.OpenKey(hkey, subkey_path, 0, winreg.KEY_READ)

                    # Enumerate subkeys
                    i = 0
                    while True:
                        try:
                            subkey_name = winreg.EnumKey(key, i)

                            # Check if subkey name matches plugin
                            if plugin_name_lower in subkey_name.lower():
                                full_path = f"{hkey}\\{subkey_path}\\{subkey_name}"
                                winreg.CloseKey(key)
                                return full_path

                            # Open subkey and check values
                            try:
                                subkey = winreg.OpenKey(key, subkey_name, 0, winreg.KEY_READ)
                                j = 0
                                while True:
                                    try:
                                        value_name, value_data, value_type = winreg.EnumValue(
                                            subkey, j
                                        )

                                        # Check if value contains file path
                                        if (
                                            isinstance(value_data, str)
                                            and value_data.lower() in file_path_str
                                        ):
                                            full_path = f"{hkey}\\{subkey_path}\\{subkey_name}"
                                            winreg.CloseKey(subkey)
                                            winreg.CloseKey(key)
                                            return full_path

                                        j += 1
                                    except OSError:
                                        break
                                winreg.CloseKey(subkey)
                            except:
                                pass

                            i += 1
                        except OSError:
                            break

                    winreg.CloseKey(key)
                except FileNotFoundError:
                    continue
                except PermissionError:
                    continue

        except Exception as e:
            self.logger.debug(f"Could not find registry key for {plugin_name}: {e}")

        return None

    def extract_comprehensive_metadata(
        self, file_path: Path, plugin_type: PluginType
    ) -> Dict[str, Any]:
        """
        Extract comprehensive metadata using all available methods.

        This combines:
        - File system metadata (always)
        - PE header data (if available)
        - VST host loading (if enabled and safe)
        - Windows registry (if enabled and Windows)

        Args:
            file_path: Path to plugin file
            plugin_type: Plugin type (VST2, VST3, AAX, CLAP)

        Returns:
            Dictionary with all extracted metadata
        """
        # Start with basic file metadata
        metadata = self.extract_file_metadata(file_path)
        metadata["plugin_type"] = plugin_type

        # Add PE-based metadata
        if plugin_type == PluginType.VST2:
            dll_metadata = self.extract_dll_metadata(file_path)
            metadata.update(dll_metadata)
        elif plugin_type == PluginType.VST3:
            vst3_metadata = self.extract_vst3_metadata(file_path)
            metadata.update(vst3_metadata)
        elif plugin_type == PluginType.AAX:
            aax_metadata = self.extract_aax_metadata(file_path)
            metadata.update(aax_metadata)

        # Extract version from PE
        version = self.extract_version_from_pe(file_path)
        if version:
            metadata["version"] = version

        # Extract from registry if enabled
        if self.enable_registry:
            registry_metadata = self._get_registry_metadata(
                file_path, metadata.get("file_name", file_path.stem)
            )
            if registry_metadata:
                metadata.update(registry_metadata)

        # Extract from VST host if enabled and is VST2
        if self.enable_vst_host and plugin_type == PluginType.VST2:
            vst_metadata = self._get_vst_host_metadata(file_path)
            if vst_metadata:
                metadata.update(vst_metadata)

        return metadata

    def _get_registry_scanner(self):
        """Lazy-load registry scanner."""
        if self._registry_scanner is None:
            try:
                from .registry_metadata import RegistryMetadataScanner

                self._registry_scanner = RegistryMetadataScanner()
            except ImportError as e:
                self.logger.debug(f"Registry scanner not available: {e}")
                self._registry_scanner = False  # Don't try again
        return self._registry_scanner if self._registry_scanner is not False else None

    def _get_registry_metadata(self, file_path: Path, plugin_name: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata from Windows registry.

        Args:
            file_path: Path to plugin
            plugin_name: Plugin name

        Returns:
            Metadata dict or None
        """
        scanner = self._get_registry_scanner()
        if not scanner:
            return None

        try:
            return scanner.find_plugin_in_registry(file_path, plugin_name)
        except Exception as e:
            self.logger.debug(f"Registry metadata extraction failed: {e}")
            return None

    def _get_vst_host_metadata(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        Get metadata by loading plugin via external JUCE host.

        This is SAFE - uses a separate JUCE process that won't crash MPSM.

        Args:
            file_path: Path to VST2/VST3 plugin

        Returns:
            Metadata dict or None
        """
        try:
            # Lazy-load external VST host
            if not self._external_vst_host:
                from .external_vst_host import ExternalVSTHost, find_juce_host

                # Find JUCE host executable
                juce_path = self.juce_host_path or find_juce_host()
                if not juce_path:
                    self.logger.warning(
                        "JUCE VST Scanner not found. Please build it first. "
                        "Place VSTScanner.exe in bin/ or tools/ directory."
                    )
                    self.enable_vst_host = False  # Disable for this session
                    return None

                self._external_vst_host = ExternalVSTHost(juce_host_path=juce_path)
                self._external_vst_host.start()

            # Extract metadata via external host
            vst_data = self._external_vst_host.extract_metadata(file_path)

            if vst_data:
                # Map JUCE host data to our metadata format
                metadata = {}

                if vst_data.get("plugin_id"):
                    metadata["plugin_id"] = vst_data["plugin_id"]

                if vst_data.get("plugin_id_hex"):
                    metadata["plugin_id_hex"] = vst_data["plugin_id_hex"]

                if vst_data.get("name"):
                    metadata["vst_name"] = vst_data["name"]

                if vst_data.get("vendor"):
                    metadata["vst_vendor"] = vst_data["vendor"]

                if vst_data.get("category"):
                    metadata["vst_category"] = vst_data["category"]

                if vst_data.get("version"):
                    metadata["vst_version"] = vst_data["version"]

                if vst_data.get("num_inputs"):
                    metadata["num_inputs"] = vst_data["num_inputs"]

                if vst_data.get("num_outputs"):
                    metadata["num_outputs"] = vst_data["num_outputs"]

                if vst_data.get("is_synth"):
                    metadata["is_synth"] = vst_data["is_synth"]

                return metadata

        except Exception as e:
            self.logger.debug(f"External VST host metadata extraction failed: {e}")

        return None
