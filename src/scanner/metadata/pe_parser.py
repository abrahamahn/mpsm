"""PE (Portable Executable) header parsing for Windows binaries."""

import re
import struct
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import pefile

    HAS_PEFILE = True
except ImportError:
    HAS_PEFILE = False

from ...models.plugin import Version


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

            major = version_info.FileVersionMS >> 16
            minor = version_info.FileVersionMS & 0xFFFF
            patch = version_info.FileVersionLS >> 16

            if major or minor or patch:
                return Version(major=major, minor=minor, patch=patch)

        # Try version string
        if hasattr(pe, "FileInfo"):
            for file_info in pe.FileInfo:
                for entry in file_info:
                    if hasattr(entry, "StringTable"):
                        for st in entry.StringTable:
                            for key, value in st.entries.items():
                                if key in [b"FileVersion", b"ProductVersion"]:
                                    version_str = value.decode("utf-8", errors="ignore")
                                    parsed = parse_version_string(version_str)
                                    if parsed:
                                        return parsed

    except Exception:
        pass

    return None


def get_product_name(file_path: Path) -> str:
    """
    Extract product name from PE header.

    Args:
        file_path: Path to PE file

    Returns:
        Product name or filename
    """
    if not HAS_PEFILE:
        return file_path.stem

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
                                if key in [b"ProductName", b"InternalName", b"OriginalFilename"]:
                                    product_name = value.decode("utf-8", errors="ignore").strip()
                                    if product_name and product_name.lower() not in ["", "null"]:
                                        # Clean up extension if present
                                        product_name = product_name.replace(".dll", "").replace(
                                            ".exe", ""
                                        )
                                        return product_name

    except Exception:
        pass

    return file_path.stem


def get_company_name(file_path: Path) -> str:
    """
    Extract company name from PE header.

    Args:
        file_path: Path to PE file

    Returns:
        Company name or "Unknown"
    """
    if not HAS_PEFILE:
        return "Unknown"

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
                                if key == b"CompanyName":
                                    company = value.decode("utf-8", errors="ignore").strip()
                                    if company and company.lower() not in ["", "null", "unknown"]:
                                        return company

    except Exception:
        pass

    return "Unknown"


def detect_architecture(file_path: Path) -> str:
    """
    Detect architecture (x86/x64) from PE header.

    Args:
        file_path: Path to PE file

    Returns:
        Architecture string: "x64", "x86", or "unknown"
    """
    try:
        # Read PE header
        with open(file_path, "rb") as f:
            # Read DOS header
            dos_header = f.read(64)
            if len(dos_header) < 64 or dos_header[:2] != b"MZ":
                return "unknown"

            # Get PE header offset
            pe_offset = struct.unpack("<I", dos_header[60:64])[0]

            # Read PE header
            f.seek(pe_offset)
            pe_signature = f.read(4)
            if pe_signature != b"PE\x00\x00":
                return "unknown"

            # Read machine type (2 bytes after PE signature)
            machine_type = struct.unpack("<H", f.read(2))[0]

            # Machine types
            IMAGE_FILE_MACHINE_I386 = 0x014C  # x86
            IMAGE_FILE_MACHINE_AMD64 = 0x8664  # x64

            if machine_type == IMAGE_FILE_MACHINE_AMD64:
                return "x64"
            elif machine_type == IMAGE_FILE_MACHINE_I386:
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
    # Remove non-digit prefixes
    version_str = re.sub(r"^[vV]", "", version_str.strip())

    # Extract numbers
    parts = re.findall(r"\d+", version_str)

    if not parts:
        return None

    major = int(parts[0]) if len(parts) > 0 else 0
    minor = int(parts[1]) if len(parts) > 1 else 0
    patch = int(parts[2]) if len(parts) > 2 else 0

    return Version(major=major, minor=minor, patch=patch)
