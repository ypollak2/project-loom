"""Generator for Aider AI tool configuration (AGENTS.md)."""

from loom.config import LoomConfig


def generate_aider(config: LoomConfig) -> str:
    """Generate AGENTS.md for Aider.

    Returns:
        str: Markdown content for AGENTS.md
    """
    parts = [
        f"# {config.name} — Agents and Tasks\n\n",
        f"{config.description}\n\n",
        "---\n\n",
        _generate_repo_map(config),
        "\n\n---\n\n",
        _generate_task_templates(config),
    ]
    return "".join(parts)


def _generate_repo_map(config: LoomConfig) -> str:
    """Generate repository map for Aider."""
    lines = ["## Repository Map\n"]

    for repo in config.repos:
        local_path = repo.resolve_local_path()
        lines.append(f"\n### {repo.name}")
        lines.append(f"- **Role**: {repo.role}")
        lines.append(f"- **Language**: {repo.language.value}")
        lines.append(f"- **Path**: `{local_path}`")
        lines.append(f"- **URL**: {repo.url}")

    return "\n".join(lines)


def _generate_task_templates(config: LoomConfig) -> str:
    """Generate task templates for common patterns."""
    lines = ["## Task Templates\n"]

    lines.append("\n### Single-Repo Tasks\n")
    lines.append("When working in a single repository, Aider automatically handles")
    lines.append("file navigation and testing within that repo.\n")
    lines.append("```bash")
    lines.append("# Open a single repo for work")
    lines.append("cd services/<repo-name>")
    lines.append("aider")
    lines.append("```")

    lines.append("\n### Cross-Repo Impact Analysis\n")
    lines.append("When changes cross repo boundaries, ensure impact zones are reviewed:\n")

    if config.impact_zones:
        lines.append("**Critical Impact Zones**:\n")
        for zone in config.impact_zones:
            if zone.risk.value in ("HIGH", "MEDIUM"):
                lines.append(f"- {zone.id}: {zone.name} ({zone.risk.value})")

    lines.append("\n### Workflow: Multi-Repo Change\n")
    lines.append("1. Identify which repos are affected")
    lines.append("2. Check impact zones for those repos")
    lines.append("3. Work in the primary repo first")
    lines.append("4. Test with `loom test-all` before changing the secondary repo")
    lines.append("5. Use `loom sync-commit` to coordinate commits\n")

    lines.append("### Workflow: Dependency Update\n")
    lines.append("When updating a shared dependency:\n")
    lines.append("1. Update in the primary (dependency-providing) repo")
    lines.append("2. Run tests in that repo")
    lines.append("3. Update consumer repos")
    lines.append("4. Run `loom test-all` to verify no breakage")
    lines.append("5. Coordinate commits with `loom sync-commit`")

    return "\n".join(lines)
