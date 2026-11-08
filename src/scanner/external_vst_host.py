"""External VST Host communication via JUCE application.

This module provides communication with an external JUCE-based VST host application
that safely loads and extracts metadata from VST2/VST3 plugins.

Architecture:
    MPSM (Python) <--JSON--> JUCE VST Host (C++)

    Communication methods:
    1. Subprocess (stdin/stdout) - Default, simple
    2. HTTP REST API - For separate process/server
    3. Named pipes - For Windows IPC (future)
"""

import json
import subprocess
import time
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..core.logger import get_logger


class CommunicationMethod(Enum):
    """Communication method with external VST host."""

    SUBPROCESS = "subprocess"  # stdin/stdout JSON
    HTTP = "http"  # REST API
    NAMED_PIPE = "named_pipe"  # Windows named pipes (future)


class ExternalVSTHost:
    """
    Communicates with external JUCE-based VST host application.

    The external host loads VST plugins safely in a separate process,
    preventing crashes from unstable plugins.
    """

    def __init__(
        self,
        juce_host_path: Optional[Path] = None,
        communication_method: CommunicationMethod = CommunicationMethod.SUBPROCESS,
        timeout: int = 5,
        http_url: str = "http://localhost:8080",
    ):
        """
        Initialize external VST host communication.

        Args:
            juce_host_path: Path to JUCE VST scanner executable
            communication_method: How to communicate with host
            timeout: Timeout in seconds for plugin loading
            http_url: URL for HTTP communication method
        """
        self.logger = get_logger()
        self.juce_host_path = juce_host_path
        self.communication_method = communication_method
        self.timeout = timeout
        self.http_url = http_url

        self._process: Optional[subprocess.Popen[str]] = None

        if communication_method == CommunicationMethod.SUBPROCESS:
            if not juce_host_path or not Path(juce_host_path).exists():
                raise FileNotFoundError(
                    f"JUCE VST host not found: {juce_host_path}. "
                    "Please build the JUCE VST scanner first."
                )

    def start(self) -> bool:
        """
        Start the external VST host process.

        Returns:
            True if started successfully
        """
        if self.communication_method == CommunicationMethod.SUBPROCESS:
            return self._start_subprocess()
        if self.communication_method == CommunicationMethod.HTTP:
            return self._check_http_available()

        return False

    def _start_subprocess(self) -> bool:
        """Start subprocess for stdin/stdout communication."""
        try:
            self._process = subprocess.Popen(
                [str(self.juce_host_path)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )
            self.logger.info(f"Started JUCE VST host: {self.juce_host_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to start JUCE host: {e}")
            return False

    def _check_http_available(self) -> bool:
        """Check if HTTP server is available."""
        try:
            import requests

            response = requests.get(f"{self.http_url}/health", timeout=1)
            return bool(response.status_code == 200)
        except Exception:
            return False

    def stop(self) -> None:
        """Stop the external VST host process."""
        if self._process:
            try:
                self._process.terminate()
                self._process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self._process.kill()
            finally:
                self._process = None

    def extract_metadata(self, plugin_path: Path) -> Optional[Dict[str, Any]]:
        """
        Extract metadata from plugin using external host.

        Args:
            plugin_path: Path to VST plugin file

        Returns:
            Metadata dictionary or None if extraction failed
        """
        if self.communication_method == CommunicationMethod.SUBPROCESS:
            return self._extract_via_subprocess(plugin_path)
        if self.communication_method == CommunicationMethod.HTTP:
            return self._extract_via_http(plugin_path)

        return None

    def _extract_via_subprocess(self, plugin_path: Path) -> Optional[Dict[str, Any]]:
        """Extract via subprocess stdin/stdout."""
        if not self._process:
            if not self.start():
                return None

        if not self._process or not self._process.stdin or not self._process.stdout:
            return None

        try:
            request = {"command": "scan", "path": str(plugin_path), "timeout": self.timeout}

            self._process.stdin.write(json.dumps(request) + "\n")
            self._process.stdin.flush()

            start_time = time.time()
            while time.time() - start_time < self.timeout:
                line = self._process.stdout.readline()
                if line:
                    response = json.loads(line.strip())

                    if response.get("success"):
                        data = response.get("data")
                        return dict(data) if isinstance(data, dict) else None
                    error = response.get("error", "Unknown error")
                    self.logger.debug(f"Plugin scan failed: {error}")
                    return None

            self.logger.warning(f"Timeout scanning {plugin_path}")
            return None

        except Exception as e:
            self.logger.error(f"Error extracting metadata: {e}")
            return None

    def _extract_via_http(self, plugin_path: Path) -> Optional[Dict[str, Any]]:
        """Extract via HTTP REST API."""
        try:
            import requests

            response = requests.post(
                f"{self.http_url}/scan",
                json={"path": str(plugin_path), "timeout": self.timeout},
                timeout=self.timeout + 1,
            )

            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    data = result.get("data")
                    return dict(data) if isinstance(data, dict) else None

            return None

        except Exception as e:
            self.logger.error(f"HTTP request failed: {e}")
            return None

    def batch_extract(self, plugin_paths: List[Path]) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        Extract metadata from multiple plugins.

        Args:
            plugin_paths: List of plugin paths to scan

        Returns:
            Dictionary mapping path to metadata (or None if failed)
        """
        results: Dict[str, Optional[Dict[str, Any]]] = {}

        if not self.start():
            return {str(path): None for path in plugin_paths}

        try:
            for plugin_path in plugin_paths:
                results[str(plugin_path)] = self.extract_metadata(plugin_path)
        finally:
            self.stop()

        return results

    def __enter__(self) -> "ExternalVSTHost":
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.stop()


def find_juce_host() -> Optional[Path]:
    """
    Find JUCE VST host executable.

    Returns:
        Path to JUCE host or None
    """
    candidates = [
        Path("bin/VSTScanner.exe"),
        Path("bin/VSTScanner"),
        Path("tools/VSTScanner.exe"),
        Path("tools/VSTScanner"),
        Path("VSTScanner.exe"),
        Path("VSTScanner"),
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()

    return None
