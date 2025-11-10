# MPSM Technical Framework
## Music Production Software Manager - Implementation Blueprint

**Version**: 1.0
**Target Platform**: Windows 11
**Language**: Python 3.9+
**Architecture**: Modular CLI Application

---

## Table of Contents

1. [System Architecture](#1-system-architecture)
2. [Module Specifications](#2-module-specifications)
3. [Data Models](#3-data-models)
4. [Core Utilities](#4-core-utilities)
5. [Configuration Management](#5-configuration-management)
6. [Error Handling & Safety](#6-error-handling--safety)
7. [Testing Strategy](#7-testing-strategy)
8. [Implementation Phases](#8-implementation-phases)
9. [Technical Specifications](#9-technical-specifications)

---

## 1. System Architecture

### 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        CLI Interface                         │
│                         (mpsm.py)                           │
└──────────────────┬──────────────────────────────────────────┘
                   │
┌──────────────────┴──────────────────────────────────────────┐
│                    Core Orchestrator                         │
│              (Coordinates all operations)                    │
└──────────────────┬──────────────────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
┌───────▼───────┐   ┌────────▼─────────┐
│  Data Layer   │   │  Service Layer   │
│               │   │                  │
│ • Config      │   │ • Scanner        │
│ • Models      │   │ • Registry Mgr   │
│ • Database    │   │ • Updater        │
│ • Validators  │   │ • License Track  │
└───────────────┘   │ • Installer      │
                    └──────────────────┘
```

### 1.2 Directory Structure

```
mpsm/
├── mpsm.py                     # Main entry point (CLI)
├── config.yaml                 # User configuration
├── requirements.txt            # Python dependencies
├── setup.py                    # Installation script
│
├── src/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── orchestrator.py    # Main coordination logic
│   │   ├── config.py          # Configuration management
│   │   ├── logger.py          # Logging system
│   │   └── exceptions.py      # Custom exceptions
│   │
│   ├── scanner/
│   │   ├── __init__.py
│   │   ├── file_scanner.py        # Filesystem scanning
│   │   ├── application_scanner.py # Application/executable scanning
│   │   ├── folder_analyzer.py     # Folder structure analysis
│   │   ├── metadata_extractor.py  # Metadata from all file types
│   │   ├── registry_reader.py     # Comprehensive registry queries
│   │   └── plugin_detector.py     # Component identification
│   │
│   ├── registry/
│   │   ├── __init__.py
│   │   ├── manager.py         # Registry operations
│   │   ├── backup.py          # Registry backups
│   │   └── validator.py       # Path validation
│   │
│   ├── updater/
│   │   ├── __init__.py
│   │   ├── version_checker.py # Version comparison
│   │   ├── vendor_scrapers.py # Vendor website scrapers
│   │   └── downloader.py      # Update downloads
│   │
│   ├── license/
│   │   ├── __init__.py
│   │   ├── tracker.py         # License tracking
│   │   ├── ilok_manager.py    # iLok integration
│   │   └── validator.py       # License validation
│   │
│   ├── installer/
│   │   ├── __init__.py
│   │   ├── path_manager.py    # Installation path control
│   │   ├── symlink_manager.py # Symbolic link creation
│   │   └── silent_installer.py # Silent installation
│   │
│   ├── organizer/
│   │   ├── __init__.py
│   │   ├── file_mover.py          # Safe file/folder operations
│   │   ├── structure_builder.py   # Target folder structure
│   │   ├── consolidator.py        # Complete installation consolidation
│   │   ├─ relationship_manager.py # Component relationship tracking
│   │   └── registry_path_updater.py # Registry path updates after moves
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── plugin.py          # Plugin data model
│   │   ├── daw.py             # DAW data model
│   │   ├── license.py         # License data model
│   │   └── scan_result.py     # Scan result model
│   │
│   └── utils/
│       ├── __init__.py
│       ├── file_operations.py # Safe file ops
│       ├── validators.py      # Input validation
│       ├── formatters.py      # Output formatting
│       └── system_info.py     # System detection
│
├── data/                       # Runtime data
│   ├── scan_results.csv
│   ├── scan_results.xlsx
│   └── plugin_database.db
│
├── backups/                    # Backup storage
│   ├── registry/
│   └── files/
│
├── logs/                       # Log files
│   └── mpsm_YYYYMMDD_HHMMSS.log
│
└── tests/                      # Test suite
    ├── __init__.py
    ├── test_scanner.py
    ├── test_registry.py
    ├── test_updater.py
    ├── test_license.py
    └── test_installer.py
```

---

## 2. Module Specifications

### 2.1 Scanner Module (`scanner/`)

**Purpose**: Discover and catalog ALL music production software components on the system.

#### Scan Scope (Comprehensive):

1. **Plugin Files**: VST2 (.dll), VST3 (.vst3), AAX (.aax), CLAP (.clap)
2. **Plugin Applications**: Full installation folders with executables, resources, DLLs
3. **Plugin Managers**: Waves Central, Native Access, iLok License Manager, Plugin Alliance, etc.
4. **Data Folders**: Presets, samples, user content, configurations
5. **DAW Installations**: FL Studio, Ableton, and all their components
6. **Registry Entries**: All registry keys related to above components
7. **Support Files**: Documentation, uninstallers, licenses, activation files

#### Key Components:

**`file_scanner.py`**
```python
class FileScanner:
    """Comprehensive filesystem scanner for all music production components."""

    def scan_directory(self, path: str, extensions: List[str]) -> List[Path]
    def scan_for_executables(self, path: str) -> List[Path]
    def scan_plugin_folders(self, path: str) -> List[PluginFolder]
    def scan_data_folders(self, path: str) -> List[DataFolder]
    def exclude_paths(self, paths: List[str]) -> None
    def scan_parallel(self, root_paths: List[str]) -> Iterator[Path]
    def detect_folder_type(self, folder_path: Path) -> FolderType
```

**`metadata_extractor.py`**
```python
class MetadataExtractor:
    """Extracts metadata from all file types."""

    # Plugin files
    def extract_dll_metadata(self, file_path: Path) -> PluginMetadata
    def extract_vst3_metadata(self, file_path: Path) -> PluginMetadata
    def extract_aax_metadata(self, file_path: Path) -> PluginMetadata

    # Executables
    def extract_exe_metadata(self, file_path: Path) -> ExeMetadata
    def get_file_version(self, file_path: Path) -> Version
    def identify_publisher(self, file_path: Path) -> str
    def get_product_name(self, file_path: Path) -> str

    # Folders
    def analyze_folder_structure(self, folder_path: Path) -> FolderMetadata
    def detect_preset_folder(self, folder_path: Path) -> bool
    def detect_sample_folder(self, folder_path: Path) -> bool
```

**`registry_reader.py`**
```python
class RegistryReader:
    """Comprehensive Windows Registry scanner."""

    # VST paths
    def get_vst_paths(self) -> List[str]
    def get_vst3_paths(self) -> List[str]

    # DAW paths
    def get_daw_paths(self) -> Dict[str, str]
    def get_fl_studio_registry(self) -> Dict[str, Any]
    def get_ableton_registry(self) -> Dict[str, Any]

    # Plugin installations
    def find_plugin_registry_keys(self, plugin_name: str) -> List[str]
    def get_all_uninstaller_keys(self) -> List[UninstallEntry]
    def get_plugin_manager_keys(self) -> Dict[str, str]

    # Comprehensive scan
    def scan_all_music_production_keys(self) -> Dict[str, Any]
    def map_registry_to_files(self, file_paths: List[Path]) -> Dict[Path, str]
    def export_registry_snapshot(self, output_path: Path) -> None

    # Known registry locations
    KNOWN_KEYS = [
        r"HKEY_LOCAL_MACHINE\SOFTWARE\VST",
        r"HKEY_LOCAL_MACHINE\SOFTWARE\VST3",
        r"HKEY_CURRENT_USER\Software\Image-Line",
        r"HKEY_CURRENT_USER\Software\Ableton",
        r"HKEY_LOCAL_MACHINE\SOFTWARE\Waves",
        r"HKEY_LOCAL_MACHINE\SOFTWARE\iZotope",
        r"HKEY_LOCAL_MACHINE\SOFTWARE\Native Instruments",
        r"HKEY_LOCAL_MACHINE\SOFTWARE\Arturia",
        r"HKEY_LOCAL_MACHINE\SOFTWARE\FabFilter",
        # ... more vendor keys
    ]
```

**`plugin_detector.py`**
```python
class PluginDetector:
    """Identifies all types of music production components."""

    # Plugin files
    def detect_plugin_type(self, file_path: Path) -> PluginType
    def identify_vendor(self, metadata: PluginMetadata) -> Vendor
    def categorize_plugin(self, plugin: Plugin) -> Category

    # Applications
    def is_plugin_manager(self, file_path: Path) -> bool
    def is_plugin_application(self, folder_path: Path) -> bool
    def detect_manager_type(self, exe_path: Path) -> ManagerType

    # Folders
    def is_preset_folder(self, folder_path: Path) -> bool
    def is_sample_library(self, folder_path: Path) -> bool
    def is_plugin_installation(self, folder_path: Path) -> bool
    def get_folder_owner(self, folder_path: Path) -> Optional[str]

    # Known patterns
    PLUGIN_MANAGER_PATTERNS = {
        "Waves Central": ["WavesCentral.exe", "Waves"],
        "Native Access": ["Native Access.exe", "Native Instruments"],
        "iLok License Manager": ["iLok License Manager.exe", "PACE"],
        "Plugin Alliance": ["Plugin Alliance.exe"],
        "Arturia Software Center": ["Arturia Software Center.exe"],
        "Splice": ["Splice.exe"],
        "Output Hub": ["Output Hub.exe"],
    }

    PRESET_FOLDER_PATTERNS = [
        "**/Presets/**",
        "**/User Presets/**",
        "**/Factory/**",
        "**/Sounds/**",
        "**/.vstpreset",
    ]

    SAMPLE_FOLDER_PATTERNS = [
        "**/Samples/**",
        "**/Libraries/**",
        "**/Content/**",
        "**/Expansion/**",
    ]
```

**`application_scanner.py`** (NEW)
```python
class ApplicationScanner:
    """Scans for installed music production applications."""

    def scan_program_files(self) -> List[Application]
    def scan_appdata(self) -> List[Application]
    def detect_plugin_manager_apps(self) -> List[PluginManager]
    def find_related_executables(self, plugin_name: str) -> List[Path]
    def map_application_to_plugins(self, app: Application) -> List[Plugin]

    def get_application_info(self, exe_path: Path) -> ApplicationInfo:
        """Get comprehensive application information."""
        return ApplicationInfo(
            name=...,
            publisher=...,
            version=...,
            install_path=...,
            executable=exe_path,
            registry_key=...,
            related_folders=[...],
            related_plugins=[...],
        )
```

**`folder_analyzer.py`** (NEW)
```python
class FolderAnalyzer:
    """Analyzes folder structures for music production content."""

    def analyze_plugin_installation(self, folder: Path) -> PluginInstallation
    def find_data_folders(self, plugin_name: str) -> List[DataFolder]
    def calculate_folder_size(self, folder: Path) -> int
    def map_folder_relationships(self, folders: List[Path]) -> Dict[Path, List[Path]]

    def get_folder_contents(self, folder: Path) -> FolderContents:
        """Get detailed folder contents."""
        return FolderContents(
            path=folder,
            executables=[...],
            dlls=[...],
            plugins=[...],
            presets=[...],
            samples=[...],
            configs=[...],
            docs=[...],
            total_size=...,
        )
```

#### Data Flow:
```
FileScanner ──────────┐
ApplicationScanner ───┼──→ MetadataExtractor ──→ PluginDetector ──→ Database
FolderAnalyzer ───────┤                              ↓
                      └──────────────────→ RegistryReader
                                                      ↓
                                          Registry-to-File Mapper
```

#### Comprehensive Scan Workflow:

```
1. Initialize Scan
   ├─> Load configuration
   ├─> Create backup point
   └─> Initialize database/output

2. File System Scan (Parallel)
   ├─> FileScanner
   │   ├─> Scan for plugin files (.dll, .vst3, .aax)
   │   ├─> Scan for executables (.exe)
   │   └─> Scan for license files (.lic, .key)
   │
   ├─> ApplicationScanner
   │   ├─> Detect plugin managers (Waves Central, Native Access, etc.)
   │   ├─> Detect standalone plugins
   │   └─> Map applications to plugins
   │
   └─> FolderAnalyzer
       ├─> Identify installation folders
       ├─> Identify preset folders
       ├─> Identify sample libraries
       └─> Calculate folder sizes

3. Metadata Extraction (Parallel)
   ├─> Extract plugin metadata (DLL/VST3/AAX)
   ├─> Extract executable metadata (version, publisher)
   ├─> Analyze folder structures
   └─> Identify vendors and products

4. Registry Scan
   ├─> Scan known registry keys
   ├─> Find plugin-related entries
   ├─> Map registry entries to files
   ├─> Detect orphaned entries
   └─> Extract uninstaller information

5. Relationship Mapping
   ├─> Link plugins to installation folders
   ├─> Link plugins to data folders
   ├─> Link plugins to registry entries
   ├─> Link applications to managed plugins
   └─> Identify complete installations

6. Validation & Issue Detection
   ├─> Detect broken links
   ├─> Find missing licenses
   ├─> Identify registry mismatches
   ├─> Find orphaned folders
   └─> Detect orphaned registry entries

7. Data Aggregation
   ├─> Build ComprehensiveScanResult
   ├─> Generate statistics
   └─> Create issue reports

8. Export Results
   ├─> Export to CSV (multiple files)
   ├─> Export to Excel (multiple sheets)
   ├─> Generate summary report
   └─> Create visualization data
```

#### Example Scan Output:

For "Serum" plugin, the comprehensive scan would find:

**1. Plugin Files**:
   - `C:\Program Files\Common Files\VST3\Serum.vst3`
   - `C:\Program Files\VstPlugins\Serum_x64.dll`

**2. Installation Folder**:
   - `C:\Program Files\Xfer\Serum\`
     - `Serum.exe` (standalone)
     - `Serum_x64.dll` (VST2)
     - `Resources\` folder
     - `Documentation.pdf`

**3. Data Folders**:
   - `C:\Users\{USER}\Documents\Xfer\Serum\Presets\` (2,345 files, 145 MB)
   - `C:\Users\{USER}\Documents\Xfer\Serum\Wavetables\` (1,234 files, 89 MB)
   - `C:\Users\{USER}\Documents\Xfer\Serum\Skins\` (12 files, 3 MB)

**4. Registry Entries**:
   - `HKLM\SOFTWARE\Xfer\Serum\InstallPath` = "C:\Program Files\Xfer\Serum"
   - `HKCU\Software\Xfer\Serum\PresetsPath` = "C:\Users\{USER}\Documents\Xfer\Serum\Presets"
   - `HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Serum`

**5. Related Files**:
   - License: `C:\ProgramData\Xfer\Serum\Serum.lic`
   - Uninstaller: `C:\Program Files\Xfer\Serum\uninstall.exe`

**6. Complete Installation Summary**:
```
Plugin: Serum by Xfer Records
Version: 1.36b5
Total Size: 1.2 GB
Components:
  - 2 plugin files (VST2, VST3)
  - 1 standalone executable
  - 3 data folders (3,591 files)
  - 3 registry keys
  - 1 license file
Status: ✓ Complete, ✓ Licensed, ✓ No Issues
```

---

### 2.2 Registry Manager Module (`registry/`)

**Purpose**: Safely manage Windows Registry modifications for plugin paths.

#### Key Components:

**`manager.py`**
```python
class RegistryManager:
    """Manages registry operations."""

    def backup_key(self, key_path: str) -> Path
    def update_path(self, key_path: str, old_path: str, new_path: str) -> bool
    def batch_update(self, updates: List[PathUpdate]) -> BatchResult
    def rollback(self, backup_path: Path) -> bool
    def verify_update(self, key_path: str, expected_path: str) -> bool
```

**`backup.py`**
```python
class RegistryBackup:
    """Handles registry backup operations."""

    def create_backup(self, keys: List[str]) -> BackupArchive
    def restore_backup(self, backup_id: str) -> bool
    def list_backups(self) -> List[BackupInfo]
    def cleanup_old_backups(self, keep_days: int) -> None
```

**`validator.py`**
```python
class PathValidator:
    """Validates registry path changes."""

    def validate_path_exists(self, path: str) -> bool
    def validate_plugin_loadable(self, plugin_path: str) -> bool
    def test_daw_scan(self, daw: DAW) -> ScanResult
```

#### Safety Features:
- Automatic backup before any modification
- Transaction-based updates (all-or-nothing)
- Rollback capability
- Dry-run mode for testing
- Path existence validation

---

### 2.3 Updater Module (`updater/`)

**Purpose**: Check for and apply plugin updates automatically.

#### Key Components:

**`version_checker.py`**
```python
class VersionChecker:
    """Compares installed vs latest versions."""

    def get_installed_version(self, plugin: Plugin) -> Version
    def get_latest_version(self, plugin: Plugin) -> Version
    def compare_versions(self, current: Version, latest: Version) -> VersionStatus
    def check_all_plugins(self) -> List[UpdateAvailable]
```

**`vendor_scrapers.py`**
```python
class VendorScraperBase:
    """Base class for vendor-specific scrapers."""

    def get_latest_version(self, product_name: str) -> Version
    def get_download_url(self, product_name: str) -> str
    def parse_changelog(self, html: str) -> Changelog

class WavesScraper(VendorScraperBase): ...
class iZotopeScraper(VendorScraperBase): ...
class FabFilterScraper(VendorScraperBase): ...
# ... additional vendor scrapers
```

**`downloader.py`**
```python
class Downloader:
    """Downloads and verifies updates."""

    def download_update(self, url: str, output_path: Path) -> Path
    def verify_checksum(self, file_path: Path, expected: str) -> bool
    def extract_installer(self, archive_path: Path) -> Path
    def run_silent_install(self, installer: Path, args: List[str]) -> bool
```

#### Update Flow:
```
VersionChecker → VendorScraper → Downloader → SilentInstaller → Verification
```

---

### 2.4 License Tracker Module (`license/`)

**Purpose**: Track, verify, and centralize license files.

#### Key Components:

**`tracker.py`**
```python
class LicenseTracker:
    """Tracks license status for all plugins."""

    def scan_license_files(self) -> List[LicenseFile]
    def verify_license(self, plugin: Plugin) -> LicenseStatus
    def centralize_licenses(self, target_dir: Path) -> None
    def export_license_report(self) -> pd.DataFrame
```

**`ilok_manager.py`**
```python
class iLokManager:
    """Interfaces with PACE iLok system."""

    def get_activated_plugins(self) -> List[str]
    def check_activation_status(self, plugin_name: str) -> ActivationStatus
    def list_available_licenses(self) -> List[License]
```

**`validator.py`**
```python
class LicenseValidator:
    """Validates license files and status."""

    def validate_license_file(self, file_path: Path) -> ValidationResult
    def check_expiration(self, license: License) -> ExpirationStatus
    def verify_machine_id(self, license: License) -> bool
```

#### License Status Types:
- **Verified**: License active and valid
- **Pending**: License found but not activated
- **Expired**: License past expiration date
- **Missing**: No license found for plugin
- **iLok**: Managed through iLok system

---

### 2.5 Installer Module (`installer/`)

**Purpose**: Control installation paths for new plugins.

#### Key Components:

**`path_manager.py`**
```python
class PathManager:
    """Manages custom installation paths."""

    def set_installation_path(self, plugin_type: PluginType, path: Path) -> None
    def create_path_structure(self, root: Path) -> None
    def get_install_path_for_plugin(self, plugin: Plugin) -> Path
```

**`symlink_manager.py`**
```python
class SymlinkManager:
    """Creates and manages symbolic links."""

    def create_junction(self, target: Path, link: Path) -> bool
    def create_symlink(self, target: Path, link: Path) -> bool
    def remove_symlink(self, link: Path) -> bool
    def verify_symlink(self, link: Path) -> bool
```

**`silent_installer.py`**
```python
class SilentInstaller:
    """Runs installers in silent mode."""

    def detect_installer_type(self, installer_path: Path) -> InstallerType
    def get_silent_flags(self, installer_type: InstallerType) -> List[str]
    def run_installer(self, installer: Path, custom_path: Path) -> InstallResult
    def monitor_installation(self, process: Process) -> InstallStatus
```

---

### 2.6 Organizer Module (`organizer/`)

**Purpose**: Reorganize ALL music production components into clean structure.

#### Comprehensive Organization Scope:

The organizer handles complete plugin installations, not just individual files:

1. **Plugin Files**: Move VST2/VST3/AAX files to organized locations
2. **Applications**: Move standalone executables and plugin managers
3. **Data Folders**: Relocate presets, samples, user content
4. **Registry Updates**: Update all registry paths to reflect new locations
5. **Relationship Preservation**: Maintain links between components

#### Key Components:

**`file_mover.py`**
```python
class FileMover:
    """Safely moves files with backup and verification."""

    def move_file(self, source: Path, dest: Path, backup: bool = True) -> MoveResult
    def move_folder(self, source: Path, dest: Path, backup: bool = True) -> MoveResult
    def batch_move(self, operations: List[MoveOperation]) -> BatchResult
    def verify_move(self, source: Path, dest: Path) -> bool
    def rollback_move(self, operation_id: str) -> bool
    def estimate_move_time(self, size_bytes: int) -> float
```

**`structure_builder.py`**
```python
class StructureBuilder:
    """Builds target folder structure for all components."""

    def create_structure(self, root: Path, config: Config) -> None
    def validate_structure(self, root: Path) -> ValidationResult

    # Mapping functions
    def map_plugin_file_location(self, plugin: Plugin) -> Path
    def map_application_location(self, app: Application) -> Path
    def map_data_folder_location(self, folder: DataFolder) -> Path
    def map_installation_location(self, installation: PluginInstallation) -> Dict[str, Path]

    # Example mappings:
    # Plugin file: C:\MusicProduction\Plugins\VST3\Serum.vst3
    # Standalone: C:\MusicProduction\Plugins\Xfer\Serum\Serum.exe
    # Presets: C:\MusicProduction\Libraries\Serum\Presets\
    # Samples: C:\MusicProduction\Libraries\Serum\Wavetables\
```

**`consolidator.py`**
```python
class Consolidator:
    """Consolidates complete plugin installations."""

    def plan_consolidation(self, scan_result: ComprehensiveScanResult) -> ConsolidationPlan
    def execute_consolidation(self, plan: ConsolidationPlan, dry_run: bool = True) -> Result
    def update_all_references(self, moves: List[MoveOperation]) -> None

    def create_installation_plan(self, installation: PluginInstallation) -> InstallationMoveplan:
        """
        Create a plan to move an entire plugin installation:
        1. Move plugin files to Plugins\VST2, VST3, etc.
        2. Move standalone to Plugins\{Vendor}\{Plugin}\
        3. Move data folders to Libraries\{Plugin}\
        4. Create registry update list
        5. Verify all paths are valid
        """
        pass
```

**`relationship_manager.py`** (NEW)
```python
class RelationshipManager:
    """Manages relationships between moved components."""

    def track_move_relationships(self, move_ops: List[MoveOperation]) -> RelationshipMap
    def update_internal_paths(self, installation: PluginInstallation, new_paths: Dict[str, Path]) -> None
    def verify_relationships_intact(self, installation: PluginInstallation) -> ValidationResult

    # Examples of what needs updating:
    # 1. Plugin config files that point to preset folders
    # 2. Application settings that reference plugin paths
    # 3. Symbolic links
    # 4. INI/XML/JSON config files
```

**`registry_path_updater.py`** (NEW)
```python
class RegistryPathUpdater:
    """Updates registry paths after file moves."""

    def create_registry_update_plan(self, move_ops: List[MoveOperation]) -> RegistryUpdatePlan
    def execute_registry_updates(self, plan: RegistryUpdatePlan) -> UpdateResult
    def verify_registry_updates(self, updates: List[RegistryUpdate]) -> ValidationResult

    def batch_update_registry(self, updates: List[RegistryUpdate]) -> BatchResult:
        """
        Update multiple registry entries atomically:
        1. Backup all affected keys
        2. Update all paths
        3. Verify each update
        4. Rollback all if any fail
        """
        pass
```

#### Organization Workflow:

```
1. Scan Results Analysis
   ├─> Identify complete installations
   ├─> Group related components
   └─> Detect dependencies

2. Plan Generation
   ├─> Create target structure
   ├─> Map each component to new location
   ├─> Calculate total size and time
   ├─> Identify potential conflicts
   └─> Generate move operations list

3. Validation
   ├─> Verify sufficient disk space
   ├─> Check write permissions
   ├─> Validate target paths
   └─> Confirm no conflicts

4. Backup Creation
   ├─> Backup registry keys
   ├─> Create file manifest
   └─> Record current state

5. Execution (Per Installation)
   ├─> Move plugin files
   ├─> Move applications
   ├─> Move data folders
   ├─> Update registry paths
   ├─> Update internal configs
   └─> Verify each step

6. Verification
   ├─> Verify all files moved
   ├─> Verify registry updated
   ├─> Test plugin loadability
   ├─> Verify folder sizes match
   └─> Check relationships intact

7. Cleanup
   ├─> Remove empty folders
   ├─> Clean orphaned registry entries
   └─> Update scan database

8. Report Generation
   ├─> List successful moves
   ├─> List failed moves
   ├─> Generate before/after comparison
   └─> Create rollback instructions
```

#### Example Organization Plan:

For "Serum" complete installation:

```
Source Locations:
├─ Plugin Files:
│  ├─ C:\Program Files\Common Files\VST3\Serum.vst3 (45 MB)
│  └─ C:\Program Files\VstPlugins\Serum_x64.dll (32 MB)
├─ Installation:
│  └─ C:\Program Files\Xfer\Serum\ (250 MB)
│     ├─ Serum.exe
│     ├─ Resources\
│     └─ uninstall.exe
├─ Data Folders:
│  ├─ C:\Users\{USER}\Documents\Xfer\Serum\Presets\ (145 MB)
│  ├─ C:\Users\{USER}\Documents\Xfer\Serum\Wavetables\ (89 MB)
│  └─ C:\Users\{USER}\Documents\Xfer\Serum\Skins\ (3 MB)
└─ License:
   └─ C:\ProgramData\Xfer\Serum\Serum.lic (2 KB)

Target Locations:
├─ Plugin Files:
│  ├─ C:\MusicProduction\Plugins\VST3\Serum.vst3
│  └─ C:\MusicProduction\Plugins\VST2\Xfer\Serum_x64.dll
├─ Installation:
│  └─ C:\MusicProduction\Plugins\Xfer\Serum\
│     ├─ Serum.exe
│     ├─ Resources\
│     └─ uninstall.exe
├─ Data:
│  └─ C:\MusicProduction\Libraries\Serum\
│     ├─ Presets\
│     ├─ Wavetables\
│     └─ Skins\
└─ License:
   └─ C:\MusicProduction\Licenses\Serum\Serum.lic

Registry Updates:
├─ HKLM\SOFTWARE\Xfer\Serum\InstallPath:
│  Old: "C:\Program Files\Xfer\Serum"
│  New: "C:\MusicProduction\Plugins\Xfer\Serum"
├─ HKCU\Software\Xfer\Serum\PresetsPath:
│  Old: "C:\Users\{USER}\Documents\Xfer\Serum\Presets"
│  New: "C:\MusicProduction\Libraries\Serum\Presets"
└─ HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Serum\InstallLocation:
   Old: "C:\Program Files\Xfer\Serum"
   New: "C:\MusicProduction\Plugins\Xfer\Serum"

Operation Summary:
├─ Files to move: 3,594
├─ Total size: 564 MB
├─ Estimated time: 2 minutes
├─ Registry updates: 3
└─ Risk level: Low (all components found, license valid)
```

---

## 3. Data Models

### 3.1 Plugin Model

```python
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional
from datetime import datetime

class PluginType(Enum):
    VST2 = "VST2"
    VST3 = "VST3"
    AAX = "AAX"
    CLAP = "CLAP"
    AU = "AU"
    UNKNOWN = "UNKNOWN"

class PluginCategory(Enum):
    INDIVIDUAL = "Individual"
    WAVES = "Waves"
    IZOTOPE = "iZotope"
    FABFILTER = "FabFilter"
    NATIVE_INSTRUMENTS = "Native Instruments"
    ARTURIA = "Arturia"
    PLUGIN_ALLIANCE = "Plugin Alliance"
    OTHER = "Other"

@dataclass
class Version:
    major: int
    minor: int
    patch: int
    build: Optional[int] = None

    def __str__(self) -> str:
        if self.build:
            return f"{self.major}.{self.minor}.{self.patch}.{self.build}"
        return f"{self.major}.{self.minor}.{self.patch}"

    def __gt__(self, other: 'Version') -> bool:
        return (self.major, self.minor, self.patch, self.build or 0) > \
               (other.major, other.minor, other.patch, other.build or 0)

@dataclass
class Plugin:
    """Core plugin data model."""

    # Identification
    name: str
    publisher: str
    plugin_id: Optional[str]

    # Classification
    plugin_type: PluginType
    category: PluginCategory

    # Version
    version: Version

    # Paths
    file_path: Path
    install_date: Optional[datetime]

    # Registry
    registry_key: Optional[str]

    # License
    license_status: str  # "Verified", "Pending", "Missing", "Expired"
    license_path: Optional[Path]

    # Metadata
    file_size: int
    file_hash: str
    architecture: str  # "x64", "x86", "ARM"

    # Additional Info
    description: Optional[str] = None
    website: Optional[str] = None
    support_url: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for CSV/JSON export."""
        return {
            'name': self.name,
            'publisher': self.publisher,
            'type': self.plugin_type.value,
            'category': self.category.value,
            'version': str(self.version),
            'file_path': str(self.file_path),
            'registry_key': self.registry_key,
            'license_status': self.license_status,
            'architecture': self.architecture,
            'file_size_mb': round(self.file_size / (1024 * 1024), 2)
        }
```

### 3.2 DAW Model

```python
@dataclass
class DAW:
    """Digital Audio Workstation data model."""

    name: str  # "FL Studio", "Ableton Live"
    version: Version
    install_path: Path
    plugin_paths: List[Path]
    preset_paths: List[Path]
    project_paths: List[Path]
    registry_key: str
    executable: Path

    def scan_for_plugins(self) -> List[Path]:
        """Get all plugin scan paths for this DAW."""
        pass

    def verify_can_load(self) -> bool:
        """Test if DAW can launch successfully."""
        pass
```

### 3.3 License Model

```python
class LicenseType(Enum):
    FILE = "File"  # .lic, .key
    ILOK = "iLok"
    REGISTRY = "Registry"
    SERIAL = "Serial Number"
    SUBSCRIPTION = "Subscription"
    NFR = "NFR"  # Not For Resale
    DEMO = "Demo"

@dataclass
class License:
    """License information model."""

    plugin_name: str
    license_type: LicenseType
    status: str  # "Active", "Expired", "Invalid"

    # File-based
    file_path: Optional[Path] = None

    # Serial-based
    serial_number: Optional[str] = None

    # iLok
    ilok_id: Optional[str] = None
    ilok_location: Optional[str] = None  # "Cloud", "USB", "Computer"

    # Expiration
    expiration_date: Optional[datetime] = None
    activation_date: Optional[datetime] = None

    # Metadata
    machine_id: Optional[str] = None
    activation_count: Optional[int] = None
    max_activations: Optional[int] = None
```

### 3.4 Application Model (NEW)

```python
class ApplicationType(Enum):
    PLUGIN_MANAGER = "Plugin Manager"
    STANDALONE = "Standalone Plugin"
    DAW = "DAW"
    UTILITY = "Utility"
    INSTALLER = "Installer"

@dataclass
class Application:
    """Application/Executable data model."""

    # Identification
    name: str
    publisher: str
    app_type: ApplicationType

    # Version
    version: Version

    # Paths
    executable_path: Path
    install_path: Path

    # Registry
    registry_key: Optional[str]
    uninstall_key: Optional[str]

    # Relationships
    related_plugins: List[str]  # Plugin names managed by this app
    related_folders: List[Path]  # Data/config folders

    # Metadata
    file_size: int
    install_date: Optional[datetime]
    description: Optional[str]

    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'publisher': self.publisher,
            'type': self.app_type.value,
            'version': str(self.version),
            'executable': str(self.executable_path),
            'install_path': str(self.install_path),
            'related_plugins': ', '.join(self.related_plugins),
        }
```

### 3.5 Folder Models (NEW)

```python
class FolderType(Enum):
    PLUGIN_INSTALLATION = "Plugin Installation"
    PRESETS = "Presets"
    SAMPLES = "Samples"
    USER_DATA = "User Data"
    FACTORY_DATA = "Factory Data"
    CONFIGURATION = "Configuration"
    CACHE = "Cache"
    DOCUMENTATION = "Documentation"
    UNKNOWN = "Unknown"

@dataclass
class DataFolder:
    """Data folder data model."""

    # Identification
    path: Path
    folder_type: FolderType
    owner: Optional[str]  # Plugin/App that owns this folder

    # Contents
    file_count: int
    total_size: int
    file_types: Dict[str, int]  # Extension -> count

    # Metadata
    created_date: Optional[datetime]
    modified_date: Optional[datetime]

    # Relationships
    parent_plugin: Optional[str]
    parent_application: Optional[str]

    def to_dict(self) -> dict:
        return {
            'path': str(self.path),
            'type': self.folder_type.value,
            'owner': self.owner,
            'file_count': self.file_count,
            'size_mb': round(self.total_size / (1024 * 1024), 2),
            'parent': self.parent_plugin or self.parent_application,
        }

@dataclass
class PluginInstallation:
    """Complete plugin installation including all components."""

    # Plugin info
    plugin_name: str
    publisher: str

    # Components
    plugin_files: List[Path]  # VST2/VST3/AAX files
    executables: List[Path]  # Standalone versions
    data_folders: List[DataFolder]  # Presets, samples, etc.

    # Installation
    install_root: Path
    total_size: int

    # Registry
    registry_keys: List[str]

    def get_all_paths(self) -> List[Path]:
        """Get all file/folder paths for this installation."""
        paths = []
        paths.extend(self.plugin_files)
        paths.extend(self.executables)
        paths.extend([f.path for f in self.data_folders])
        return paths
```

### 3.6 Registry Entry Model (NEW)

```python
@dataclass
class RegistryEntry:
    """Registry entry data model."""

    # Key info
    key_path: str  # Full registry path
    value_name: str
    value_data: str
    value_type: str  # REG_SZ, REG_DWORD, etc.

    # Relationships
    related_file: Optional[Path]
    related_plugin: Optional[str]
    related_application: Optional[str]

    # Metadata
    hive: str  # HKLM, HKCU, etc.
    category: str  # "VST Path", "Install Location", "License", etc.

    def to_dict(self) -> dict:
        return {
            'key': self.key_path,
            'value_name': self.value_name,
            'data': self.value_data,
            'type': self.value_type,
            'category': self.category,
            'related_to': self.related_plugin or self.related_application,
        }
```

### 3.7 Comprehensive Scan Result Model

```python
@dataclass
class ComprehensiveScanResult:
    """Complete scan result containing ALL discovered items."""

    scan_id: str
    scan_date: datetime
    scan_duration: float  # seconds

    # Discovered items
    plugins: List[Plugin]
    applications: List[Application]
    data_folders: List[DataFolder]
    plugin_installations: List[PluginInstallation]
    daws: List[DAW]
    licenses: List[License]
    registry_entries: List[RegistryEntry]

    # Statistics
    total_files_scanned: int
    total_plugins_found: int
    total_applications_found: int
    total_folders_found: int
    total_size_gb: float
    total_registry_entries: int

    # Issues
    broken_links: List[Path]
    missing_licenses: List[str]
    registry_mismatches: List[dict]
    orphaned_folders: List[Path]  # Folders with no associated plugin
    orphaned_registry: List[str]  # Registry entries pointing to non-existent files

    def to_dataframe(self) -> pd.DataFrame:
        """Convert to pandas DataFrame for export."""
        pass

    def export_csv(self, output_path: Path) -> None:
        """Export scan results to CSV."""
        pass

    def export_excel(self, output_path: Path) -> None:
        """Export comprehensive scan results to Excel with multiple sheets:
        - Plugins
        - Applications
        - Folders
        - Registry Entries
        - Installations (grouped by plugin)
        - Issues
        - Statistics
        """
        pass

    def generate_summary(self) -> str:
        """Generate human-readable summary."""
        summary = f"""
        Scan Summary (ID: {self.scan_id})
        ================================
        Scan Date: {self.scan_date}
        Duration: {self.scan_duration:.2f}s

        Components Found:
        - Plugins: {len(self.plugins)}
        - Applications: {len(self.applications)}
        - Data Folders: {len(self.data_folders)}
        - Complete Installations: {len(self.plugin_installations)}
        - Registry Entries: {len(self.registry_entries)}

        Total Size: {self.total_size_gb:.2f} GB

        Issues:
        - Broken Links: {len(self.broken_links)}
        - Missing Licenses: {len(self.missing_licenses)}
        - Registry Mismatches: {len(self.registry_mismatches)}
        - Orphaned Folders: {len(self.orphaned_folders)}
        """
        return summary
```

---

## 4. Core Utilities

### 4.1 File Operations (`utils/file_operations.py`)

```python
class SafeFileOperations:
    """Thread-safe file operations with backup."""

    @staticmethod
    def safe_copy(source: Path, dest: Path, backup: bool = True) -> bool:
        """Copy file with automatic backup."""
        pass

    @staticmethod
    def safe_move(source: Path, dest: Path, backup: bool = True) -> bool:
        """Move file with automatic backup."""
        pass

    @staticmethod
    def calculate_hash(file_path: Path, algorithm: str = 'sha256') -> str:
        """Calculate file hash for verification."""
        pass

    @staticmethod
    def atomic_write(file_path: Path, content: str) -> bool:
        """Write file atomically (temp + rename)."""
        pass
```

### 4.2 Validators (`utils/validators.py`)

```python
class Validators:
    """Input and data validation."""

    @staticmethod
    def validate_path(path: str) -> Path:
        """Validate and normalize path."""
        pass

    @staticmethod
    def validate_plugin_file(file_path: Path) -> bool:
        """Verify file is a valid plugin."""
        pass

    @staticmethod
    def validate_version_string(version: str) -> Version:
        """Parse and validate version string."""
        pass

    @staticmethod
    def validate_registry_key(key: str) -> bool:
        """Validate registry key format."""
        pass
```

### 4.3 Logger (`core/logger.py`)

```python
class MPSMLogger:
    """Custom logging system with rotation and levels."""

    def __init__(self, log_dir: Path, level: str = "INFO"):
        self.log_dir = log_dir
        self.setup_logging()

    def setup_logging(self) -> None:
        """Configure logging with rotation."""
        pass

    def log_operation(self, operation: str, details: dict) -> None:
        """Log operation with structured data."""
        pass

    def log_error(self, error: Exception, context: dict) -> None:
        """Log error with context."""
        pass

    def export_logs(self, start_date: datetime, end_date: datetime) -> Path:
        """Export logs for time period."""
        pass
```

---

## 5. Configuration Management

### 5.1 Configuration Schema (`config.yaml`)

```yaml
# MPSM Configuration File
version: "1.0"

# Root directory for music production files
root_path: "C:\\MusicProduction"

# Custom paths (relative to root_path)
custom_paths:
  vst2: "Plugins\\VST2"
  vst3: "Plugins\\VST3"
  aax: "Plugins\\AAX"
  clap: "Plugins\\CLAP"
  daw_fl: "DAWs\\FLStudio"
  daw_ableton: "DAWs\\Ableton"
  libraries: "Libraries"
  licenses: "Licenses"
  temp: "Temp"

# Scan configuration
scan:
  # Directories to scan
  scan_paths:
    - "C:\\"

  # Directories to exclude
  exclude_paths:
    - "C:\\Windows"
    - "C:\\Windows\\System32"
    - "C:\\Windows\\WinSxS"
    - "C:\\ProgramData\\Microsoft\\OneDrive"
    - "C:\\$Recycle.Bin"

  # Component types to scan
  components:
    plugin_files: true         # VST2, VST3, AAX files
    applications: true         # Executables and plugin managers
    folders: true              # Installation and data folders
    registry: true             # Registry entries

  # File extensions to scan
  extensions:
    plugins:
      vst2: [".dll"]
      vst3: [".vst3"]
      aax: [".aax"]
      clap: [".clap"]
    executables: [".exe"]
    documents: [".pdf", ".txt", ".rtf"]
    licenses: [".lic", ".key", ".license"]

  # Folder detection
  folder_patterns:
    # Installation folders
    installation:
      - "**/Program Files/**"
      - "**/Program Files (x86)/**"
      - "**/VSTPlugins/**"
      - "**/Steinberg/**"

    # Data folders
    presets:
      - "**/Presets/**"
      - "**/User Presets/**"
      - "**/.vstpreset"
    samples:
      - "**/Samples/**"
      - "**/Libraries/**"
      - "**/Content/**"
    user_data:
      - "**/Documents/**/**/Presets/**"
      - "**/AppData/**/**/Presets/**"

  # Application detection
  known_applications:
    plugin_managers:
      - "Waves Central"
      - "Native Access"
      - "iLok License Manager"
      - "Plugin Alliance"
      - "Arturia Software Center"
      - "Splice"
      - "Output Hub"
      - "Roland Cloud Manager"
      - "Komplete Kontrol"

    daws:
      - "FL Studio"
      - "Ableton Live"
      - "Cubase"
      - "Studio One"
      - "Logic Pro"
      - "Reaper"

  # Registry scan
  registry_scan:
    enabled: true
    depth: "deep"  # "quick" or "deep"

    # Specific keys to scan
    target_keys:
      - "HKLM\\SOFTWARE\\VST"
      - "HKLM\\SOFTWARE\\VST3"
      - "HKCU\\Software\\VST"
      - "HKCU\\Software\\Image-Line"
      - "HKCU\\Software\\Ableton"
      - "HKLM\\SOFTWARE\\Waves"
      - "HKLM\\SOFTWARE\\iZotope"
      - "HKLM\\SOFTWARE\\Native Instruments"
      - "HKLM\\SOFTWARE\\Arturia"
      - "HKLM\\SOFTWARE\\FabFilter"
      - "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall"

    # Detect orphaned registry entries
    detect_orphans: true

  # Performance
  parallel: true
  max_workers: 4

  # Limits (prevent excessive scanning)
  max_folder_depth: 10
  max_file_size_mb: 5000
  skip_cache_folders: true

# DAW configuration
daws:
  enabled:
    - "FLStudio"
    - "AbletonLive"

  fl_studio:
    exe_path: "C:\\Program Files\\Image-Line\\FL Studio 21\\FL64.exe"
    plugin_db: "C:\\Users\\{USER}\\Documents\\Image-Line\\FL Studio\\Settings\\Plugin database.xml"

  ableton:
    exe_path: "C:\\ProgramData\\Ableton\\Live 12\\Program\\Ableton Live.exe"

# Update configuration
updates:
  enabled: true
  auto_update: false  # Require confirmation
  check_frequency: "daily"
  check_time: "02:00"

  # Vendors to check
  vendors:
    - "Waves"
    - "iZotope"
    - "FabFilter"
    - "Native Instruments"
    - "Arturia"
    - "Plugin Alliance"

# License configuration
licenses:
  centralize: true
  verify_on_scan: true
  backup_licenses: true

  ilok:
    enabled: true
    check_cloud: true

# Registry configuration
registry:
  backup_enabled: true
  backup_retention_days: 30
  verify_after_update: true

  # Registry keys to monitor
  keys:
    - "HKEY_LOCAL_MACHINE\\SOFTWARE\\VST"
    - "HKEY_CURRENT_USER\\Software\\Image-Line\\FL Studio"
    - "HKEY_CURRENT_USER\\Software\\Ableton"

# Safety configuration
safety:
  dry_run: true  # Default to dry-run mode
  backup_before_move: true
  verify_after_move: true
  rollback_on_error: true
  max_file_size_mb: 5000  # Warn if file larger than this

# Logging configuration
logging:
  level: "INFO"  # DEBUG, INFO, WARNING, ERROR
  max_log_size_mb: 100
  log_retention_days: 90
  log_to_console: true
  log_to_file: true

# Export configuration
export:
  formats: ["csv", "xlsx"]
  include_metadata: true
  compress_exports: false

# Performance configuration
performance:
  cache_enabled: true
  cache_ttl_hours: 24
  database_type: "sqlite"  # sqlite, json
  optimize_scans: true
```

### 5.2 Config Manager (`core/config.py`)

```python
class ConfigManager:
    """Manages application configuration."""

    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.config = self.load_config()

    def load_config(self) -> dict:
        """Load configuration from YAML."""
        pass

    def save_config(self, config: dict) -> None:
        """Save configuration to YAML."""
        pass

    def get(self, key_path: str, default=None):
        """Get config value by dot notation (e.g., 'scan.parallel')."""
        pass

    def set(self, key_path: str, value) -> None:
        """Set config value by dot notation."""
        pass

    def validate_config(self) -> List[str]:
        """Validate configuration and return errors."""
        pass

    def create_default_config(self) -> None:
        """Create default configuration file."""
        pass
```

---

## 6. Error Handling & Safety

### 6.1 Custom Exceptions (`core/exceptions.py`)

```python
class MPSMException(Exception):
    """Base exception for MPSM."""
    pass

class ScanException(MPSMException):
    """Raised during scanning operations."""
    pass

class RegistryException(MPSMException):
    """Raised during registry operations."""
    pass

class FileOperationException(MPSMException):
    """Raised during file operations."""
    pass

class LicenseException(MPSMException):
    """Raised during license operations."""
    pass

class ConfigException(MPSMException):
    """Raised for configuration errors."""
    pass

class ValidationException(MPSMException):
    """Raised when validation fails."""
    pass

class RollbackException(MPSMException):
    """Raised when rollback fails."""
    pass
```

### 6.2 Safety Mechanisms

#### Dry-Run Mode
```python
class DryRunManager:
    """Manages dry-run operations."""

    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.operations = []

    def log_operation(self, operation: Operation) -> None:
        """Log operation without executing."""
        if self.enabled:
            self.operations.append(operation)
            logger.info(f"[DRY RUN] Would execute: {operation}")

    def execute_operation(self, operation: Operation) -> Result:
        """Execute or simulate based on dry-run mode."""
        if self.enabled:
            return self.simulate(operation)
        return self.execute(operation)

    def generate_report(self) -> str:
        """Generate report of operations that would be performed."""
        pass
```

#### Backup System
```python
class BackupManager:
    """Manages backups for rollback capability."""

    def create_backup(self, items: List[BackupItem]) -> BackupArchive:
        """Create backup of files/registry."""
        pass

    def restore_backup(self, backup_id: str) -> bool:
        """Restore from backup."""
        pass

    def verify_backup(self, backup_id: str) -> bool:
        """Verify backup integrity."""
        pass

    def cleanup_old_backups(self, retention_days: int) -> None:
        """Remove old backups."""
        pass
```

#### Transaction Manager
```python
class TransactionManager:
    """Manages atomic operations with rollback."""

    def begin_transaction(self) -> Transaction:
        """Start new transaction."""
        pass

    def commit(self, transaction: Transaction) -> bool:
        """Commit transaction."""
        pass

    def rollback(self, transaction: Transaction) -> bool:
        """Rollback transaction."""
        pass
```

---

## 7. Testing Strategy

### 7.1 Unit Tests

```python
# tests/test_scanner.py
class TestFileScanner:
    def test_scan_vst2_files(self):
        """Test VST2 file detection."""
        pass

    def test_exclude_system_paths(self):
        """Test path exclusion."""
        pass

    def test_metadata_extraction(self):
        """Test metadata extraction from DLL."""
        pass

# tests/test_registry.py
class TestRegistryManager:
    def test_backup_registry_key(self):
        """Test registry backup."""
        pass

    def test_update_registry_path(self):
        """Test registry path update."""
        pass

    def test_rollback_registry(self):
        """Test registry rollback."""
        pass
```

### 7.2 Integration Tests

```python
# tests/test_integration.py
class TestFullWorkflow:
    def test_scan_organize_workflow(self):
        """Test complete scan and organize workflow."""
        pass

    def test_update_workflow(self):
        """Test plugin update workflow."""
        pass

    def test_license_verification_workflow(self):
        """Test license verification workflow."""
        pass
```

### 7.3 Test Environment

```yaml
# tests/test_config.yaml
test_environment:
  mock_plugins:
    - name: "TestPlugin1"
      type: "VST3"
      path: "tests/fixtures/TestPlugin1.vst3"

  mock_registry:
    create_test_keys: true
    cleanup_after: true

  temp_directory: "tests/temp"
  fixtures_directory: "tests/fixtures"
```

---

## 8. Implementation Phases

### Phase 1: Foundation (Week 1-2)
**Goal**: Core infrastructure and basic scanning

- [ ] Project structure setup
- [ ] Configuration system
- [ ] Logging system
- [ ] Data models
- [ ] Basic file scanner
- [ ] Metadata extractor (VST2/VST3)
- [ ] CSV export functionality
- [ ] Unit tests for core components

**Deliverable**: Working scanner that can detect plugins and export to CSV

### Phase 2: Registry Management (Week 3)
**Goal**: Safe registry operations

- [ ] Registry reader
- [ ] Registry backup system
- [ ] Registry updater
- [ ] Path validator
- [ ] Transaction manager
- [ ] Rollback capability
- [ ] Integration tests

**Deliverable**: Registry manager with backup/restore capability

### Phase 3: Organization (Week 4)
**Goal**: File organization and consolidation

- [ ] Structure builder
- [ ] File mover with backup
- [ ] Consolidation planner
- [ ] Reference updater
- [ ] Dry-run mode
- [ ] Progress reporting

**Deliverable**: Working organizer that can relocate plugins safely

### Phase 4: License Tracking (Week 5)
**Goal**: License detection and verification

- [ ] License scanner
- [ ] iLok integration
- [ ] License validator
- [ ] Centralization system
- [ ] Status reporting
- [ ] Export to dashboard

**Deliverable**: License tracking and reporting system

### Phase 5: Update System (Week 6-7)
**Goal**: Automated update checking

- [ ] Version checker
- [ ] Vendor scrapers (start with top 3)
- [ ] Download manager
- [ ] Silent installer
- [ ] Update scheduler
- [ ] Notification system

**Deliverable**: Automated update system for major vendors

### Phase 6: Installation Control (Week 8)
**Goal**: Custom installation paths

- [ ] Path manager
- [ ] Symlink manager
- [ ] Silent installer integration
- [ ] Installation monitoring
- [ ] Path enforcement

**Deliverable**: Custom installation path system

### Phase 7: Polish & Testing (Week 9-10)
**Goal**: Production-ready application

- [ ] Comprehensive testing
- [ ] Performance optimization
- [ ] Error handling improvements
- [ ] Documentation
- [ ] User guide
- [ ] Packaging (PyInstaller)
- [ ] Installation script

**Deliverable**: Production-ready MPSM application

---

## 9. Technical Specifications

### 9.1 Performance Requirements

| Operation | Target Time | Max Time |
|-----------|-------------|----------|
| Full system scan | < 5 min | 10 min |
| Registry backup | < 30 sec | 1 min |
| Plugin move (single) | < 5 sec | 10 sec |
| Registry update | < 10 sec | 30 sec |
| License scan | < 2 min | 5 min |
| Update check (all) | < 3 min | 10 min |

### 9.2 Resource Limits

- **Memory**: Max 500MB during scan
- **Disk I/O**: Max 100MB/s read
- **CPU**: Max 50% utilization (parallel operations)
- **Network**: Max 10MB/s download

### 9.3 Compatibility

- **OS**: Windows 11 (primary), Windows 10 (tested)
- **Python**: 3.9+
- **Architecture**: x64 (primary), x86 (supported)
- **Privileges**: User-level (admin for registry operations)

### 9.4 Security Considerations

1. **Registry Operations**: Always backup before modification
2. **File Operations**: Validate paths to prevent traversal attacks
3. **Downloads**: Verify checksums of downloaded installers
4. **Credentials**: Never store license keys in plain text
5. **Logging**: Sanitize sensitive data from logs

### 9.5 Dependencies

```txt
# Core
pandas>=2.0.0
pyyaml>=6.0
requests>=2.31.0
beautifulsoup4>=4.12.0
lxml>=4.9.0

# File operations
pefile>=2023.2.7
python-magic-bin>=0.4.14  # Windows file type detection

# Scheduling
schedule>=1.2.0
apscheduler>=3.10.0

# CLI
click>=8.1.0
rich>=13.0.0  # Better terminal output
tqdm>=4.66.0

# Validation
pydantic>=2.0.0
jsonschema>=4.19.0

# Security
cryptography>=41.0.0

# Database
sqlalchemy>=2.0.0  # If using database

# Testing
pytest>=7.4.0
pytest-cov>=4.1.0
pytest-mock>=3.11.0

# Development
black>=23.7.0
mypy>=1.5.0
pylint>=2.17.0
```

---

## 10. CLI Interface Specification

### 10.1 Command Structure

```bash
# Initialize MPSM
mpsm init [--path PATH] [--config CONFIG]

# Scanning
mpsm scan [--full] [--quick] [--export FORMAT]
mpsm scan --rescan  # Re-scan specific plugin

# Organization
mpsm organize [--dry-run] [--approve] [--plugin PLUGIN]
mpsm organize --plan  # Show what would be done

# Registry
mpsm registry backup [--keys KEYS]
mpsm registry restore [--backup-id ID]
mpsm registry verify  # Verify all plugin paths

# Updates
mpsm update check [--plugin PLUGIN] [--vendor VENDOR]
mpsm update install [--plugin PLUGIN] [--all]
mpsm update schedule [--time TIME]

# Licenses
mpsm license scan
mpsm license verify [--plugin PLUGIN]
mpsm license centralize
mpsm license report

# Installation
mpsm install --plugin PLUGIN --type TYPE [--path PATH]
mpsm install --setup-symlinks

# Utilities
mpsm export [--format FORMAT] [--output PATH]
mpsm backup create [--type TYPE]
mpsm backup list
mpsm backup restore --id ID
mpsm config show
mpsm config set KEY VALUE
mpsm status  # Show system status
mpsm doctor  # Diagnose issues

# Complete workflow
mpsm run-all [--dry-run]
```

### 10.2 Output Formatting

```python
# Using Rich library for better output
from rich.console import Console
from rich.table import Table
from rich.progress import Progress

console = Console()

# Status display
console.print("[bold green]Scan completed successfully![/bold green]")
console.print(f"Found {count} plugins")

# Table output
table = Table(title="Scan Results")
table.add_column("Name", style="cyan")
table.add_column("Publisher", style="magenta")
table.add_column("Type", style="green")
table.add_column("Status", style="yellow")

# Progress bars
with Progress() as progress:
    task = progress.add_task("[cyan]Scanning...", total=total_files)
    # ... scanning logic
    progress.update(task, advance=1)
```

---

## Next Steps

1. **Review this framework** with stakeholders
2. **Set up development environment**
3. **Begin Phase 1 implementation** (Core + Scanner)
4. **Create test fixtures** for unit testing
5. **Establish CI/CD pipeline** for automated testing

---

**Framework Version**: 1.0
**Last Updated**: 2025-11-09
**Status**: Ready for Implementation
