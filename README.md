# Music Production Software Manager (MPSM)  
### Comprehensive Automation Plan for Windows 11 (Zephyrus G14)

> **Goal**: Fully automate scanning, organizing, relocating, updating, and managing 450+ VST plugins, DAWs (FL Studio, Ableton), plugin managers, and licenses — with zero clutter and full registry control.

---

## Overview

**MPSM** is a **Python-based CLI tool** that:
- Scans the entire drive for music production files.
- Centralizes everything into a clean, logical folder structure.
- Automatically fixes broken registry paths after moving files.
- Detects and applies plugin updates.
- Tracks and verifies licenses.
- Enforces custom installation paths for new plugins.

**Target User**: You — on a **Windows 11 ASUS ROG Zephyrus G14** used **exclusively for music production**.

---

## Target Folder Structure (Enforced)

```
C:\MusicProduction\                  # Configurable root
├── DAWs\
│   ├── FLStudio\
│   │   ├── InstallDir\
│   │   ├── Plugins\
│   │   └── Presets\
│   └── Ableton\
│       ├── InstallDir\
│       ├── Packs\
│       └── Plugins\
├── Plugins\
│   ├── VST2\                    # .dll files
│   │   ├── Waves\
│   │   ├── iZotope\
│   │   └── Individual\
│   ├── VST3\                    # .vst3 bundles
│   ├── AAX\                     # Pro Tools
│   └── Managers\                # Waves Central, etc.
├── Libraries\                   # Samples, PDFs, manuals
├── Licenses\                    # .lic, .key, iLok data
└── Temp\                        # Downloads, installers
```

---

## MPSM Tool Structure

```
C:\MPSM\
├── mpsm.py                      # Main CLI script
├── config.yaml                  # User settings
├── backups\                     # Registry + file backups
├── logs\                        # Scan/update logs
├── data\                        # Exported tables (CSV/Excel)
└── requirements.txt
```

---

## Core Features & Implementation

| Feature | Module | Key Functions | Output |
|--------|--------|---------------|--------|
| **1. System Scanner** | `scanner.py` | `scan_files()`, `extract_metadata()`, `query_registry()` | CSV table: Name, Publisher, Format, Location, Registry, License |
| **2. Registry Updater** | `registry_manager.py` | `backup_registry()`, `update_paths()` | Auto-fixes broken DAW/plugin paths |
| **3. Version Control** | `updater.py` | `check_updates()`, `download_update()` | Auto-fetch latest plugin versions |
| **4. License Tracker** | `license_tracker.py` | `verify_status()`, `centralize_licenses()` | License status in scan table |
| **5. Custom Installer** | `installer.py` | `set_custom_paths()`, `intercept_installer()` | New plugins install to correct folder |

---

## 1. System Scanner

```text
Scans: C:\ (excludes Windows, System32, OneDrive sync)
Detects:
- .dll → VST2
- .vst3 → VST3 bundle
- FL Studio / Ableton folders
- Plugin managers
- PDFs, uninstallers, startup junk
```

**Table Columns**:
| Name | Publisher | Type | Format | License | File Path | Registry Path |
|------|-----------|------|--------|---------|-----------|---------------|
| Serum | Xfer Records | Individual | VST3 | Verified | `C:\Program Files\Common Files\VST3\Serum.vst3` | `HKCU\Software\VST\Serum` |

Export: `data/scan_results.csv` or `.xlsx`

---

## 2. Registry Updater

**Problem**: Moving a `.dll` breaks DAW scanning.  
**Solution**: Auto-update registry entries.

```text
Actions:
- Backup registry key → .reg file
- Find all path references
- Replace old path → new path
- Test DAW load (optional)
- Rollback on failure
```

**Common Keys**:
```reg
HKEY_LOCAL_MACHINE\SOFTWARE\VST
HKEY_CURRENT_USER\Software\Image-Line\FL Studio\Locations
HKEY_CURRENT_USER\Software\Ableton
```

---

## 3. Version Control & Auto-Update

```text
For each plugin:
→ Scrape vendor site (Waves, iZotope, etc.)
→ Compare current vs latest version
→ Download installer
→ Run silent install (/S, /quiet)
→ Re-scan & verify
```

**Scheduled**: Daily at 2 AM via Windows Task Scheduler

---

## 4. License Tracking

```text
Detects:
- .lic, .key, .iLok files
- PACE/iLok activation status (via CLI tools)
- Serial numbers in registry
```

**Status**:
- Verified (Green)
- Pending (Yellow)
- Expired/Missing (Red)

Centralized in `C:\MusicProduction\Licenses\`

---

## 5. Custom Installation Paths

```text
Before installing new plugin:
→ Create symbolic links:
    mklink /J "C:\Program Files\Common Files\VST3" "C:\MusicProduction\Plugins\VST3"
→ Set environment variables
→ Run installer with pre-defined paths
```

**CLI Command**:
```bash
python mpsm.py install --plugin "Serum" --path "C:\MusicProduction\Plugins\VST3"
```

---

## Configuration (`config.yaml`)

```yaml
root_path: C:\MusicProduction
custom_paths:
  vst2: Plugins\VST2
  vst3: Plugins\VST3
  daw_fl: DAWs\FLStudio
  daw_ableton: DAWs\Ableton
daws: [FLStudio, AbletonLive]
auto_update: true
auto_update_time: "02:00"
dry_run: true
backup_enabled: true
```

---

## CLI Commands

```bash
python mpsm.py init              # Setup config + folders
python mpsm.py scan              # Full system scan
python mpsm.py organize          # Move + fix registry
python mpsm.py update            # Check all plugin updates
python mpsm.py license-check     # Verify all licenses
python mpsm.py install --plugin "Ozone 11" --type vst3
python mpsm.py run-all           # Full cycle
```

---

## Safety & Testing

- **Dry-run mode** (default): Simulate all actions
- **Backups**: Registry + file copies before changes
- **Logging**: `logs/mpsm_YYYYMMDD.log`
- **Rollback**: Restore from backup if DAW fails to load

---

## Dependencies (`requirements.txt`)

```txt
pandas
pyyaml
requests
beautifulsoup4
pefile
schedule
tqdm
cryptography
```

Install with:
```bash
pip install -r requirements.txt
```

---

## Deployment

1. Save all files in `C:\MPSM\`
2. Run: `python mpsm.py init`
3. Review `scan_results.csv`
4. Run: `python mpsm.py organize --approve`
5. Schedule daily: `python mpsm.py run-all`

**Optional**: Package as `.exe` with PyInstaller

---

## Next Steps

1. **Start with Scanner module** (I can provide full code)
2. Test on **1 plugin** (e.g., free VST)
3. Expand to **top 10 vendors**
4. Automate full cleanup
