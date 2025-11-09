# MPSM Quick Start Guide

Get started with MPSM in 5 minutes!

## Prerequisites

- Windows 11
- Python 3.8 or higher
- Administrator privileges (for registry operations)
- Git (for cloning the repository)

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/mpsm.git
cd mpsm
```

### 2. Create Virtual Environment (Recommended)

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Initialize MPSM

```bash
python mpsm.py init
```

This creates the necessary directories:
- `backups/` - Registry and file backups
- `logs/` - Operation logs
- `data/` - Scan results and exports

### 5. Review Configuration

Open `config.yaml` and customize:

```yaml
# Change the root path if needed
root_path: C:\MusicProduction

# Enable/disable dry-run mode
dry_run: true  # Set to false for actual operations
```

## First Scan

Run your first system scan:

```bash
python mpsm.py scan
```

This will:
- Scan your system for VST2, VST3, and AAX plugins
- Detect DAW installations (FL Studio, Ableton)
- Find license files
- Export results to `data/scan_results.csv`

## Understanding Dry-Run Mode

By default, MPSM runs in **dry-run mode** which means:
- All operations are simulated
- No files are moved
- No registry changes are made
- You can safely test without risk

To disable dry-run mode:
1. Edit `config.yaml`
2. Set `dry_run: false`
3. Run operations with the `--approve` flag

## Common Commands

```bash
# Scan system
python mpsm.py scan

# Organize files (dry-run)
python mpsm.py organize

# Organize files (actual)
python mpsm.py organize --approve

# Check for updates
python mpsm.py update

# Verify licenses
python mpsm.py license-check

# Full automation cycle
python mpsm.py run-all
```

## Next Steps

1. Review the scan results in `data/scan_results.csv`
2. Verify the proposed folder structure
3. Create a backup of your important data
4. Test organization with dry-run mode first
5. When ready, disable dry-run and run actual operations

## Getting Help

```bash
# View all commands
python mpsm.py --help

# Get help for specific command
python mpsm.py scan --help
```

## Safety Tips

1. **Always backup first** - MPSM creates automatic backups, but manual backups are recommended
2. **Test with dry-run** - Use dry-run mode before making actual changes
3. **Review logs** - Check `logs/` directory for operation details
4. **Start small** - Test with a few plugins before running full automation

## Troubleshooting

### "Module not found" errors
Make sure you've installed dependencies:
```bash
pip install -r requirements.txt
```

### Permission errors
Run Command Prompt or PowerShell as Administrator

### Config file not found
Run initialization first:
```bash
python mpsm.py init
```

## Support

For issues and questions:
- Check the [README.md](README.md)
- Review [COMPREHENSIVE_PLAN.md](COMPREHENSIVE_PLAN.md)
- Open an issue on GitHub

Happy organizing! 🎵
