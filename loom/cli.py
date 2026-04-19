"""Typer CLI for Project Loom."""

import secrets
import subprocess
from datetime import datetime
from pathlib import Path

import typer
from pydantic import ValidationError
from rich.console import Console
from rich.table import Table

from loom.analyzer import blast_radius, check_boundaries, trace_chain
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
                console.print("[green]  ✓ Passed[/green]")
            else:
                console.print("[red]  ✗ Failed[/red]")
                failed.append(repo.name)

        if failed:
            console.print(f"\n[red]Failed: {', '.join(failed)}[/red]")
            raise typer.Exit(1)
        else:
            console.print("\n[green]All tests passed[/green]")

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
                console.print("[green]  ✓ Installed[/green]")
            else:
                console.print("[red]  ✗ Failed[/red]")

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
        console.print("[bold green]✓ Configuration valid[/bold green]")
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
        console.print("[red]✗ Configuration validation error[/red]")
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

        console.print("\n[bold]Summary[/bold]")
        console.print(f"  Committed: {len(committed)}")
        console.print(f"  Skipped: {len(skipped)}")

    except FileNotFoundError:
        console.print(f"[red]✗ Configuration file not found: {config_path}[/red]")
        raise typer.Exit(1)


@app.command()
def pre_change(
    file_path: str = typer.Argument(..., help="File path to check (e.g., src/auth.py)"),
    config_path: str = typer.Option("loom.yaml", help="Path to loom.yaml"),
) -> None:
    """Pre-change safety checklist for a file.

    Lookup file in impact zones and emit safety checklist before editing.

    Args:
        file_path: File path to check
        config_path: Path to loom.yaml
    """
    try:
        config = LoomConfig.load_yaml(config_path)
        console.print("\n[bold]Pre-Change Safety Check[/bold]")
        console.print(f"[dim]File: {file_path}[/dim]\n")

        # Find impact zones affecting this file
        affected_zones = []
        for zone in config.impact_zones or []:
            if zone.source and zone.source.file and file_path.endswith(zone.source.file):
                affected_zones.append(zone)
            elif zone.target and zone.target.file and file_path.endswith(zone.target.file):
                affected_zones.append(zone)

        if affected_zones:
            console.print("[bold yellow]⚠ Critical file detected![/bold yellow]\n")
            for zone in affected_zones:
                console.print(f"[bold]{zone.name}[/bold] ({zone.id})")
                console.print(f"  Risk: {zone.risk.value}")
                console.print(f"  Trigger: {zone.trigger}")
                if zone.shared_env:
                    console.print(f"  Environment: {', '.join(zone.shared_env)}")
                console.print()

            console.print("[bold]Pre-Flight Checklist:[/bold]")
            console.print("- [ ] Read the impact zone description")
            console.print("- [ ] Review the trigger condition")
            console.print("- [ ] Check that shared environment variables are set")
            console.print("- [ ] Run tests in affected repositories after changes")
            console.print("- [ ] Use `loom sync-commit` to maintain consistency")
        else:
            console.print("[green]✓ No critical impact zones for this file[/green]")
            console.print("Safe to edit.")

    except FileNotFoundError:
        console.print(f"[red]✗ Configuration file not found: {config_path}[/red]")
        raise typer.Exit(1)


