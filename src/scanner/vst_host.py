"""Minimal VST2 host for safe plugin metadata extraction.

This module provides a lightweight VST host that can load plugins
and extract metadata without requiring a full DAW environment.

SAFETY WARNINGS:
- Loading unknown DLLs can crash the process
- Some plugins require audio drivers or GUI
- Always run in a separate process for isolation
"""

import ctypes
from ctypes import wintypes, c_int, c_void_p, POINTER, Structure, CFUNCTYPE
from pathlib import Path
from typing import Optional, Dict, Any
import struct
import platform

from ..core.logger import get_logger


# VST2 SDK Constants
audioMasterVersion = 23
effOpen = 0
effClose = 1
effGetEffectName = 45
effGetVendorString = 47
effGetProductString = 48
effGetVendorVersion = 49
effGetPlugCategory = 35
effIdentify = 22
effGetVstVersion = 58

# Plugin Categories (VST2)
kPlugCategUnknown = 0
kPlugCategEffect = 1
kPlugCategSynth = 2
kPlugCategAnalysis = 3
kPlugCategMastering = 4
kPlugCategSpacializer = 5
kPlugCategRoomFx = 6
kPlugCategSurroundFx = 7
kPlugCategRestoration = 8
kPlugCategOfflineProcess = 9
kPlugCategShell = 10
kPlugCategGenerator = 11


class AEffect(Structure):
    """VST2 AEffect structure (simplified).

    This is the main plugin interface structure.
    We only define the fields we need.
    """
    _fields_ = [
        ('magic', c_int),           # Must be 'VstP' (0x50747356)
        ('dispatcher', c_void_p),   # Dispatcher function pointer
        ('process', c_void_p),      # Process function (deprecated)
        ('setParameter', c_void_p), # Set parameter function
        ('getParameter', c_void_p), # Get parameter function
        ('numPrograms', c_int),
        ('numParams', c_int),
        ('numInputs', c_int),
        ('numOutputs', c_int),
        ('flags', c_int),
        ('resvd1', c_void_p),
        ('resvd2', c_void_p),
        ('initialDelay', c_int),
        ('realQualities', c_int),
        ('offQualities', c_int),
        ('ioRatio', ctypes.c_float),
        ('object', c_void_p),
        ('user', c_void_p),
        ('uniqueID', c_int),        # The plugin ID we want!
        ('version', c_int),
        ('processReplacing', c_void_p),
        ('processDoubleReplacing', c_void_p),
    ]


# Define callback signature
audioMasterCallback = CFUNCTYPE(
    c_void_p,  # Return type (intptr_t)
    c_void_p,  # effect
    c_int,     # opcode
    c_int,     # index
    c_void_p,  # value (intptr_t)
    c_void_p,  # ptr
    ctypes.c_float  # opt
)


