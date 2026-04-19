"""Generator for Claude Code AI tool configuration."""

from loom.config import ImpactZone, LoomConfig


def generate_claude_code(config: LoomConfig) -> str:
    """Generate .claudecode.md for Claude Code AI tool.

    Returns:
        str: Markdown content for .claudecode.md
    """
    parts = [
        "# Project Loom — AI-Ready Workspace Configuration",
        f"\n## {config.name}",
        f"\n{config.description}",
        "\n---\n",
        _generate_ecosystem_map(config),
        "\n---\n",
        _generate_dependency_graph(config),
        "\n---\n",
        _generate_impact_zones_table(config),
        "\n---\n",
        _generate_quick_reference(config),
    ]
    return "".join(parts)


def _generate_ecosystem_map(config: LoomConfig) -> str:
    """Generate ecosystem map table."""
    lines = ["## Ecosystem Map\n"]
    lines.append(
        "| Repo | Role | Language | Interface |"
        "\n|------|------|----------|-----------|"
    )

    for repo in config.repos:
        interface_parts = []
        if repo.test_command:
            interface_parts.append("test")
        if repo.install_command:
            interface_parts.append("install")
        if repo.doctor_command:
            interface_parts.append("doctor")
        interface = ", ".join(interface_parts) or "—"

        lines.append(
            f"| `{repo.name}` | {repo.role} | {repo.language.value} | {interface} |"
        )

    return "\n".join(lines)


def _generate_dependency_graph(config: LoomConfig) -> str:
    """Generate dependency graph (ASCII or table)."""
    lines = ["## Dependency Graph\n"]

    if not config.dependencies:
        lines.append("No direct dependencies defined.")
        return "\n".join(lines)

    lines.append("| From | To | Description |")
    lines.append("|------|-----|-------------|")

    for dep in config.dependencies:
        lines.append(f"| `{dep.from_repo}` | `{dep.to_repo}` | {dep.description} |")

    return "\n".join(lines)


def _generate_impact_zones_table(config: LoomConfig) -> str:
    """Generate impact zones table with shared environment section."""
    lines = ["## Impact Zones\n"]
    lines.append(
        "| ID | Name | Risk | Source | Target | Trigger |"
        "\n|-----|------|------|--------|--------|---------|"
    )

    if config.impact_zones:
        for zone in config.impact_zones:
            source = _format_location(zone.source)
            target = _format_location(zone.target)
            lines.append(
                f"| {zone.id} | {zone.name} | **{zone.risk.value}** | "
                f"{source} | {target} | {zone.trigger} |"
            )

    # Add shared environment variables section
    lines.append("\n### Shared Environment Variables\n")
    zones_with_env = [z for z in (config.impact_zones or []) if z.shared_env]

    if zones_with_env:
        for zone in zones_with_env:
            lines.append(f"**{zone.name}** ({zone.id}):\n")
            for env_var in zone.shared_env:
                lines.append(f"- `{env_var}`")
            lines.append("")
    else:
        lines.append("No shared environment variables defined.")

    return "\n".join(lines)


def _generate_quick_reference(config: LoomConfig) -> str:
    """Generate quick reference CLI commands."""
    lines = ["## Quick Reference\n"]
    lines.append("### Commands\n")
    lines.append("```bash")
    lines.append("# Install all repositories")
    lines.append("loom install")
    lines.append("")
    lines.append("# Run tests across all repositories")
    lines.append("loom test-all")
    lines.append("")
    lines.append("# Check health of all repositories")
    lines.append("loom doctor")
    lines.append("")
    lines.append("# Git status across all repositories")
    lines.append("loom status")
    lines.append("")
    lines.append("# Make a synchronized commit across all dirty repos")
    lines.append("loom sync-commit 'your commit message'")
    lines.append("```")

    lines.append("\n### Repository Paths\n")
    for repo in config.repos:
        local_path = repo.resolve_local_path()
        lines.append(f"- `{repo.name}`: `{local_path}`")

    return "\n".join(lines)


def _format_location(location) -> str:
    """Format a source/target location for display."""
    if not location:
        return "—"

    parts = []
    if location.repo:
        parts.append(f"`{location.repo}`")
    if location.file:
        parts.append(f"`{location.file}`")
    if location.function:
        parts.append(f"`{location.function}()`")
    if location.tool:
        parts.append(f"`{location.tool}`")

    return " → ".join(parts) if parts else "—"
