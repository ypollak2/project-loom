"""Generator for Codex AI tool configuration."""

from loom.config import LoomConfig


def generate_codex(config: LoomConfig) -> str:
    """Generate Codex context configuration.

    Returns:
        str: Markdown content for Codex context injection
    """
    parts = [
        f"# {config.name} — Codex Multi-Repo Context\n\n",
        f"{config.description}\n\n",
        "---\n\n",
        _generate_repo_manifest(config),
        "\n\n---\n\n",
        _generate_codex_rules(config),
    ]
    return "".join(parts)


def _generate_repo_manifest(config: LoomConfig) -> str:
    """Generate repository manifest for Codex."""
    lines = ["## Repository Manifest\n"]

    for repo in config.repos:
        lines.append(f"\n### {repo.name}\n")
        lines.append(f"- **Role**: {repo.role}")
        lines.append(f"- **URL**: {repo.url}")
        lines.append(f"- **Language**: {repo.language.value}")
        lines.append(f"- **Local Path**: `{repo.resolve_local_path()}`")

        if repo.install_command:
            lines.append(f"- **Install**: `{repo.install_command}`")
        if repo.test_command:
            lines.append(f"- **Test**: `{repo.test_command}`")
        if repo.doctor_command:
            lines.append(f"- **Health Check**: `{repo.doctor_command}`")

    return "\n".join(lines)


def _generate_codex_rules(config: LoomConfig) -> str:
    """Generate Codex-specific rules for cross-repo work."""
    lines = ["## Codex Rules for Cross-Repo Work\n"]

    lines.append("\n### Before Making Changes\n")
    lines.append("1. Check impact zones (see below)")
    lines.append("2. Run `loom doctor` to ensure both repos are healthy")
    lines.append("3. Run `loom test-all` to establish baseline")

    lines.append("\n### Impact Zones (High-Risk Areas)\n")

    if config.impact_zones:
        for zone in config.impact_zones:
            if zone.risk.value == "HIGH":
                lines.append(f"\n#### {zone.id}: {zone.name}\n")
                if zone.source:
                    lines.append(f"- **Source**: {_describe_location(zone.source)}")
                if zone.target:
                    lines.append(f"- **Target**: {_describe_location(zone.target)}")
                lines.append(f"- **Trigger**: {zone.trigger}")
                if zone.status:
                    lines.append(f"- **Status**: {zone.status}")

    lines.append("\n### After Making Changes\n")
    lines.append("1. Run tests in the modified repo")
    lines.append("2. Run `loom test-all` to verify no cross-repo regressions")
    lines.append("3. Run `loom doctor` to verify health")

    return "\n".join(lines)


def _describe_location(location) -> str:
    """Describe a source/target location in prose."""
    if not location:
        return "unknown"

    parts = []
    if location.repo:
        parts.append(f"repo `{location.repo}`")
    if location.file:
        parts.append(f"file `{location.file}`")
    if location.function:
        parts.append(f"function `{location.function}()`")
    if location.tool:
        parts.append(f"tool `{location.tool}`")

    return " → ".join(parts) if parts else "unknown"
