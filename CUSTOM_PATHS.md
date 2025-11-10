# Custom Plugin Paths Configuration

## Quick Start

1. Open the `.env` file in the root directory
2. Uncomment and edit paths to your custom plugin locations
3. Run `python mpsm.py scan` - your custom paths will be scanned automatically

## Example

```bash
# Your .env file:
CUSTOM_VST2_PATH_1=C:\Production\Library\VST2
CUSTOM_VST2_PATH_2=D:\Audio\VST2
CUSTOM_VST3_PATH_1=C:\Production\Library\VST3
```

When you run a scan, MPSM will scan:
- All default paths from `config.yaml`
- **Plus** all custom paths from `.env`

## Why Use .env?

- **Easy to edit** - No YAML syntax to worry about
- **Personal** - `.env` is gitignored, your paths stay private
- **Safe** - Can't break config.yaml by mistake
- **Flexible** - Add unlimited paths with incrementing numbers

## Supported Path Variables

| Variable Pattern | Description | Example |
|------------------|-------------|---------|
| `CUSTOM_VST2_PATH_*` | VST2 plugin directories | `CUSTOM_VST2_PATH_1=C:\VST2` |
| `CUSTOM_VST3_PATH_*` | VST3 plugin directories | `CUSTOM_VST3_PATH_1=C:\VST3` |
| `CUSTOM_AAX_PATH_*` | AAX plugin directories | `CUSTOM_AAX_PATH_1=C:\AAX` |
| `CUSTOM_CLAP_PATH_*` | CLAP plugin directories | `CUSTOM_CLAP_PATH_1=C:\CLAP` |
| `CUSTOM_PLUGIN_PATH_*` | General (all types) | `CUSTOM_PLUGIN_PATH_1=C:\Plugins` |

## Adding Multiple Paths

Just increment the number:

```bash
CUSTOM_VST2_PATH_1=C:\Production\Library\VST2
CUSTOM_VST2_PATH_2=D:\Audio\VST2
CUSTOM_VST2_PATH_3=E:\Plugins\VST2
CUSTOM_VST2_PATH_4=F:\More Plugins\VST2
# ... add as many as you need
```

## Default Paths

MPSM still scans all default paths from `config.yaml`:
- `C:\Program Files\VSTPlugins`
- `C:\Program Files\Common Files\VST3`
- `C:\Program Files\Common Files\Avid\Audio`
- And many more vendor directories

Custom paths are **added** to these defaults, not replaced.

## Troubleshooting

### My paths aren't being scanned

1. Check the path uses backslashes: `C:\Folder\Subfolder`
2. Make sure the line is uncommented (no `#` at the start)
3. Variable must match pattern: `CUSTOM_*_PATH_*`

### Can I use forward slashes?

Either works:
- `C:\Production\VST2` ✅
- `C:/Production/VST2` ✅

### Do I need to create .env?

No! It already exists with your current path:
- `C:\Production\Library\VST2`

Just edit it to add more paths if needed.

---

**Created**: 2025-11-10
