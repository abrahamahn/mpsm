"""Main metadata extractor using modular components."""

import hashlib
from pathlib import Path
from typing import Any, Dict, Optional

from ...core.exceptions import MetadataExtractionException
from ...core.logger import get_logger
from ...models.plugin import PluginType, Version

# Import modular components
from . import pe_parser, publisher_identifier, vst_detector


class MetadataExtractor:
    """Extracts metadata from plugin files using modular components."""

    def __init__(
        self,
        enable_vst_host: bool = False,
        enable_registry: bool = True,
        juce_host_path: Optional[Path] = None,
    ):
        """
        Initialize metadata extractor.

        Args:
            enable_vst_host: Enable external JUCE VST host for plugin_id extraction
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

    # ============================================================
    # Core File Operations
    # ============================================================

    def extract_file_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract basic file metadata."""
        if not file_path.exists():
            raise MetadataExtractionException(f"File not found: {file_path}")

        try:
            stat = file_path.stat()
            return {
                "file_name": file_path.name,
                "file_path": str(file_path),
                "file_size": stat.st_size,
                "file_size_mb": round(stat.st_size / (1024 * 1024), 2),
                "modified_time": stat.st_mtime,
                "created_time": stat.st_ctime,
                "extension": file_path.suffix.lower(),
                "file_hash": self.calculate_file_hash(file_path),
            }
        except Exception as e:
            self.logger.error(f"Failed to extract metadata from {file_path}: {e}")
            raise MetadataExtractionException(
                "Failed to extract metadata", {"file": str(file_path), "error": str(e)}
            )

    def calculate_file_hash(self, file_path: Path, algorithm: str = "sha256") -> str:
        """Calculate file hash (SHA-256 by default)."""
        hash_func = hashlib.new(algorithm)

        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    hash_func.update(chunk)
            return hash_func.hexdigest()
        except Exception as e:
            self.logger.warning(f"Failed to calculate hash for {file_path}: {e}")
            return ""

    # ============================================================
    # Plugin Type Detection
    # ============================================================

    def detect_plugin_type(self, file_path: Path) -> PluginType:
        """Detect plugin type from file extension."""
        ext = file_path.suffix.lower()

        if ext == ".vst3":
            return PluginType.VST3
        elif ext == ".dll":
            return PluginType.VST2
        elif ext == ".aax":
            return PluginType.AAX
        elif ext == ".clap":
            return PluginType.CLAP
        else:
            return PluginType.UNKNOWN

    # ============================================================
    # Validation (delegates to vst_detector)
    # ============================================================

    def is_valid_plugin_file(
        self, file_path: Path, min_size_mb: float = 0.1, max_size_mb: float = 500
    ) -> bool:
        """Validate if file is a real plugin."""
        return vst_detector.is_valid_plugin_file(file_path, min_size_mb, max_size_mb)

    def is_blacklisted(self, file_path: Path) -> bool:
        """Check if file is blacklisted."""
        return vst_detector.is_blacklisted(file_path)

    def has_vst_signature(self, dll_path: Path) -> bool:
        """Check for VST signatures in DLL."""
        return vst_detector.has_vst_signature(dll_path)

    # ============================================================
    # PE Header Extraction (delegates to pe_parser)
    # ============================================================

    def extract_version_from_pe(self, file_path: Path) -> Optional[Version]:
        """Extract version from PE header."""
        return pe_parser.extract_version_from_pe(file_path)

    def get_product_name(self, file_path: Path) -> str:
        """Get product name from PE header."""
        return pe_parser.get_product_name(file_path)

    def detect_architecture(self, file_path: Path) -> str:
        """Detect architecture (x86/x64)."""
        return pe_parser.detect_architecture(file_path)

    # ============================================================
    # Publisher Identification (delegates to publisher_identifier)
    # ============================================================

    def identify_publisher(self, file_path: Path) -> str:
        """Identify publisher from path."""
        return publisher_identifier.identify_publisher_from_path(file_path)

    # ============================================================
    # Category Detection
    # ============================================================

    def detect_plugin_category(self, file_path: Path, name: str, publisher: str) -> str:
        """Detect plugin category from name/path."""
        name_lower = name.lower()
        path_lower = str(file_path).lower()
        combined = f"{name_lower} {path_lower}"

        # FX categories
        if any(word in combined for word in ["comp", "compressor", "dynamics"]):
            return "fx_compressor"
        elif any(word in combined for word in ["eq", "equalizer", "filter"]):
            return "fx_eq"
        elif any(word in combined for word in ["reverb", "verb", "room"]):
            return "fx_reverb"
        elif any(word in combined for word in ["delay", "echo"]):
            return "fx_delay"
        elif any(word in combined for word in ["chorus", "flanger", "phaser"]):
            return "fx_modulation"
        elif any(word in combined for word in ["distortion", "overdrive", "saturator"]):
            return "fx_distortion"
        elif any(word in combined for word in ["limiter", "maximizer"]):
            return "fx_limiter"

        # Instrument categories
        elif any(word in combined for word in ["synth", "synthesizer", "vsti"]):
            return "inst_synth"
        elif any(word in combined for word in ["sampler", "kontakt", "sample"]):
            return "inst_sampler"
        elif any(word in combined for word in ["drum", "percussion", "beat"]):
            return "inst_drum"
        elif any(word in combined for word in ["piano", "keys", "keyboard"]):
            return "inst_piano"
        elif any(word in combined for word in ["guitar", "bass", "string"]):
            return "inst_guitar"

        return "unknown"

    # ============================================================
    # External VST Host Integration
    # ============================================================

    def _get_vst_host_metadata(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Get metadata via external JUCE host."""
        try:
            if not self._external_vst_host:
                from ..external_vst_host import ExternalVSTHost, find_juce_host

                juce_path = self.juce_host_path or find_juce_host()
                if not juce_path:
                    self.logger.warning(
                        "JUCE VST Scanner not found. "
                        "Place VSTScanner.exe in bin/ or tools/ directory."
                    )
                    self.enable_vst_host = False
                    return None

                self._external_vst_host = ExternalVSTHost(juce_host_path=juce_path)
                self._external_vst_host.start()

            vst_data = self._external_vst_host.extract_metadata(file_path)

            if vst_data:
                metadata = {}
                if vst_data.get("plugin_id"):
                    metadata["plugin_id"] = vst_data["plugin_id"]
                if vst_data.get("name"):
                    metadata["vst_name"] = vst_data["name"]
                if vst_data.get("vendor"):
                    metadata["vst_vendor"] = vst_data["vendor"]
                if vst_data.get("version"):
                    metadata["vst_version"] = vst_data["version"]
                return metadata

        except Exception as e:
            self.logger.debug(f"External VST host failed: {e}")

        return None

    # ============================================================
    # Registry Integration
    # ============================================================

    def _get_registry_metadata(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Get metadata from Windows registry."""
        if not self.enable_registry:
            return None

        try:
            if not self._registry_scanner:
                from ..registry_metadata import RegistryMetadataScanner

                self._registry_scanner = RegistryMetadataScanner()

            return self._registry_scanner.find_plugin_metadata(file_path)

        except Exception as e:
            self.logger.debug(f"Registry metadata extraction failed: {e}")
            return None
