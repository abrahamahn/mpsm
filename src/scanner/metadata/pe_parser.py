"""PE (Portable Executable) header parsing for Windows binaries."""

import re
import struct
from pathlib import Path
from typing import List, Optional

try:
    import pefile

    HAS_PEFILE = True
except ImportError:
    HAS_PEFILE = False

from ...models.plugin import Version


def _extract_pe_string(file_path: Path, target_keys: List[bytes]) -> Optional[str]:
    """Extract the first matching non-empty string entry from a PE StringTable."""
    if not HAS_PEFILE:
        return None

    try:
        pe = pefile.PE(str(file_path), fast_load=True)
        pe.parse_data_directories(
            directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_RESOURCE"]]
        )

        if hasattr(pe, "FileInfo"):
            for file_info in pe.FileInfo:
                for entry in file_info:
                    if hasattr(entry, "StringTable"):
                        for st in entry.StringTable:
                            for key, value in st.entries.items():
                                if key in target_keys:
                                    decoded = str(value.decode("utf-8", errors="ignore")).strip()
                                    if decoded and decoded.lower() not in ["", "null", "unknown"]:
                                        return decoded
    except Exception:
        pass

    return None


def extract_version_from_pe(file_path: Path) -> Optional[Version]:
    """
    Extract version from PE header.

    Args:
        file_path: Path to PE file (.dll, .exe)

    Returns:
        Version object or None
    """
    if not HAS_PEFILE:
        return None

    try:
        pe = pefile.PE(str(file_path), fast_load=True)
        pe.parse_data_directories(
            directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_RESOURCE"]]
        )

        if hasattr(pe, "VS_FIXEDFILEINFO") and pe.VS_FIXEDFILEINFO:
            version_info = pe.VS_FIXEDFILEINFO[0]

            major = int(version_info.FileVersionMS >> 16)
            minor = int(version_info.FileVersionMS & 0xFFFF)
            patch = int(version_info.FileVersionLS >> 16)

            if major or minor or patch:
                return Version(major=major, minor=minor, patch=patch)
    except Exception:
        pass

    version_str = _extract_pe_string(file_path, [b"FileVersion", b"ProductVersion"])
    if version_str:
        return parse_version_string(version_str)

    return None


def get_product_name(file_path: Path) -> str:
    """
    Extract product name from PE header.

    Args:
        file_path: Path to PE file

    Returns:
        Product name or filename
    """
    product_name = _extract_pe_string(
        file_path, [b"ProductName", b"InternalName", b"OriginalFilename"]
    )
    if product_name:
        return product_name.replace(".dll", "").replace(".exe", "")

    return file_path.stem


def get_company_name(file_path: Path) -> str:
    """
    Extract company name from PE header.

    Args:
        file_path: Path to PE file

    Returns:
        Company name or "Unknown"
    """
    return _extract_pe_string(file_path, [b"CompanyName"]) or "Unknown"


def detect_architecture(file_path: Path) -> str:
    """
    Detect architecture (x86/x64) from PE header.

    Args:
        file_path: Path to PE file

    Returns:
        Architecture string: "x64", "x86", or "unknown"
    """
    try:
        with open(file_path, "rb") as f:
            dos_header = f.read(64)
            if len(dos_header) < 64 or dos_header[:2] != b"MZ":
                return "unknown"

            pe_offset = struct.unpack("<I", dos_header[60:64])[0]

            f.seek(pe_offset)
            pe_signature = f.read(4)
            if pe_signature != b"PE\x00\x00":
                return "unknown"

            machine_type = struct.unpack("<H", f.read(2))[0]

            image_file_machine_i386 = 0x014C  # x86
            image_file_machine_amd64 = 0x8664  # x64

            if machine_type == image_file_machine_amd64:
                return "x64"
            if machine_type == image_file_machine_i386:
                return "x86"

    except Exception:
        pass

    return "unknown"


def parse_version_string(version_str: str) -> Optional[Version]:
    """
    Parse version string into Version object.

    Args:
        version_str: Version string (e.g., "1.2.3", "v1.2.3.4")

    Returns:
        Version object or None
    """
    version_str = re.sub(r"^[vV]", "", version_str.strip())
    parts = re.findall(r"\d+", version_str)

    if not parts:
        return None

    major = int(parts[0]) if len(parts) > 0 else 0
    minor = int(parts[1]) if len(parts) > 1 else 0
    patch = int(parts[2]) if len(parts) > 2 else 0

    return Version(major=major, minor=minor, patch=patch)
