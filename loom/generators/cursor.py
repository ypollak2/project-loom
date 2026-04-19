"""Generator for Cursor AI tool configuration (.cursorrules)."""

from loom.config import LoomConfig


def generate_cursor(config: LoomConfig) -> str:
    """Generate .cursorrules for Cursor IDE.

    Returns:
        str: Markdown content for .cursorrules
    """
    parts = [
        f"# Project Loom — {config.name}\n\n",
        f"{config.description}\n\n",
        "## Multi-Repo Rules\n\n",
        _generate_repo_ownership(config),
        "\n",
        _generate_impact_zone_rules(config),
        "\n",
        _generate_command_rules(config),
    ]
    return "".join(parts)


def _generate_repo_ownership(config: LoomConfig) -> str:
    """Generate file ownership rules per repository."""
    lines = ["### File Ownership\n"]

    for repo in config.repos:
        local_path = repo.resolve_local_path()
        lines.append(f"\n`{local_path}/**/*` - **{repo.name}** ({repo.role})")
        lines.append(f"  - Language: {repo.language.value}")
        lines.append(f"  - Primary owner: {repo.name} team")

    return "\n".join(lines)


def _generate_impact_zone_rules(config: LoomConfig) -> str:
    """Generate rules for impact zones."""
    lines = ["### Impact Zone Rules\n"]

    if not config.impact_zones:
        lines.append("\nNo impact zones defined.")
        return "\n".join(lines)

    for zone in config.impact_zones:
        lines.append(f"\n#### {zone.id}: {zone.name}\n")
        lines.append(f"**Risk**: {zone.risk.value}\n")

        if zone.source:
            if zone.source.file:
                lines.append(f"- Source: `{zone.source.file}`")
            if zone.source.function:
                lines.append(f"- Source function: `{zone.source.function}()`")

        if zone.target:
            if zone.target.file:
                lines.append(f"- Target: `{zone.target.file}`")
            if zone.target.function:
                lines.append(f"- Target function: `{zone.target.function}()`")
            if zone.target.tool:
                lines.append(f"- Target tool: `{zone.target.tool}`")

        lines.append(f"- Trigger: {zone.trigger}")
        if zone.status:
            lines.append(f"- Status: {zone.status}")

    return "\n".join(lines)


def _generate_command_rules(config: LoomConfig) -> str:
    """Generate command reference rules."""
    lines = ["### Essential Commands\n"]

    lines.append("\n```bash")
    lines.append("# Workspace setup and maintenance")
    lines.append("loom install          # Install all dependencies")
    lines.append("loom test-all         # Run tests in all repos")
    lines.append("loom doctor           # Health check all repos")
    lines.append("loom status           # Git status all repos")
    lines.append("loom logs             # Last 10 commits all repos")
    lines.append("loom diff             # Git diff summary all repos")
    lines.append("loom sync-commit MSG  # Synchronized commit across dirty repos")
    lines.append("```")

    return "\n".join(lines)