@app.command()
def post_change(
    file_path: str = typer.Argument(..., help="File path that was changed"),
    config_path: str = typer.Option("loom.yaml", help="Path to loom.yaml"),
) -> None:
    """Post-change validation: run affected tests.

    Determine which repositories are affected by changes to a file and run their tests.

    Args:
        file_path: File path that was changed
        config_path: Path to loom.yaml
    """
    try:
        config = LoomConfig.load_yaml(config_path)
        console.print("\n[bold]Post-Change Test Validation[/bold]")
        console.print(f"[dim]File: {file_path}[/dim]\n")

        # Find affected repositories
        affected_repos = set()
        for zone in config.impact_zones or []:
            if zone.source and zone.source.file and file_path.endswith(zone.source.file):
                if zone.source.repo:
                    affected_repos.add(zone.source.repo)
            elif zone.target and zone.target.file and file_path.endswith(zone.target.file):
                if zone.target.repo:
                    affected_repos.add(zone.target.repo)

        if affected_repos:
            console.print(f"[bold yellow]Running tests in {len(affected_repos)} affected repo(s):[/bold yellow]\n")
            failed = []

            for repo_name in sorted(affected_repos):
                repo = next((r for r in config.repos if r.name == repo_name), None)
                if not repo:
                    console.print(f"[red]✗ {repo_name}: not found in config[/red]")
                    continue

                if not repo.test_command:
                    console.print(f"[dim]{repo_name}: [yellow]no test command[/yellow][/dim]")
                    continue

                local_path = repo.resolve_local_path()
                if not local_path.exists():
                    console.print(f"[yellow]{repo_name}: [dim]not cloned[/dim][/yellow]")
                    continue

                console.print(f"[bold]{repo_name}[/bold]: {repo.test_command}")
                result = subprocess.run(
                    repo.test_command,
                    shell=True,
                    cwd=local_path,
                    capture_output=True,
                )

                if result.returncode == 0:
                    console.print("[green]  ✓ Passed[/green]\n")
                else:
                    console.print("[red]  ✗ Failed[/red]\n")
                    failed.append(repo_name)

            if failed:
                console.print(f"[red]✗ Tests failed in: {', '.join(failed)}[/red]")
                raise typer.Exit(1)
            else:
                console.print("[green]✓ All affected tests passed[/green]")
        else:
            console.print("[green]✓ No affected repositories[/green]")
            console.print("Changes are isolated.")

    except FileNotFoundError:
        console.print(f"[red]✗ Configuration file not found: {config_path}[/red]")
        raise typer.Exit(1)


