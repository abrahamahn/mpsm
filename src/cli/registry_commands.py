"""Registry commands - manage Windows registry operations."""

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from ..core.config import ConfigManager
from ..core.exceptions import RegistryException
from ..core.logger import get_logger
from ..registry.backup import RegistryBackup
from ..registry.manager import RegistryManager
from ..registry.registry_reader import RegistryReader
from ..registry.validator import PathValidator

console = Console()


@click.group()
def registry():
    """Registry management commands."""
    pass


@registry.command("backup")
@click.option("--keys", "-k", multiple=True, help="Registry keys to backup")
@click.option("--description", "-d", default="", help="Backup description")
def registry_backup(keys, description):
    """Backup registry keys."""
    try:
        console.print("[bold cyan]Registry Backup[/bold cyan]")
        console.print("=" * 50)

        # Initialize registry manager
        manager = RegistryManager()

        # If no keys specified, backup all known music production keys
        if not keys:
            reader = RegistryReader()
            console.print(
                "\n[yellow]No keys specified, backing up all known music production keys...[/yellow]"
            )
            keys = []
            for base_key in reader.KNOWN_KEYS:
                for hive in ["HKLM", "HKCU"]:
                    key_path = f"{hive}\\{base_key}"
                    if reader.key_exists(key_path):
                        keys.append(key_path)

        console.print(f"\nBacking up {len(keys)} keys...")

        # Create backup
        backup_id = manager.backup_keys(list(keys), description)

        console.print(f"\n[bold green]✓ Backup created successfully![/bold green]")
        console.print(f"Backup ID: {backup_id}")
        console.print(f"Keys backed up: {len(keys)}")

    except RegistryException as e:
        console.print(f"\n[red]Registry Error:[/red] {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]Error:[/red] {e}")
        sys.exit(1)


@registry.command("restore")
@click.argument("backup_id")
def registry_restore(backup_id):
    """Restore registry from backup."""
    try:
        console.print("[bold cyan]Registry Restore[/bold cyan]")
        console.print("=" * 50)

        manager = RegistryManager()

        # Get backup info
        backup_info = manager.backup_manager.get_backup_info(backup_id)
        if not backup_info:
            console.print(f"[red]Backup not found: {backup_id}[/red]")
            sys.exit(1)

        console.print(f"\nBackup ID: {backup_id}")
        console.print(f"Date: {backup_info['backup_date']}")
        console.print(f"Keys: {backup_info['keys_count']}")
        console.print(f"Description: {backup_info.get('description', 'N/A')}")

        if not click.confirm("\nAre you sure you want to restore this backup?"):
            console.print("[yellow]Restore cancelled[/yellow]")
            return

        console.print("\nRestoring...")
        success = manager.rollback(backup_id)

        if success:
            console.print(f"\n[bold green]✓ Backup restored successfully![/bold green]")
        else:
            console.print(f"\n[red]✗ Restore failed[/red]")
            sys.exit(1)

    except RegistryException as e:
        console.print(f"\n[red]Registry Error:[/red] {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]Error:[/red] {e}")
        sys.exit(1)


@registry.command("list")
def registry_list():
    """List all registry backups."""
    try:
        manager = RegistryManager()
        backups = manager.list_backups()

        if not backups:
            console.print("[yellow]No backups found[/yellow]")
            return

        console.print(f"\n[bold]Registry Backups ({len(backups)} total)[/bold]")

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Backup ID", style="cyan")
        table.add_column("Date", style="yellow")
        table.add_column("Keys", style="green")
        table.add_column("Description", style="white")

        for backup in backups:
            table.add_row(
                backup["backup_id"],
                backup["backup_date"][:19],  # Truncate timestamp
                str(backup["keys_count"]),
                backup.get("description", "")[:50],  # Truncate long descriptions
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@registry.command("validate")
def registry_validate():
    """Validate registry paths."""
    try:
        console.print("[bold cyan]Registry Path Validation[/bold cyan]")
        console.print("=" * 50)

        validator = PathValidator()

        console.print("\n[bold]Validating registry paths...[/bold]")
        broken_paths = validator.validate_registry_paths()

        if not broken_paths:
            console.print("\n[bold green]✓ All registry paths are valid![/bold green]")
            return

        console.print(f"\n[bold red]Found {len(broken_paths)} broken paths:[/bold red]")

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Key", style="cyan")
        table.add_column("Value", style="yellow")
        table.add_column("Path", style="red")
        table.add_column("Reason", style="white")

        for broken in broken_paths[:20]:  # Show first 20
            table.add_row(
                broken["key_path"][-50:],  # Truncate long paths
                broken["value_name"],
                broken["path"][-50:],
                broken["reason"],
            )

        console.print(table)

        if len(broken_paths) > 20:
            console.print(f"\n[yellow]... and {len(broken_paths) - 20} more[/yellow]")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@registry.command("scan")
@click.option("--export", "-e", type=click.Path(), help="Export to file")
def registry_scan(export):
    """Scan registry for music production software."""
    try:
        console.print("[bold cyan]Registry Scanner[/bold cyan]")
        console.print("=" * 50)

        reader = RegistryReader()

        console.print("\n[bold]Scanning registry...[/bold]")
        all_entries = reader.scan_all_music_production_keys()

        total_entries = sum(len(entries) for entries in all_entries.values())
        console.print(
            f"\n[bold green]Found {len(all_entries)} keys with {total_entries} total entries[/bold green]"
        )

        # Display summary
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Registry Key", style="cyan")
        table.add_column("Values", style="yellow")

        for key_path, entries in list(all_entries.items())[:15]:
            table.add_row(key_path[-60:], str(len(entries)))

        console.print(table)

        if len(all_entries) > 15:
            console.print(f"\n[yellow]... and {len(all_entries) - 15} more keys[/yellow]")

        # Export if requested
        if export:
            reader.export_registry_snapshot(Path(export))
            console.print(f"\n[green]✓[/green] Exported to {export}")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)
