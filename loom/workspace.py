"""Core workspace setup logic — clone, symlink, and generate configurations."""

import subprocess
from pathlib import Path

from rich.console import Console

from loom.config import LoomConfig
from loom.generators import (
    generate_aider,
    generate_claude_code,
    generate_codex,
    generate_cursor,
)

console = Console()


def apply_workspace(config: LoomConfig, workspace_path: Path | str = None) -> None:
    """Apply workspace configuration: clone repos, create symlinks, generate AI configs.

    Args:
        config: LoomConfig loaded from loom.yaml
        workspace_path: Target workspace path (default: ./meta-workspace)
    """
    workspace_path = Path(workspace_path or "meta-workspace")

    console.print(f"[bold blue]Applying workspace: {config.name}[/bold blue]")

    # Create workspace structure
    _setup_workspace_dirs(workspace_path)

    # Process repositories
    services_path = workspace_path / "services"
    for repo in config.repos:
        _process_repo(repo, services_path)

    # Generate AI tool configurations
    _generate_ai_configs(config, workspace_path)

    # Generate orchestration script
    _generate_orchestration_script(config, workspace_path)

    # Generate dependency and impact documentation
    _generate_documentation(config, workspace_path)

    console.print(f"[bold green]✓ Workspace ready at: {workspace_path.resolve()}[/bold green]")


def _setup_workspace_dirs(workspace_path: Path) -> None:
    """Create workspace directory structure."""
    dirs = [
        workspace_path,
        workspace_path / "services",
        workspace_path / "configs",
        workspace_path / "scripts",
    ]
    for dir_path in dirs:
        dir_path.mkdir(parents=True, exist_ok=True)
        console.print(f"[dim]✓ Created {dir_path}[/dim]")


def _process_repo(repo, services_path: Path) -> None:
    """Process a single repository: clone if needed, create symlink.

    Args:
        repo: Repo configuration
        services_path: Path to services directory
    """
    local_path = repo.resolve_local_path()
    link_path = services_path / repo.name

    # Clone if repo doesn't exist
    if not local_path.exists():
        console.print(f"[yellow]Cloning {repo.name}...[/yellow]")
        try:
            subprocess.run(
                ["git", "clone", repo.url, str(local_path)],
                check=True,
                capture_output=True,
            )
            console.print(f"[green]✓ Cloned {repo.name}[/green]")
        except subprocess.CalledProcessError as e:
            console.print(f"[red]✗ Failed to clone {repo.name}: {e}[/red]")
            raise
    else:
        console.print(f"[dim]→ {repo.name} already exists at {local_path}[/dim]")

    # Create symlink
    if link_path.exists():
        link_path.unlink()
    link_path.symlink_to(local_path)
    console.print(f"[dim]✓ Linked {repo.name} → {local_path}[/dim]")


def _generate_ai_configs(config: LoomConfig, workspace_path: Path) -> None:
    """Generate AI tool configurations.

    Args:
        config: LoomConfig
        workspace_path: Target workspace path
    """
    console.print("[blue]Generating AI tool configurations...[/blue]")

    # Claude Code
    if config.ai_tools and config.ai_tools.claude_code:
        content = generate_claude_code(config)
        file_path = workspace_path / ".claudecode.md"
        file_path.write_text(content)
        console.print(f"[green]✓ Generated .claudecode.md[/green]")

    # Codex
    if config.ai_tools and config.ai_tools.codex:
        content = generate_codex(config)
        codex_dir = workspace_path / ".codex-plugin"
        codex_dir.mkdir(exist_ok=True)
        (codex_dir / "loom-context.md").write_text(content)
        console.print(f"[green]✓ Generated .codex-plugin/loom-context.md[/green]")

    # Cursor
    if config.ai_tools and config.ai_tools.cursor:
        content = generate_cursor(config)
        file_path = workspace_path / ".cursorrules"
        file_path.write_text(content)
        console.print(f"[green]✓ Generated .cursorrules[/green]")

    # Aider
    if config.ai_tools and config.ai_tools.aider:
        content = generate_aider(config)
        file_path = workspace_path / "AGENTS.md"
        file_path.write_text(content)
        console.print(f"[green]✓ Generated AGENTS.md[/green]")


