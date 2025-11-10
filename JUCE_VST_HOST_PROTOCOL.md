# JUCE VST Host Communication Protocol

This document describes the communication protocol between MPSM (Python) and the JUCE-based VST scanner application.

## Overview

**Architecture:**
```
MPSM (Python)  <--JSON over stdin/stdout-->  VSTScanner.exe (JUCE C++)
```

**Why JUCE?**
- JUCE is a professional audio application framework
- Handles VST loading safely with proper error handling
- Runs in separate process - crashes don't affect MPSM
- Supports VST2, VST3, AU, AAX formats
- Industry-standard for plugin hosting

## Communication Methods

### 1. Subprocess (Default) - stdin/stdout

MPSM spawns VSTScanner.exe as a subprocess and communicates via JSON lines.

**Advantages:**
- Simple, no network overhead
- Works offline
- Process isolation

**Flow:**
1. MPSM starts: `subprocess.Popen(["VSTScanner.exe"])`
2. MPSM sends JSON requests to stdin
3. JUCE app processes plugins and writes JSON responses to stdout
4. Line-based protocol (one JSON object per line)

### 2. HTTP REST API (Alternative)

VSTScanner runs as HTTP server, MPSM makes REST API calls.

**Advantages:**
- Can run as service
- Multiple clients can connect
- Better for batch operations

**Endpoint:**
```
POST http://localhost:8080/scan
```

### 3. Named Pipes (Future/Windows)

For high-performance Windows IPC.

---

## JSON Protocol Specification

### Request Format (MPSM → JUCE)

```json
{
  "command": "scan",
  "path": "C:/VST/MyPlugin.dll",
  "timeout": 5
}
```

**Fields:**
- `command` (string, required): Always "scan" for now
- `path` (string, required): Absolute path to plugin file
- `timeout` (integer, optional): Timeout in seconds (default: 5)

**Alternative commands (future):**
```json
{"command": "batch_scan", "paths": ["path1.dll", "path2.dll"]}
{"command": "health"}
{"command": "shutdown"}
```

---

### Response Format (JUCE → MPSM)

#### Success Response

```json
{
  "success": true,
  "data": {
    "plugin_id": "abcd",
    "plugin_id_hex": "61626364",
    "name": "SuperCompressor",
    "vendor": "AudioCo",
    "version": "1.2.3",
    "category": "Effect",
    "num_inputs": 2,
    "num_outputs": 2,
    "is_synth": false,
    "plugin_type": "VST2"
  }
}
```

#### Error Response

```json
{
  "success": false,
  "error": "Failed to load plugin: Invalid format",
  "error_code": "LOAD_FAILED"
}
```

---

## Response Data Fields

### Core Fields (Required)

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `plugin_id` | string | 4-char VST2 ID or VST3 UUID | `"abcd"` or `"12345678-1234-1234-1234-123456789abc"` |
| `plugin_id_hex` | string | Hex representation of ID | `"61626364"` |
| `name` | string | Plugin display name | `"SuperCompressor"` |
| `vendor` | string | Plugin manufacturer | `"AudioCo"` |
| `plugin_type` | string | Format type | `"VST2"`, `"VST3"`, `"AAX"` |

### Optional Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `version` | string | Plugin version | `"1.2.3"` |
| `category` | string | Plugin category | `"Effect"`, `"Synth"` |
| `num_inputs` | integer | Audio input channels | `2` |
| `num_outputs` | integer | Audio output channels | `2` |
| `is_synth` | boolean | Is instrument/synth | `false` |
| `num_programs` | integer | Number of presets | `128` |
| `num_parameters` | integer | Number of parameters | `24` |
| `latency` | integer | Latency in samples | `512` |
| `can_process_replacing` | boolean | Supports in-place processing | `true` |

---

## Error Codes

| Code | Description |
|------|-------------|
| `LOAD_FAILED` | Plugin DLL failed to load |
| `INVALID_FORMAT` | Not a valid VST plugin |
| `TIMEOUT` | Loading exceeded timeout |
| `FILE_NOT_FOUND` | Plugin file doesn't exist |
| `ARCHITECTURE_MISMATCH` | 32-bit plugin, 64-bit scanner (or vice versa) |
| `MISSING_DEPENDENCIES` | Plugin missing required DLLs |

---

## Example Exchange

**MPSM sends (stdin):**
```json
{"command": "scan", "path": "C:/VST/Serum.dll", "timeout": 5}
```

**JUCE responds (stdout):**
```json
{
  "success": true,
  "data": {
    "plugin_id": "XfsX",
    "plugin_id_hex": "58667358",
    "name": "Serum",
    "vendor": "Xfer Records",
    "version": "1.36",
    "category": "Synth",
    "num_inputs": 0,
    "num_outputs": 2,
    "is_synth": true,
    "plugin_type": "VST2",
    "num_programs": 512,
    "num_parameters": 256
  }
}
```

