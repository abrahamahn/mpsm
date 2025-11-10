"""VST plugin signature detection and validation."""

from pathlib import Path
from typing import List

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

# VST2 signature patterns
VST_SIGNATURES = [
    b"VSTPluginMain",
    b"VstPlugin",
    b"VST",
    b"VSTXML",
    b"AudioEffect",
    b"AEffect",
    b"VSTi",
    b"VSTx",
    b"main",
    b"MAIN",
]


def is_blacklisted(file_path: Path) -> bool:
    """
    Check if file matches blacklist patterns.

    Args:
        file_path: Path to check

    Returns:
        True if blacklisted
    """
    filename_lower = file_path.name.lower()

    for pattern in BLACKLISTED_PATTERNS:
        if pattern in filename_lower:
            return True

    return False


def has_vst_signature(dll_path: Path) -> bool:
    """
    Check if DLL contains VST signatures.

    Args:
        dll_path: Path to DLL file

    Returns:
        True if VST signatures found
    """
    try:
        # Read first 128KB (increased from 8KB for better detection)
        with open(dll_path, "rb") as f:
            data = f.read(131072)  # 128KB

            # Check for VST signatures
            for signature in VST_SIGNATURES:
                if signature in data:
                    return True

        return False

    except Exception:
        return False


def is_valid_plugin_file(
    file_path: Path, min_size_mb: float = 0.1, max_size_mb: float = 500
) -> bool:
    """
    Validate if file is likely a real plugin.

    Args:
        file_path: Path to file
        min_size_mb: Minimum file size in MB
        max_size_mb: Maximum file size in MB

    Returns:
        True if file passes validation
    """
    # Check if blacklisted
    if is_blacklisted(file_path):
        return False

    # Check file exists
    if not file_path.exists():
        return False

    # Check file size
    file_size_mb = file_path.stat().st_size / (1024 * 1024)

    if file_size_mb < min_size_mb:
        return False

    if file_size_mb > max_size_mb:
        return False

    # For DLLs, check VST signature
    if file_path.suffix.lower() == ".dll":
        if not has_vst_signature(file_path):
            return False

    # VST3, AAX, CLAP are valid by extension
    return True
