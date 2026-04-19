"""Typer CLI for Project Loom."""

import secrets
import subprocess
from datetime import datetime
from pathlib import Path

import typer
from pydantic import ValidationError
from rich.console import Console

from loom.config import LoomConfig
from loom.workspace import apply_workspace
from loom.wizard import run_init_wizard

app = typer.Typer(help="Project Loom — Multi-repo AI workspace generator")
console = Console()


@app.command()
def init(output: str = typer.Option("loom.yaml", help="Output YAML file path")) -> None:
    """Interactive wizard to create a new loom.yaml configuration.

    Args:
        output: Path to write the configuration file
    """
    try:
        config = run_init_wizard()
        config_path = Path(output)
        config.save_yaml(config_path)
        console.print(f"\n[bold green]✓ Configuration saved to {config_path}[/bold green]")
    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled.[/yellow]")
        raise typer.Exit(1)


@app.command()
def apply(
    config_path: str = typer.Argument("loom.yaml", help="Path to loom.yaml"),
    workspace: str = typer.Option(
        "meta-workspace", help="Workspace output directory"
    ),
) -> None:
    """Apply workspace configuration: clone repos, create symlinks, generate AI configs.

    Args:
        config_path: Path to loom.yaml configuration file
        workspace: Target workspace directory
    """
    try:
        config = LoomConfig.load_yaml(config_path)
        apply_workspace(config, workspace)
    except FileNotFoundError:
        console.print(f"[red]✗ Configuration file not found: {config_path}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def status(config_path: str = typer.Argument("loom.yaml", help="Path to loom.yaml")) -> None:
    """Show git status of all repositories.

    Args:
        config_path: Path to loom.yaml
    """
    try:
        config = LoomConfig.load_yaml(config_path)
        console.print(f"\n[bold]Git Status — {config.name}[/bold]\n")

        for repo in config.repos:
            local_path = repo.resolve_local_path()
            if not local_path.exists():
                console.print(f"[yellow]{repo.name}: [dim]not cloned[/dim][/yellow]")
                continue

            result = subprocess.run(
                ["git", "status", "--short"],
                cwd=local_path,
                capture_output=True,
                text=True,
            )

            console.print(f"[bold]{repo.name}[/bold]")
            if result.stdout:
                console.print(result.stdout)
            else:
                console.print("[dim]  (clean)[/dim]")

    except FileNotFoundError:
        console.print(f"[red]✗ Configuration file not found: {config_path}[/red]")
        raise typer.Exit(1)


@app.command()
def test_all(config_path: str = typer.Argument("loom.yaml", help="Path to loom.yaml")) -> None:
    """Run tests in all repositories.

    Args:
        config_path: Path to loom.yaml
    """
    try:
        config = LoomConfig.load_yaml(config_path)
        console.print(f"\n[bold]Running Tests — {config.name}[/bold]\n")

        failed = []
        for repo in config.repos:
            if not repo.test_command:
                console.print(f"[dim]{repo.name}: [yellow]no test command[/yellow][/dim]")
                continue

            local_path = repo.resolve_local_path()
            if not local_path.exists():
                console.print(f"[yellow]{repo.name}: [dim]not cloned[/dim][/yellow]")
                continue

            console.print(f"[bold]{repo.name}[/bold]: {repo.test_command}")
            result = subprocess.run(
                repo.test_command,
                shell=True,
                cwd=local_path,
                capture_output=True,
            )

            if result.returncode == 0:
                console.print(f"[green]  ✓ Passed[/green]")
            else:
                console.print(f"[red]  ✗ Failed[/red]")
                failed.append(repo.name)

        if failed:
            console.print(f"\n[red]Failed: {', '.join(failed)}[/red]")
            raise typer.Exit(1)
        else:
            console.print(f"\n[green]All tests passed[/green]")

    except FileNotFoundError:
        console.print(f"[red]✗ Configuration file not found: {config_path}[/red]")
        raise typer.Exit(1)


@app.command()
def install(config_path: str = typer.Argument("loom.yaml", help="Path to loom.yaml")) -> None:
    """Install all repositories.

    Args:
        config_path: Path to loom.yaml
    """
    try:
        config = LoomConfig.load_yaml(config_path)
        console.print(f"\n[bold]Installing — {config.name}[/bold]\n")

        for repo in config.repos:
            if not repo.install_command:
                console.print(f"[dim]{repo.name}: [yellow]no install command[/yellow][/dim]")
                continue

            local_path = repo.resolve_local_path()
            if not local_path.exists():
                console.print(f"[yellow]{repo.name}: [dim]not cloned[/dim][/yellow]")
                continue

            console.print(f"[bold]{repo.name}[/bold]: {repo.install_command}")
            result = subprocess.run(
                repo.install_command,
                shell=True,
                cwd=local_path,
            )

            if result.returncode == 0:
                console.print(f"[green]  ✓ Installed[/green]")
            else:
                console.print(f"[red]  ✗ Failed[/red]")

    except FileNotFoundError:
        console.print(f"[red]✗ Configuration file not found: {config_path}[/red]")
        raise typer.Exit(1)


@app.command()
def doctor(config_path: str = typer.Argument("loom.yaml", help="Path to loom.yaml")) -> None:
    """Run health checks for all repositories.

    Args:
        config_path: Path to loom.yaml
    """
    try:
        config = LoomConfig.load_yaml(config_path)
        console.print(f"\n[bold]Health Check — {config.name}[/bold]\n")

        for repo in config.repos:
            if not repo.doctor_command:
                console.print(f"[dim]{repo.name}: [yellow]no doctor command[/yellow][/dim]")
                continue

            local_path = repo.resolve_local_path()
            if not local_path.exists():
                console.print(f"[yellow]{repo.name}: [dim]not cloned[/dim][/yellow]")
                continue

            console.print(f"[bold]{repo.name}[/bold]")
            subprocess.run(
                repo.doctor_command,
                shell=True,
                cwd=local_path,
            )

    except FileNotFoundError:
        console.print(f"[red]✗ Configuration file not found: {config_path}[/red]")
        raise typer.Exit(1)


@app.command()
def diff(config_path: str = typer.Argument("loom.yaml", help="Path to loom.yaml")) -> None:
    """Show git diff summary for all repositories.

    Args:
        config_path: Path to loom.yaml
    """
    try:
        config = LoomConfig.load_yaml(config_path)
        console.print(f"\n[bold]Git Diff — {config.name}[/bold]\n")

        for repo in config.repos:
            local_path = repo.resolve_local_path()
            if not local_path.exists():
                console.print(f"[yellow]{repo.name}: [dim]not cloned[/dim][/yellow]")
                continue

            result = subprocess.run(
                ["git", "diff", "--stat"],
                cwd=local_path,
                capture_output=True,
                text=True,
            )

            if result.stdout:
                console.print(f"[bold]{repo.name}[/bold]")
                console.print(result.stdout)
            else:
                console.print(f"[dim]{repo.name}: (no changes)[/dim]")

    except FileNotFoundError:
        console.print(f"[red]✗ Configuration file not found: {config_path}[/red]")
        raise typer.Exit(1)


@app.command()
def logs(
    config_path: str = typer.Argument("loom.yaml", help="Path to loom.yaml"),
    count: int = typer.Option(10, help="Number of commits to show"),
) -> None:
    """Show recent commits in all repositories.

    Args:
        config_path: Path to loom.yaml
        count: Number of commits to show per repo
    """
    try:
        config = LoomConfig.load_yaml(config_path)
        console.print(f"\n[bold]Recent Commits — {config.name}[/bold]\n")

        for repo in config.repos:
            local_path = repo.resolve_local_path()
            if not local_path.exists():
                console.print(f"[yellow]{repo.name}: [dim]not cloned[/dim][/yellow]")
                continue

            result = subprocess.run(
                ["git", "log", f"-{count}", "--oneline"],
                cwd=local_path,
                capture_output=True,
                text=True,
            )

            if result.stdout:
                console.print(f"[bold]{repo.name}[/bold]")
                console.print(result.stdout)

    except FileNotFoundError:
        console.print(f"[red]✗ Configuration file not found: {config_path}[/red]")
        raise typer.Exit(1)


@app.command()
def validate(config_path: str = typer.Argument("loom.yaml", help="Path to loom.yaml")) -> None:
    """Validate loom.yaml configuration against schema.

    Args:
        config_path: Path to loom.yaml
    """
    try:
        config = LoomConfig.load_yaml(config_path)
        console.print(f"[bold green]✓ Configuration valid[/bold green]")
        console.print(f"  Workspace: {config.name}")
        console.print(f"  Repos: {len(config.repos)}")
        if config.dependencies:
            console.print(f"  Dependencies: {len(config.dependencies)}")
        if config.impact_zones:
            console.print(f"  Impact zones: {len(config.impact_zones)}")
    except FileNotFoundError:
        console.print(f"[red]✗ Configuration file not found: {config_path}[/red]")
        raise typer.Exit(1)
    except ValidationError as e:
        console.print(f"[red]✗ Configuration validation error[/red]")
        for error in e.errors():
            console.print(f"  {error['loc'][0]}: {error['msg']}")
        raise typer.Exit(1)


@app.command()
def pull(config_path: str = typer.Argument("loom.yaml", help="Path to loom.yaml")) -> None:
    """Pull latest changes from all repositories (git pull --ff-only).

    Args:
        config_path: Path to loom.yaml
    """
    try:
        config = LoomConfig.load_yaml(config_path)
        console.print(f"\n[bold]Pulling — {config.name}[/bold]\n")

        for repo in config.repos:
            local_path = repo.resolve_local_path()
            if not local_path.exists():
                console.print(f"[yellow]{repo.name}: [dim]not cloned[/dim][/yellow]")
                continue

            result = subprocess.run(
                ["git", "pull", "--ff-only"],
                cwd=local_path,
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                if result.stdout.strip():
                    console.print(f"[green]✓ {repo.name}[/green]")
                    console.print(f"  {result.stdout.strip()}")
                else:
                    console.print(f"[dim]{repo.name}: (already up to date)[/dim]")
            else:
                console.print(f"[red]✗ {repo.name} failed[/red]")
                if result.stderr:
                    console.print(f"  {result.stderr.strip()}")

    except FileNotFoundError:
        console.print(f"[red]✗ Configuration file not found: {config_path}[/red]")
        raise typer.Exit(1)


@app.command()
def sync_commit(
    message: str = typer.Argument(..., help="Commit message"),
    config_path: str = typer.Option("loom.yaml", help="Path to loom.yaml"),
) -> None:
    """Commit changes across all repositories with a shared sync trailer.

    Generates a unique sync ID (LOOM-YYYY-MM-DD-<6hex>) and commits all dirty repos
    with the trailer appended to the message.

    Args:
        message: Commit message
        config_path: Path to loom.yaml
    """
    try:
        config = LoomConfig.load_yaml(config_path)

        # Generate sync ID: LOOM-YYYY-MM-DD-<6hex>
        date_str = datetime.now().strftime("%Y-%m-%d")
        hex_str = secrets.token_hex(3)
        sync_id = f"LOOM-{date_str}-{hex_str}"

        console.print(f"\n[bold]Sync Commit — {config.name}[/bold]")
        console.print(f"[dim]Sync ID: {sync_id}[/dim]\n")

        committed = []
        skipped = []

        for repo in config.repos:
            local_path = repo.resolve_local_path()
            if not local_path.exists():
                console.print(f"[yellow]{repo.name}: [dim]not cloned[/dim][/yellow]")
                continue

            # Check if repo is dirty
            status_result = subprocess.run(
                ["git", "status", "--short"],
                cwd=local_path,
                capture_output=True,
                text=True,
            )

            if not status_result.stdout.strip():
                skipped.append(repo.name)
                console.print(f"[dim]{repo.name}: (clean, skipped)[/dim]")
                continue

            # Commit: git add -A && git commit
            add_result = subprocess.run(
                ["git", "add", "-A"],
                cwd=local_path,
                capture_output=True,
            )

            if add_result.returncode != 0:
                console.print(f"[red]✗ {repo.name}: failed to stage[/red]")
                continue

            commit_msg = f"{message}\n\nLoom-Sync: {sync_id}"
            commit_result = subprocess.run(
                ["git", "commit", "-m", commit_msg],
                cwd=local_path,
                capture_output=True,
                text=True,
            )

            if commit_result.returncode == 0:
                committed.append(repo.name)
                console.print(f"[green]✓ {repo.name}[/green]")
            else:
                console.print(f"[red]✗ {repo.name}: commit failed[/red]")

        console.print(f"\n[bold]Summary[/bold]")
        console.print(f"  Committed: {len(committed)}")
        console.print(f"  Skipped: {len(skipped)}")

    except FileNotFoundError:
        console.print(f"[red]✗ Configuration file not found: {config_path}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