---

## Building the JUCE Application

### Requirements

- JUCE Framework 7.0+
- CMake 3.15+ or Projucer
- C++17 compiler
- VST2 SDK (optional, for VST2 support)

### Project Structure

```
VSTScanner/
├── CMakeLists.txt
├── Source/
│   ├── Main.cpp              # Entry point, subprocess loop
│   ├── PluginScanner.cpp     # Core scanning logic
│   ├── JSONProtocol.cpp      # JSON parsing/serialization
│   └── SafePluginLoader.cpp  # Sandboxed plugin loading
└── README.md
```

### Key JUCE Classes to Use

```cpp
#include <juce_audio_processors/juce_audio_processors.h>

// Load plugin
juce::OwnedArray<juce::PluginDescription> types;
juce::KnownPluginList pluginList;
juce::VSTPluginFormat vstFormat;

vstFormat.findAllTypesForFile(types, pluginPath);

// Extract metadata
for (auto* desc : types) {
    json["name"] = desc->name.toStdString();
    json["vendor"] = desc->manufacturerName.toStdString();
    json["plugin_id"] = String::toHexString(desc->uid);
    // ... etc
}
```

### Safety Features to Implement

1. **Process Timeout:** Kill plugin load after N seconds
2. **Exception Handling:** Catch all crashes/exceptions
3. **Sandboxing:** Use restricted security context
4. **Resource Limits:** Prevent memory/CPU abuse

---

## Testing

### Manual Testing

```bash
# Start scanner
./VSTScanner.exe

# Send test request (type manually or pipe)
{"command": "scan", "path": "C:/VST/TestPlugin.dll", "timeout": 5}

# Expect JSON response
{"success": true, "data": {...}}
```

### Automated Testing (Python)

```python
from src.scanner.external_vst_host import ExternalVSTHost

host = ExternalVSTHost(juce_host_path="VSTScanner.exe")
metadata = host.extract_metadata("C:/VST/TestPlugin.dll")

assert metadata['plugin_id'] == "abcd"
assert metadata['vendor'] == "Test Vendor"
```

---

## Performance Considerations

- **Startup Cost:** ~100ms per plugin load
- **Batch Processing:** Start process once, scan many plugins
- **Caching:** Cache results by (file_path, file_hash)
- **Parallelization:** Run multiple scanner instances for parallel scanning

### Recommended Usage

```python
# Good: Reuse process
with ExternalVSTHost() as host:
    for plugin in plugins:
        metadata = host.extract_metadata(plugin)

# Bad: Start/stop per plugin
for plugin in plugins:
    host = ExternalVSTHost()
    metadata = host.extract_metadata(plugin)  # Slow!
    host.stop()
```

---

## Security Considerations

1. **Path Validation:** Verify plugin paths before loading
2. **No Code Execution:** Don't eval/exec JSON responses
3. **Timeout All Operations:** Prevent infinite loops
4. **Isolate Process:** Run scanner with restricted permissions
5. **Validate JSON:** Use strict JSON parsing

---

## Future Enhancements

### Version 2 Features

- Batch scanning: Send array of paths, get array of results
- Preset extraction: Return all preset names
- Parameter info: Full parameter list with ranges
- Audio fingerprinting: Generate audio signature for each plugin
- GUI screenshot: Capture plugin UI for preview

### Example Batch Request

```json
{
  "command": "batch_scan",
  "paths": [
    "C:/VST/Plugin1.dll",
    "C:/VST/Plugin2.dll",
    "C:/VST/Plugin3.dll"
  ],
  "timeout": 10
}
```

### Example Batch Response

```json
{
  "success": true,
  "results": [
    {"path": "C:/VST/Plugin1.dll", "success": true, "data": {...}},
    {"path": "C:/VST/Plugin2.dll", "success": false, "error": "LOAD_FAILED"},
    {"path": "C:/VST/Plugin3.dll", "success": true, "data": {...}}
  ]
}
```

---

## References

- [JUCE Framework](https://juce.com/)
- [JUCE Audio Processors Tutorial](https://docs.juce.com/master/tutorial_audio_processor_graph.html)
- [VST Plugin Specification](https://steinbergmedia.github.io/vst3_dev_portal/)
- [JSON Lines Format](https://jsonlines.org/)

---

## Support

If you're building the JUCE scanner and need help:

1. Check JUCE forums: https://forum.juce.com/
2. See example JUCE plugin hosts in JUCE examples folder
3. Reference: VST3PluginFormat and VSTPluginFormat classes in JUCE

**Minimal Working Example:**
A complete working JUCE VST scanner example will be provided in the `tools/VSTScanner/` directory.