def _generate_orchestration_script(config: LoomConfig, workspace_path: Path) -> None:
    """Generate bash orchestration script.

    Args:
        config: LoomConfig
        workspace_path: Target workspace path
    """
    script_content = _build_orchestration_script(config)
    script_path = workspace_path / "scripts" / "loom"
    script_path.write_text(script_content)
    script_path.chmod(0o755)
    console.print(f"[green]✓ Generated scripts/loom[/green]")


def _build_orchestration_script(config: LoomConfig) -> str:
    """Build bash orchestration script content with per-repo install/test commands."""
    # Build per-repo install/test command mappings
    install_cmds = {}
    test_cmds = {}
    for repo in config.repos:
        if repo.install_command:
            install_cmds[repo.name] = repo.install_command
        if repo.test_command:
            test_cmds[repo.name] = repo.test_command

    repo_list = " ".join(f"services/{repo.name}" for repo in config.repos)

    lines = [
        "#!/bin/bash",
        "# Generated by loom — do not edit",
        "",
        "set -e",
        "",
        "SCRIPT_DIR=\"$(cd \"$(dirname \"${BASH_SOURCE[0]}\")\" && pwd)\"",
        "WORKSPACE_DIR=\"$(dirname \"$SCRIPT_DIR\")\"",
        f"REPOS=\"{repo_list}\"",
        "",
        "# Install commands per repo",
    ]

    for repo_name, cmd in install_cmds.items():
        # Escape single quotes in command
        safe_cmd = cmd.replace("'", "'\\''")
        lines.append(f"install_{repo_name.replace('-', '_')}='{safe_cmd}'")

    lines.extend([
        "",
        "# Test commands per repo",
    ])

    for repo_name, cmd in test_cmds.items():
        safe_cmd = cmd.replace("'", "'\\''")
        lines.append(f"test_{repo_name.replace('-', '_')}='{safe_cmd}'")

    lines.extend([
        "",
        "case \"${1:-help}\" in",
        "  install)",
        "    for repo in $REPOS; do",
        "      repo_short=${repo##*/}",
        "      repo_var=install_${repo_short//-/_}",
        "      if [ -n \"${!repo_var}\" ]; then",
        "        echo \"[*] Installing $repo...\"",
        "        (cd \"$WORKSPACE_DIR/$repo\" && eval \"${!repo_var}\" || true)",
        "      fi",
        "    done",
        "    ;;",
        "  test)",
        "    for repo in $REPOS; do",
        "      repo_short=${repo##*/}",
        "      repo_var=test_${repo_short//-/_}",
        "      if [ -n \"${!repo_var}\" ]; then",
        "        echo \"[*] Testing $repo...\"",
        "        (cd \"$WORKSPACE_DIR/$repo\" && eval \"${!repo_var}\" || true)",
        "      fi",
        "    done",
        "    ;;",
        "  status)",
        "    for repo in $REPOS; do",
        "      echo \"[*] Status of $repo:\"",
        "      (cd \"$WORKSPACE_DIR/$repo\" && git status --short || true)",
        "    done",
        "    ;;",
        "  help|--help|-h)",
        "    echo \"usage: loom <command>\"",
        "    echo \"commands:\"",
        "    echo \"  install  - Install all repositories\"",
        "    echo \"  test     - Test all repositories\"",
        "    echo \"  status   - Git status of all repositories\"",
        "    echo \"  help     - Show this help message\"",
        "    ;;",
        "  *)",
        "    echo \"Unknown command: $1\"",
        "    exec \"$0\" help",
        "    ;;",
        "esac",
    ])

    return "\n".join(lines)


def _generate_documentation(config: LoomConfig, workspace_path: Path) -> None:
    """Generate dependency and impact documentation.

    Args:
        config: LoomConfig
        workspace_path: Target workspace path
    """
    # Generate dependency graph JSON
    dependency_graph = {
        "workspace": config.name,
        "repos": [repo.name for repo in config.repos],
        "dependencies": [
            {
                "from": dep.from_repo,
                "to": dep.to_repo,
                "description": dep.description,
            }
            for dep in (config.dependencies or [])
        ],
        "impact_zones": [
            {
                "id": zone.id,
                "name": zone.name,
                "risk": zone.risk.value,
                "trigger": zone.trigger,
            }
            for zone in (config.impact_zones or [])
        ],
    }

    import json

    config_dir = workspace_path / "configs"
    (config_dir / "dependency-graph.json").write_text(
        json.dumps(dependency_graph, indent=2)
    )
    console.print(f"[green]✓ Generated configs/dependency-graph.json[/green]")
