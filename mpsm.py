#!/usr/bin/env python3
"""
MPSM - Music Production Software Manager
Main CLI entry point
"""

import os
import platform
from pathlib import Path
from typing import List

import click
from rich.console import Console
from rich.table import Table

from src.cli.license_commands import license
from src.cli.organize_command import organize
from src.cli.registry_commands import registry
from src.cli.scan_command import scan
from src.core.config import ConfigManager

console = Console()


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """MPSM - Music Production Software Manager

    \b
    A comprehensive tool for managing VST plugins, DAWs, and music production software.
    Scans, organizes, and tracks all your music production components.
    """
    pass


@cli.command()
@click.option("--path", default=None, help="Target directory path")
@click.option("--auto-detect", is_flag=True, help="Auto-detect common paths")
def init(path, auto_detect):
    """Initialize MPSM configuration."""
    console.print("\n[bold cyan]MPSM Initialization[/bold cyan]")
    console.print("=" * 50)

    if auto_detect:
        console.print("\n[yellow]Auto-detecting common paths...[/yellow]")
        detected_paths = _auto_detect_scan_paths()
        console.print(f"\n[green]Found {len(detected_paths)} common paths[/green]")
        for path_item in detected_paths[:10]:
            console.print(f"  • {path_item}")
        if len(detected_paths) > 10:
            console.print(f"  ... and {len(detected_paths) - 10} more")

    target_path = Path(path) if path else Path.cwd()
    config_path = target_path / "config.yaml"

    if config_path.exists():
        console.print(f"\n[yellow]⚠ Config already exists: {config_path}[/yellow]")
        if not click.confirm("Overwrite?"):
            console.print("[red]Aborted[/red]")
            return

    config_manager = ConfigManager(config_path, create_if_missing=True)
    config_manager.create_default_config()

    console.print(f"\n[green]✓ Config created: {config_path}[/green]")
    console.print("\n[dim]Edit config.yaml to customize paths and settings[/dim]")
    console.print("[dim]Then run: mpsm scan[/dim]")


def _auto_detect_scan_paths() -> List[str]:
    """Auto-detect common music production paths."""
    detected: List[str] = []
    is_windows = platform.system() == "Windows"

    if not is_windows:
        return detected

    common_paths = [
        "C:\\Program Files\\VSTPlugins",
        "C:\\Program Files\\Common Files\\VST3",
        "C:\\Program Files\\Common Files\\Avid\\Audio",
        "C:\\Program Files\\Steinberg",
        "C:\\Program Files\\Image-Line",
        "C:\\Program Files\\Ableton",
        "C:\\Program Files\\FL Studio",
        "C:\\Program Files\\PreSonus",
        "C:\\Program Files\\Native Instruments",
        "C:\\Program Files\\Spectrasonics",
        "C:\\Program Files\\Waves",
        "C:\\Program Files\\iZotope",
        "C:\\Program Files\\FabFilter",
        "C:\\Program Files\\Arturia",
    ]

    username = os.getenv("USERNAME")
    if username:
        common_paths.extend(
            [
                f"C:\\Users\\{username}\\Documents",
                f"C:\\Users\\{username}\\AppData\\Roaming",
                f"C:\\Users\\{username}\\AppData\\Local",
            ]
        )

    for path_str in common_paths:
        path = Path(path_str)
        if path.exists() and path.is_dir():
            detected.append(path_str)

    return detected


@cli.command()
def status():
    """Show current MPSM status and configuration."""
    console.print("\n[bold cyan]MPSM Status[/bold cyan]")
    console.print("=" * 50)

    try:
        config_manager = ConfigManager()
        console.print("\n[green]✓ Configuration loaded[/green]")

        plugin_paths = config_manager.get_plugin_paths()
        data_paths = config_manager.get_data_paths()

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="yellow")

        table.add_row("Plugin Paths", str(len(plugin_paths)))
        table.add_row("Data Paths", str(len(data_paths)))
        table.add_row("Root Path", str(config_manager.get_root_path()))
        table.add_row("Dry Run", "Yes" if config_manager.is_dry_run() else "No")

        console.print(table)

    except FileNotFoundError:
        console.print("\n[red]✗ Configuration not found[/red]")
        console.print("[dim]Run: mpsm init[/dim]")


# Register commands from CLI modules
cli.add_command(scan)
cli.add_command(organize)
cli.add_command(registry)
cli.add_command(license)


if __name__ == "__main__":
    cli()
