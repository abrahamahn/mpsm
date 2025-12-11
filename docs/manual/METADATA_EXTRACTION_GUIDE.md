# Complete Plugin Metadata Extraction Guide

## Overview

This guide explains what metadata can be extracted from VST/AAX/CLAP plugins, how to extract it, and the limitations of each approach.

---

## Understanding the Fields

### file_hash
**What it is**: SHA-256 cryptographic hash of the entire file
**Example**: `c210976346b3664ee09655589edbd9f429d07bee6354460abcae5b6ed9ac67f7`
**Use**: Uniquely identify exact plugin versions, detect duplicates, verify file integrity
**Extraction**: ✅ **Always available** (file system)

```python
import hashlib
with open('plugin.dll', 'rb') as f:
    hash_sha256 = hashlib.sha256(f.read()).hexdigest()
```

### plugin_id
**What it is**: Unique plugin identifier
- **VST2**: 4-character code (e.g., `'ABCD'` stored as int32: `1094861636`)
- **VST3**: 128-bit GUID from bundle
**Use**: DAWs use this to match plugins when loading projects
**Extraction**: ⚠️ **Requires VST host** (dynamic loading)

**Why it was blank**: Static file analysis can't see it - must load the DLL and read the `AEffect` struct.

---

## Metadata Extraction Methods

### Method 1: File System (Always Available)
**Risk**: None
**Speed**: ⚡ Very fast
**What you get**:
- ✅ name (filename)
- ✅ file_path
- ✅ file_size
- ✅ file_hash
- ✅ architecture (x86/x64 from PE header)
- ⚠️ install_date (file creation time, not true install date)

### Method 2: PE Headers (Windows DLLs/EXEs)
**Risk**: None
**Speed**: ⚡ Fast
**What you get**:
- ✅ publisher (CompanyName in VS_VERSIONINFO)
- ✅ version (FileVersion in VS_VERSIONINFO)
- ✅ architecture (from PE Machine field)
- ⚠️ description (FileDescription, often generic)
- ⚠️ website (from LegalCopyright, unreliable)

**Library**: `pefile`

### Method 3: Windows Registry (Windows only)
**Risk**: None
**Speed**: ⚡ Fast
**What you get**:
- ✅ registry_key (where plugin is registered)
- ✅ install_date (from Uninstall registry)
- ✅ publisher (from Uninstall registry)
- ✅ website (from Uninstall registry)
- ✅ description (from Uninstall registry)
- ⚠️ license_status (limited - only for some vendors)

**Locations Scanned**:
- `HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall`
- `HKCU\Software\Steinberg\Vst2x` (Cubase)
- `HKCU\Software\Image-Line\FL Studio` (FL Studio)
- `HKLM\SOFTWARE\PACE Anti-Piracy` (iLok licenses)
- `HKLM\SOFTWARE\Waves` (Waves licenses)

### Method 4: VST Host (VST2 only)
**Risk**: ⚠️ **High** - Can crash if plugin is unstable
**Speed**: 🐌 Slow (loads DLL)
**What you get**:
- ✅ plugin_id (unique VST2 ID)
- ✅ name (effGetEffectName)
- ✅ vendor (effGetVendorString)
- ✅ category (effGetPlugCategory: effect/instrument)
- ✅ version (vendor version number)
- ✅ num_inputs, num_outputs, num_params

**SAFETY**: Always run in isolated process (can crash)

---

## What's NOT Extractable

### ❌ Completely Impossible

1. **License Status (generally)**
   - Most vendors use external license managers (iLok, PACE, eLicenser)
   - No standard API to query license status
   - **Exception**: Some vendors store flags in registry (Waves, iLok)

2. **Detailed Description**
   - Not embedded in VST2 DLLs
   - Some registry entries have short descriptions
   - Would need to scrape vendor websites

3. **Website (reliably)**
   - Some DLLs have copyright strings with URLs
   - Registry uninstall entries sometimes have "URLInfoAbout"
   - Not standardized

### ⚠️ Partially Available

1. **Category (detailed)**
   - **VST2 host**: Returns basic category (effect/instrument)
   - **Our heuristics**: Detect specific types (compressor, reverb, synth) from filename
   - **Best**: Combine both approaches

