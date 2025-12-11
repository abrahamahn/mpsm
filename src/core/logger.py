"""Logging system for MPSM."""

import logging
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional


class MPSMLogger:
    """Custom logging system with rotation and levels."""

    def __init__(
        self,
        log_dir: Optional[Path] = None,
        level: str = "INFO",
        log_to_console: bool = True,
        log_to_file: bool = True,
        max_log_size_mb: int = 100,
    ):
        """
        Initialize MPSM logger.

        Args:
            log_dir: Directory for log files. If None, uses logs/ in project root
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_to_console: Whether to log to console
            log_to_file: Whether to log to file
            max_log_size_mb: Maximum log file size in MB before rotation
        """
        if log_dir is None:
            project_root = Path(__file__).parent.parent.parent
            log_dir = project_root / "logs"

        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.level = getattr(logging, level.upper())
        self.log_to_console = log_to_console
        self.log_to_file = log_to_file
        self.max_log_size_bytes = max_log_size_mb * 1024 * 1024

        # Create logger
        self.logger = logging.getLogger("mpsm")
        self.logger.setLevel(self.level)

        # Remove existing handlers to avoid duplicates
        self.logger.handlers.clear()

        # Setup logging
        self.setup_logging()

    def setup_logging(self) -> None:
        """Configure logging with rotation and formatters."""
        # Create formatter
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )

        # Console handler
        if self.log_to_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(self.level)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

        # File handler with rotation
        if self.log_to_file:
            log_file = self.log_dir / f"mpsm_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

            file_handler = RotatingFileHandler(
                filename=log_file, maxBytes=self.max_log_size_bytes, backupCount=5, encoding="utf-8"
            )
            file_handler.setLevel(self.level)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

    def debug(self, message: str, **kwargs) -> None:
        """Log debug message."""
        self.logger.debug(message, extra=kwargs)

    def info(self, message: str, **kwargs) -> None:
        """Log info message."""
        self.logger.info(message, extra=kwargs)

    def warning(self, message: str, **kwargs) -> None:
        """Log warning message."""
        self.logger.warning(message, extra=kwargs)

    def error(self, message: str, **kwargs) -> None:
        """Log error message."""
        self.logger.error(message, extra=kwargs)

    def critical(self, message: str, **kwargs) -> None:
        """Log critical message."""
        self.logger.critical(message, extra=kwargs)

    def log_operation(self, operation: str, details: dict) -> None:
        """
        Log operation with structured data.

        Args:
            operation: Operation name
            details: Dictionary of operation details
        """
        detail_str = ", ".join(f"{k}={v}" for k, v in details.items())
        self.logger.info(f"Operation: {operation} | {detail_str}")

    def log_error(self, error: Exception, context: dict) -> None:
        """
        Log error with context.

        Args:
            error: Exception that occurred
            context: Dictionary of context information
        """
        context_str = ", ".join(f"{k}={v}" for k, v in context.items())
        self.logger.error(
            f"Error: {type(error).__name__}: {str(error)} | Context: {context_str}", exc_info=True
        )

    def export_logs(self, start_date: datetime, end_date: datetime, output_path: Path) -> None:
        """
        Export logs for time period.

        Args:
            start_date: Start of time period
            end_date: End of time period
            output_path: Where to save exported logs
        """
        # Find all log files in the time period
        matching_logs = []

        for log_file in self.log_dir.glob("mpsm_*.log*"):
            # Parse timestamp from filename (mpsm_YYYYMMDD_HHMMSS.log)
            try:
                timestamp_str = log_file.stem.split("_")[1] + "_" + log_file.stem.split("_")[2]
                log_date = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")

                if start_date <= log_date <= end_date:
                    matching_logs.append(log_file)
            except (IndexError, ValueError):
                # Skip files that don't match expected format
                continue

        # Combine matching logs
        with open(output_path, "w", encoding="utf-8") as outfile:
            outfile.write(f"# MPSM Logs Export\n")
            outfile.write(f"# Period: {start_date} to {end_date}\n")
            outfile.write(f"# Files included: {len(matching_logs)}\n\n")

            for log_file in sorted(matching_logs):
                outfile.write(f"\n{'='*80}\n")
                outfile.write(f"# File: {log_file.name}\n")
                outfile.write(f"{'='*80}\n\n")

                with open(log_file, "r", encoding="utf-8") as infile:
                    outfile.write(infile.read())

        self.logger.info(f"Exported {len(matching_logs)} log files to {output_path}")


# Global logger instance
_global_logger: Optional[MPSMLogger] = None


def get_logger(
    log_dir: Optional[Path] = None,
    level: str = "INFO",
    log_to_console: bool = True,
    log_to_file: bool = True,
) -> MPSMLogger:
    """
    Get or create global logger instance.

    Args:
        log_dir: Directory for log files
        level: Logging level
        log_to_console: Whether to log to console
        log_to_file: Whether to log to file

    Returns:
        MPSMLogger instance
    """
    global _global_logger

    if _global_logger is None:
        _global_logger = MPSMLogger(
            log_dir=log_dir,
            level=level,
            log_to_console=log_to_console,
            log_to_file=log_to_file,
        )

    return _global_logger