@app.command()
def serve(
    config_path: str = typer.Argument("loom.yaml", help="Path to loom.yaml"),
) -> None:
    """Start MCP server for Claude Code integration.

    Exposes workspace tools (impact zones, validation, test running) to Claude Code
    via the Model Context Protocol (MCP).

    Args:
        config_path: Path to loom.yaml configuration
    """
    try:
        # Validate config exists and is valid
        config = LoomConfig.load_yaml(config_path)
        console.print(f"[bold green]✓ Configuration loaded: {config.name}[/bold green]")

        from loom.mcp_server import server

        console.print("[bold]Starting MCP server...[/bold]")
        console.print(f"[dim]Config: {config_path}[/dim]")
        console.print("[dim]Available tools:[/dim]")
        console.print("  - loom_get_impact_zones")
        console.print("  - loom_find_dependents")
        console.print("  - loom_validate_change")
        console.print("  - loom_workspace_status")
        console.print("  - loom_run_affected_tests")
        console.print("  - loom_get_session_template")
        console.print("")
        console.print("[yellow]Press Ctrl+C to stop the server[/yellow]")

        # Store config path in server for tool access
        server.config_path = config_path

        # Run server
        server.run()

    except FileNotFoundError:
        console.print(f"[red]✗ Configuration file not found: {config_path}[/red]")
        raise typer.Exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Server stopped[/yellow]")
        raise typer.Exit(0)
    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def analyze_impact(
    file_path: str = typer.Argument(..., help="File path to analyze (e.g., src/auth.py)"),
    config_path: str = typer.Option("loom.yaml", help="Path to loom.yaml"),
) -> None:
    """Analyze blast radius of changes to a file.

    Shows impact zones, affected repositories, and a blast radius score (0-10).

    Args:
        file_path: File path to analyze
        config_path: Path to loom.yaml
    """
    try:
        config = LoomConfig.load_yaml(config_path)
        result = blast_radius(config, file_path)

        console.print("\n[bold]Blast Radius Analysis[/bold]")
        console.print(f"[dim]File: {file_path}[/dim]\n")

        # Show blast radius score
        score = result["score"]
        score_color = (
            "green" if score <= 3 else "yellow" if score <= 6 else "red"
        )
        console.print(f"[bold {score_color}]Blast Radius Score: {score}/10[/bold {score_color}]")
        console.print(f"Max Risk: {result['max_risk']}")
        console.print(f"Affected Repos: {', '.join(result['affected_repos']) or 'None'}\n")

        # Show impact zones table
        if result["impact_zones"]:
            table = Table(title="Impact Zones")
            table.add_column("Zone ID", style="cyan")
            table.add_column("Name", style="magenta")
            table.add_column("Risk", style="red")
            table.add_column("Trigger", style="yellow")

            for zone in result["impact_zones"]:
                table.add_row(
                    zone["id"],
                    zone["name"],
                    zone["risk"],
                    zone["trigger"][:40] + "..." if len(zone["trigger"]) > 40 else zone["trigger"],
                )

            console.print(table)
        else:
            console.print("[green]✓ No critical impact zones[/green]")

    except FileNotFoundError:
        console.print(f"[red]✗ Configuration file not found: {config_path}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def trace_dependency(
    repo: str = typer.Argument(..., help="Repository name to trace"),
    config_path: str = typer.Option("loom.yaml", help="Path to loom.yaml"),
) -> None:
    """Trace transitive dependency chain for a repository.

    Shows the full chain of dependencies and impact zones along the path.

    Args:
        repo: Repository name
        config_path: Path to loom.yaml
    """
    try:
        config = LoomConfig.load_yaml(config_path)
        result = trace_chain(config, repo)

        console.print(f"\n[bold]Dependency Chain — {repo}[/bold]\n")

        # Show chain
        chain_str = " → ".join(result["chain"])
        console.print(f"[bold cyan]{chain_str}[/bold cyan]\n")

        # Show impact zones along the chain
        if result["impact_zones"]:
            console.print("[bold yellow]Impact Zones Along Chain:[/bold yellow]")
            for zone in result["impact_zones"]:
                console.print(
                    f"  {zone['id']}: {zone['name']} ({zone['risk']}) "
                    f"[{zone['from']} → {zone['to']}]"
                )
        else:
            console.print("[green]✓ No impact zones along chain[/green]")

    except FileNotFoundError:
        console.print(f"[red]✗ Configuration file not found: {config_path}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def check_boundary(
    from_repo: str = typer.Argument(..., help="Source repository"),
    to_repo: str = typer.Argument(..., help="Target repository"),
    config_path: str = typer.Option("loom.yaml", help="Path to loom.yaml"),
) -> None:
    """Check and validate boundaries between two repositories.

    Lists matching boundaries and optionally runs test commands to verify integration.

    Args:
        from_repo: Source repository name
        to_repo: Target repository name
        config_path: Path to loom.yaml
    """
    try:
        config = LoomConfig.load_yaml(config_path)
        boundaries = check_boundaries(config, from_repo, to_repo)

        console.print(f"\n[bold]Boundary Check — {from_repo} → {to_repo}[/bold]\n")

        if not boundaries:
            console.print("[yellow]No boundaries defined between these repositories[/yellow]")
            return

        # Show boundaries table
        table = Table(title="Boundaries")
        table.add_column("Interface", style="cyan")
        table.add_column("Protocol", style="magenta")
        table.add_column("Test Command", style="yellow")

        for boundary in boundaries:
            table.add_row(
                boundary["interface"],
                boundary["protocol"],
                boundary["test_command"] or "[dim]None[/dim]",
            )

        console.print(table)

        # Run test commands
        failed = []
        for boundary in boundaries:
            if boundary["test_command"]:
                console.print(f"\n[bold]Running test:[/bold] {boundary['test_command']}")
                result = subprocess.run(
                    boundary["test_command"],
                    shell=True,
                    capture_output=True,
                )

                if result.returncode == 0:
                    console.print("[green]✓ Passed[/green]")
                else:
                    console.print("[red]✗ Failed[/red]")
                    failed.append(boundary["interface"])

        if failed:
            console.print(f"\n[red]✗ Tests failed for: {', '.join(failed)}[/red]")
            raise typer.Exit(1)
        else:
            console.print("\n[green]✓ All boundaries verified[/green]")

    except FileNotFoundError:
        console.print(f"[red]✗ Configuration file not found: {config_path}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