2. **Install Date**
   - **File creation time**: Not true install date
   - **Registry**: Only if in Uninstall keys (most plugins are)

3. **License Path**
   - Can scan for `.lic`, `.ilok`, `.key` files nearby
   - Not reliable - licenses often stored elsewhere

---

## Usage Examples

### Basic Scan (Safe, Fast)
```python
from pathlib import Path
from src.scanner.metadata_extractor import MetadataExtractor
from src.models.plugin import PluginType

# Create extractor (registry enabled, VST host disabled)
extractor = MetadataExtractor(
    enable_vst_host=False,  # Safe mode
    enable_registry=True    # Get Windows registry data
)

# Scan a plugin
plugin_path = Path('C:/Program Files/VSTPlugins/MyPlugin.dll')
plugin_type = extractor.detect_plugin_type(plugin_path)

# Get comprehensive metadata
metadata = extractor.extract_comprehensive_metadata(plugin_path, plugin_type)

print(metadata)
# {
#     'file_name': 'MyPlugin.dll',
#     'file_path': 'C:/Program Files/VSTPlugins/MyPlugin.dll',
#     'file_size': 5242880,
#     'file_hash': 'c21097...',
#     'version': Version(1, 2, 3),
#     'publisher': 'Example Audio LLC',
#     'architecture': 'x64',
#     'registry_key': 'HKLM\\SOFTWARE\\Example\\MyPlugin',
#     'install_date': '2024-01-15T10:30:00',
#     'website': 'https://example-audio.com',
#     'license_status': 'registered',
# }
```

### Advanced Scan with VST Host (Risky)
```python
# Enable VST host for plugin_id extraction
extractor = MetadataExtractor(
    enable_vst_host=True,   # ⚠️ Can crash!
    enable_registry=True
)

metadata = extractor.extract_comprehensive_metadata(plugin_path, PluginType.VST2)

print(metadata)
# Additional fields:
# {
#     'plugin_id': 'ABCD',          # 4-char VST2 ID
#     'plugin_id_int': 1094861636,  # as integer
#     'vst_name': 'My Plugin',
#     'vst_vendor': 'Example Audio',
#     'vst_category': 'fx_compressor',
# }
```

### Direct VST Host Usage
```python
from pathlib import Path
from src.scanner.vst_host import VSTHost, format_plugin_id

# Load plugin in VST host
with VSTHost() as host:
    if host.load_plugin(Path('plugin.dll')):
        # Get plugin ID
        plugin_id = host.get_plugin_id()
        print(f"Plugin ID: {format_plugin_id(plugin_id)}")  # 'ABCD'

        # Get all metadata
        metadata = host.get_metadata()
        print(metadata)
        # {
        #     'plugin_id': 1094861636,
        #     'name': 'My Compressor',
        #     'vendor': 'Audio Co',
        #     'category': 'fx_compressor',
        #     'version': 10203,  # 1.2.3
        # }
```

### Registry-Only Scan
```python
from src.scanner.registry_metadata import RegistryMetadataScanner

scanner = RegistryMetadataScanner()

# Find plugin in registry
metadata = scanner.find_plugin_in_registry(
    plugin_path=Path('C:/Program Files/VSTPlugins/Plugin.dll'),
    plugin_name='My Plugin'
)

print(metadata)
# {
#     'registry_key': 'HKLM\\SOFTWARE\\MyVendor\\MyPlugin',
#     'install_date': '2024-01-15T10:30:00',
#     'description': 'Audio compressor plugin',
#     'website': 'https://vendor.com',
#     'license_status': 'registered',  # or 'unknown'
# }

# Get all VST install paths from registry
vst_paths = scanner.get_vst_install_paths()
print(vst_paths)
# ['C:\\Program Files\\VSTPlugins', 'C:\\Program Files\\Steinberg\\VSTPlugins']
```

---

## Complete Field Matrix