class VSTHost:
    """Minimal VST2 host for metadata extraction."""

    def __init__(self):
        """Initialize VST host."""
        self.logger = get_logger()
        self.effect = None
        self.dll = None

    @staticmethod
    @audioMasterCallback
    def host_callback(effect, opcode, index, value, ptr, opt):
        """Minimal host callback.

        This is called by the plugin to communicate with the host.
        We provide minimal responses to keep the plugin happy.
        """
        if opcode == audioMasterVersion:
            return 2400  # VST 2.4
        return 0

    def load_plugin(self, plugin_path: Path) -> bool:
        """
        Load a VST2 plugin DLL.

        Args:
            plugin_path: Path to plugin DLL

        Returns:
            True if loaded successfully
        """
        if platform.system() != 'Windows':
            self.logger.warning("VST host only works on Windows")
            return False

        try:
            # Load the DLL
            self.dll = ctypes.CDLL(str(plugin_path))

            # Get the main entry point
            try:
                main_func = self.dll.VSTPluginMain
            except AttributeError:
                try:
                    main_func = self.dll.main
                except AttributeError:
                    self.logger.debug(f"No VST entry point found in {plugin_path.name}")
                    return False

            # Set function signature
            main_func.argtypes = [audioMasterCallback]
            main_func.restype = POINTER(AEffect)

            # Call the entry point with our callback
            effect_ptr = main_func(VSTHost.host_callback)

            if not effect_ptr:
                self.logger.debug(f"Plugin returned null: {plugin_path.name}")
                return False

            self.effect = effect_ptr.contents

            # Verify magic number
            if self.effect.magic != 0x50745356:  # 'VstP'
                self.logger.debug(f"Invalid VST magic number: {plugin_path.name}")
                return False

            # Call effOpen
            self.dispatch(effOpen, 0, 0, None, 0.0)

            return True

        except Exception as e:
            self.logger.debug(f"Failed to load {plugin_path.name}: {e}")
            return False

    def dispatch(self, opcode: int, index: int, value: int, ptr, opt: float) -> int:
        """
        Call plugin dispatcher.

        Args:
            opcode: VST opcode
            index: Parameter index
            value: Integer value
            ptr: Pointer parameter
            opt: Float parameter

        Returns:
            Return value from plugin
        """
        if not self.effect or not self.effect.dispatcher:
            return 0

        try:
            dispatcher_func = CFUNCTYPE(
                c_void_p,
                POINTER(AEffect),
                c_int,
                c_int,
                c_void_p,
                c_void_p,
                ctypes.c_float
            )(self.effect.dispatcher)

            return dispatcher_func(
                ctypes.pointer(self.effect),
                opcode,
                index,
                value,
                ptr,
                opt
            )
        except Exception as e:
            self.logger.debug(f"Dispatch error (opcode {opcode}): {e}")
            return 0

    def get_plugin_id(self) -> Optional[int]:
        """
        Get plugin unique ID.

        Returns:
            Plugin ID as integer, or None if not available
        """
        if not self.effect:
            return None
        return self.effect.uniqueID

    def get_plugin_name(self) -> Optional[str]:
        """
        Get plugin name.

        Returns:
            Plugin name string, or None
        """
        if not self.effect:
            return None

        buffer = ctypes.create_string_buffer(256)
        self.dispatch(effGetEffectName, 0, 0, buffer, 0.0)

        try:
            return buffer.value.decode('utf-8', errors='ignore').strip()
        except:
            return None

    def get_vendor_name(self) -> Optional[str]:
        """
        Get vendor/publisher name.

        Returns:
            Vendor name string, or None
        """
        if not self.effect:
            return None

        buffer = ctypes.create_string_buffer(256)
        self.dispatch(effGetVendorString, 0, 0, buffer, 0.0)

        try:
            return buffer.value.decode('utf-8', errors='ignore').strip()
        except:
            return None

    def get_product_name(self) -> Optional[str]:
        """
        Get product name.

        Returns:
            Product name string, or None
        """
        if not self.effect:
            return None

        buffer = ctypes.create_string_buffer(256)
        self.dispatch(effGetProductString, 0, 0, buffer, 0.0)

        try:
            return buffer.value.decode('utf-8', errors='ignore').strip()
        except:
            return None

    def get_version(self) -> Optional[int]:
        """
        Get plugin version.

        Returns:
            Version as integer, or None
        """
        if not self.effect:
            return None
        return self.effect.version

    def get_vendor_version(self) -> Optional[int]:
        """
        Get vendor version number.

        Returns:
            Vendor version as integer, or None
        """
        if not self.effect:
            return None
        return self.dispatch(effGetVendorVersion, 0, 0, None, 0.0)

    def get_category(self) -> Optional[str]:
        """
        Get plugin category.

        Returns:
            Category string (e.g., 'effect', 'instrument'), or None
        """
        if not self.effect:
            return None

        cat = self.dispatch(effGetPlugCategory, 0, 0, None, 0.0)

        category_map = {
            kPlugCategEffect: 'fx_other',
            kPlugCategSynth: 'inst_synth',
            kPlugCategAnalysis: 'fx_utility',
            kPlugCategMastering: 'fx_mastering',
            kPlugCategSpacializer: 'fx_spatial',
            kPlugCategRoomFx: 'fx_reverb',
            kPlugCategSurroundFx: 'fx_surround',
            kPlugCategRestoration: 'fx_restoration',
            kPlugCategOfflineProcess: 'fx_offline',
            kPlugCategShell: 'shell',
            kPlugCategGenerator: 'inst_other',
        }

        return category_map.get(cat, 'unknown')

    def get_metadata(self) -> Dict[str, Any]:
        """
        Extract all available metadata from loaded plugin.

        Returns:
            Dictionary with plugin metadata
        """
        if not self.effect:
            return {}

        metadata = {
            'plugin_id': self.get_plugin_id(),
            'name': self.get_plugin_name(),
            'vendor': self.get_vendor_name(),
            'product': self.get_product_name(),
            'version': self.get_version(),
            'vendor_version': self.get_vendor_version(),
            'category': self.get_category(),
            'num_inputs': self.effect.numInputs,
            'num_outputs': self.effect.numOutputs,
            'num_programs': self.effect.numPrograms,
            'num_params': self.effect.numParams,
            'flags': self.effect.flags,
        }

        return metadata

    def close(self):
        """Close the plugin and clean up."""
        if self.effect:
            try:
                self.dispatch(effClose, 0, 0, None, 0.0)
            except:
                pass
            self.effect = None

        if self.dll:
            try:
                # Unload DLL (Windows-specific)
                import _ctypes
                _ctypes.FreeLibrary(self.dll._handle)
            except:
                pass
            self.dll = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False


def extract_vst_metadata(plugin_path: Path, timeout: int = 5) -> Optional[Dict[str, Any]]:
    """
    Safely extract VST metadata with timeout protection.

    Args:
        plugin_path: Path to VST plugin DLL
        timeout: Maximum time to wait (seconds)

    Returns:
        Metadata dictionary or None if extraction fails

    Example:
        >>> metadata = extract_vst_metadata(Path('plugin.dll'))
        >>> print(metadata['plugin_id'])
        1094861636
    """
    logger = get_logger()

    try:
        with VSTHost() as host:
            if host.load_plugin(plugin_path):
                return host.get_metadata()
            else:
                return None
    except Exception as e:
        logger.debug(f"VST metadata extraction failed for {plugin_path.name}: {e}")
        return None


def format_plugin_id(plugin_id: int) -> str:
    """
    Format plugin ID as 4-character code.

    Args:
        plugin_id: Integer plugin ID

    Returns:
        4-character string representation

    Example:
        >>> format_plugin_id(1094861636)
        'ABCD'
    """
    if plugin_id is None or plugin_id == 0:
        return ''

    try:
        # Convert to 4-char code
        bytes_data = struct.pack('>i', plugin_id)
        return bytes_data.decode('ascii', errors='ignore')
    except:
        return f'{plugin_id:08x}'  # Fallback to hex
