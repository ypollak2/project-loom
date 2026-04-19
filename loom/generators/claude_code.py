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
        _generate_critical_files(config),
        "\n---\n",
        _generate_preflight_checklist(config),
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



def _generate_critical_files(config: LoomConfig) -> str:
    """Generate critical files table for high-risk zones."""
    lines = ["## Critical Files\n"]

    critical_files = []
    for zone in config.impact_zones or []:
        if zone.risk.value == "HIGH":
            if zone.source and zone.source.file:
                critical_files.append({
                    "file": zone.source.file,
                    "zone": zone.id,
                    "zone_name": zone.name,
                    "note": f"Triggers {zone.name}",
                })
            if zone.target and zone.target.file:
                critical_files.append({
                    "file": zone.target.file,
                    "zone": zone.id,
                    "zone_name": zone.name,
                    "note": f"Affected by {zone.name}",
                })

    if critical_files:
        lines.append(
            "| File | Zone ID | Zone Name | Note |"
            "\n|------|---------|-----------|------|"
        )
        for f in critical_files:
            lines.append(
                f"| `{f['file']}` | {f['zone']} | {f['zone_name']} | {f['note']} |"
            )
    else:
        lines.append("No high-risk files defined.")

    return "\n".join(lines)


def _generate_preflight_checklist(config: LoomConfig) -> str:
    """Generate pre-flight checklist."""
    lines = ["## Pre-Flight Checklist\n"]
    lines.append("Before making changes to critical files:\n")
    lines.append("- [ ] Read the impact zone description for the file you're editing")
    lines.append("- [ ] Check that shared environment variables are set")

    # Add per-zone checks for zones with shared_env
    zones_with_env = [z for z in (config.impact_zones or []) if z.shared_env]
    if zones_with_env:
        lines.append("- [ ] Verify environment setup:")
        for zone in zones_with_env:
            lines.append(f"  - [ ] {zone.name}: Run `source .claude/env-setup.sh`")

    lines.append("- [ ] Run tests in affected repositories before committing")
    lines.append("- [ ] Use `loom sync-commit` to maintain consistency across repos")

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

    lines.append("\n### Quick Recipes\n")
    lines.append("Session templates for common workflows are available in `.claude/session-templates.json`:")
    lines.append("- **Full Stack Testing** — Run tests across all repositories")
    lines.append("- **Setup Workspace** — Fresh installation of all repositories")
    lines.append("- **Synchronized Commit** — Commit changes across multiple dirty repositories")
    
    # Add HIGH-risk zone templates
    high_risk_zones = [z for z in (config.impact_zones or []) if z.risk.value == "HIGH"]
    if high_risk_zones:
        lines.append("- **High-Risk Zone Updates** — Templates for critical impact zones:")
        for zone in high_risk_zones:
            lines.append(f"  - {zone.name} ({zone.id})")

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