| Field | File System | PE Header | Registry | VST Host | Notes |
|-------|-------------|-----------|----------|----------|-------|
| **name** | ✅ Always | ⚠️ FileDescription | ❌ | ✅ VST2 | Filename vs plugin name |
| **publisher** | ❌ | ✅ CompanyName | ✅ Best source | ✅ VST2 | Registry most reliable |
| **plugin_id** | ❌ | ❌ | ❌ | ✅ **VST host only** | Must load DLL |
| **type** | ✅ Extension | ❌ | ❌ | ✅ VST2 | .dll/.vst3/.aax |
| **category** | ⚠️ Heuristic | ❌ | ❌ | ⚠️ Basic | VST: fx/inst only |
| **version** | ❌ | ✅ FileVersion | ⚠️ DisplayVersion | ✅ VST2 | PE header best |
| **file_path** | ✅ Always | ❌ | ❌ | ❌ | Trivial |
| **file_size** | ✅ Always | ❌ | ❌ | ❌ | Trivial |
| **file_hash** | ✅ Always | ❌ | ❌ | ❌ | SHA-256 |
| **architecture** | ❌ | ✅ PE Machine | ❌ | ❌ | x86/x64/ARM |
| **registry_key** | ❌ | ❌ | ✅ **Registry only** | ❌ | Windows specific |
| **install_date** | ⚠️ File ctime | ❌ | ✅ Better | ❌ | Registry preferred |
| **description** | ❌ | ⚠️ FileDescription | ✅ Best | ❌ | Often generic |
| **website** | ❌ | ⚠️ LegalCopyright | ✅ URLInfoAbout | ❌ | Not always present |
| **license_status** | ❌ | ❌ | ⚠️ Limited | ❌ | Vendor-specific |
| **license_path** | ⚠️ Search nearby | ❌ | ⚠️ Limited | ❌ | Not reliable |

**Legend**:
- ✅ Reliably available
- ⚠️ Partially available / unreliable
- ❌ Not available

---

## Configuration in mpsm.py

Add to `config.yaml`:
```yaml
scan:
  metadata:
    # Enable Windows registry scanning (safe, fast)
    enable_registry: true

    # Enable VST host loading (risky, slow, but gets plugin_id)
    enable_vst_host: false  # Set true only if needed

    # VST host timeout (seconds)
    vst_host_timeout: 5

    # Scan for license files
    scan_license_files: true
```

---

## Safety Recommendations

### ✅ Safe Methods (Use Always)
1. File system metadata
2. PE header extraction
3. Windows registry scanning

### ⚠️ Risky Methods (Use with Caution)
1. **VST host loading**
   - Can crash if plugin requires audio drivers
   - Can crash if plugin has bugs
   - Can hang if plugin waits for GUI
   - **Solution**: Run in separate process with timeout

### 🚫 Don't Even Try
1. Emulating iLok/PACE license checks
2. Querying eLicenser dongles
3. Scraping vendor websites in real-time (too slow)

---

## Performance Comparison

| Method | Speed | Risk | plugin_id | Full Metadata |
|--------|-------|------|-----------|---------------|
| File system | ⚡⚡⚡ <1ms | None | ❌ | 30% |
| PE headers | ⚡⚡ <5ms | None | ❌ | 60% |
| Registry | ⚡⚡ <10ms | None | ❌ | 80% |
| VST host | 🐌 100-500ms | High | ✅ | 95% |

**Recommendation**: Use File+PE+Registry for speed, add VST host only if you need `plugin_id`.

---

## Conclusion

### What You Can Get Reliably
- ✅ name, publisher, version, file_path, file_size, file_hash, architecture
- ✅ registry_key, install_date (from registry)
- ✅ description, website (from registry, when available)
- ✅ plugin_id (VST2 only, requires host loading)
- ✅ category (heuristic-based, ~70% accurate)

### What You Can't Get
- ❌ License status (except vendor-specific cases)
- ❌ Detailed descriptions (not embedded)
- ❌ Reliable category for all plugins

### Best Practice
1. **Default**: Use `enable_vst_host=False, enable_registry=True`
2. **If you need plugin_id**: Run VST host in batch mode, separately
3. **License checking**: Use vendor-specific APIs (iLok, eLicenser) externally

---

**Created**: 2025-11-10
**Last Updated**: 2025-11-10
