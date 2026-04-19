"""Generator for Claude Code session templates."""

import json

from loom.config import LoomConfig


def generate_session_templates(config: LoomConfig) -> str:
    """Generate .claude/session-templates.json with workflow templates.

    Returns JSON with predefined session templates for common workflows.

    Args:
        config: LoomConfig

    Returns:
        str: JSON content for session-templates.json
    """
    templates = {
        "workspace": config.name,
        "templates": [],
    }

    # Generic templates (always included)
    templates["templates"].extend([
        {
            "name": "Full Stack Testing",
            "description": "Run tests across all repositories",
            "affected_repos": [repo.name for repo in config.repos if repo.test_command],
            "pre_checks": [
                "git status --short (verify all repos clean)",
                "loom pull (sync with remote)",
            ],
            "steps": [
                "cd services/{repo_name} && {test_command}",
            ],
            "post_checks": [
                "Review test results",
                "Check git status",
            ],
        },
        {
            "name": "Setup Workspace",
            "description": "Fresh installation of all repositories",
            "affected_repos": [repo.name for repo in config.repos if repo.install_command],
            "pre_checks": [
                "Verify all repos are cloned",
            ],
            "steps": [
                "cd services/{repo_name} && {install_command}",
            ],
            "post_checks": [
                "loom doctor (run health checks)",
                "loom test-all (verify installations)",
            ],
        },
        {
            "name": "Synchronized Commit",
            "description": "Commit changes across multiple dirty repositories",
            "affected_repos": [repo.name for repo in config.repos],
            "pre_checks": [
                "loom status (review all changes)",
                "Verify commit message is clear",
            ],
            "steps": [
                "loom sync-commit 'your commit message'",
                "git push (from meta-workspace root)",
            ],
            "post_checks": [
                "Verify commits appeared on remote",
                "Check GitHub for any CI failures",
            ],
        },
    ])

    # HIGH-risk zone templates
    for zone in config.impact_zones or []:
        if zone.risk.value == "HIGH":
            affected_repos = set()
            if zone.source and zone.source.repo:
                affected_repos.add(zone.source.repo)
            if zone.target and zone.target.repo:
                affected_repos.add(zone.target.repo)

            templates["templates"].append({
                "name": f"Update: {zone.name}",
                "description": f"Workflow for {zone.trigger}",
                "zone_id": zone.id,
                "risk": "HIGH",
                "affected_repos": list(affected_repos),
                "pre_checks": [
                    "Read impact zone description",
                    f"Run tests in: {', '.join(affected_repos)}",
                    "Verify shared environment variables are set",
                ] + (
                    [f"Check shared_env: {', '.join(zone.shared_env)}"]
                    if zone.shared_env
                    else []
                ),
                "steps": [
                    "Make changes in source repo",
                    "Run tests in affected repos",
                    "loom sync-commit 'describe your change'",
                ],
                "post_checks": [
                    "Wait for CI on all repos",
                    "Verify downstream repos still pass tests",
                    "Post in team channel about the change",
                ],
            })

    return json.dumps(templates, indent=2)
