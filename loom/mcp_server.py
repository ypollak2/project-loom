"""MCP server for Project Loom — exposes workspace tools to Claude Code."""

import json
import subprocess
from pathlib import Path

from fastmcp import FastMCP
from pydantic import BaseModel

from loom.analyzer import find_dependents, get_impact_zones
from loom.config import LoomConfig

server = FastMCP("loom")


class MCPTool(BaseModel):
    """Base model for MCP tool responses."""

    success: bool
    data: dict | list | str
    error: str | None = None


def load_config(yaml_path: str) -> LoomConfig:
    """Load LoomConfig from YAML file."""
    return LoomConfig.load_yaml(yaml_path)


@server.tool()
def loom_get_impact_zones(file: str, yaml_path: str) -> str:
    """Get impact zones affected by a file.

    Args:
        file: File path (e.g., src/auth.py)
        yaml_path: Path to loom.yaml

    Returns:
        JSON string with impact zones that touch this file
    """
    try:
        config = load_config(yaml_path)
        zones = get_impact_zones(config, file)

        return json.dumps({
            "success": True,
            "file": file,
            "zones": zones,
            "count": len(zones),
        })
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
        })


@server.tool()
def loom_find_dependents(repo: str, function: str = None, yaml_path: str = None) -> str:
    """Find repositories that depend on a repo or function.

    Args:
        repo: Repository name
        function: Optional function name
        yaml_path: Path to loom.yaml

    Returns:
        JSON string with dependent repos and files
    """
    try:
        config = load_config(yaml_path)
        dependents = find_dependents(config, repo)

        return json.dumps({
            "success": True,
            "repo": repo,
            "function": function,
            "dependents": dependents,
            "count": len(dependents),
        })
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
        })


@server.tool()
def loom_validate_change(file: str, change_type: str = "modify", yaml_path: str = None) -> str:
    """Validate a change and get safety assessment.

    Args:
        file: File path that will be changed
        change_type: Type of change (modify, delete, add)
        yaml_path: Path to loom.yaml

    Returns:
        JSON string with safety assessment and test recommendations
    """
    try:
        config = load_config(yaml_path)

        # Find affected zones
        affected_zones = []
        affected_repos = set()

        for zone in config.impact_zones or []:
            if zone.source and zone.source.file and file.endswith(zone.source.file):
                affected_zones.append(zone)
                if zone.target and zone.target.repo:
                    affected_repos.add(zone.target.repo)
            elif zone.target and zone.target.file and file.endswith(zone.target.file):
                affected_zones.append(zone)
                if zone.source and zone.source.repo:
                    affected_repos.add(zone.source.repo)

        # Determine risk level
        max_risk = "LOW"
        if affected_zones:
            risk_order = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}
            max_risk = max(
                [zone.risk.value for zone in affected_zones],
                key=lambda x: risk_order.get(x, 0),
            )

        return json.dumps({
            "success": True,
            "file": file,
            "change_type": change_type,
            "safe": len(affected_zones) == 0,
            "risk_level": max_risk,
            "affected_zones": [
                {"id": z.id, "name": z.name, "risk": z.risk.value}
                for z in affected_zones
            ],
            "affected_repos": list(affected_repos),
            "tests_to_run": [
                r.name
                for r in config.repos
                if r.name in affected_repos and r.test_command
            ],
            "shared_env_required": list(set(
                env
                for zone in affected_zones
                for env in (zone.shared_env or [])
            )),
        })
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
        })


@server.tool()
def loom_workspace_status(yaml_path: str) -> str:
    """Get current workspace status: git state and repo health.

    Args:
        yaml_path: Path to loom.yaml

    Returns:
        JSON string with git status and health info for all repos
    """
    try:
        config = load_config(yaml_path)

        repos_status = []
        for repo in config.repos:
            local_path = repo.resolve_local_path()

            if not local_path.exists():
                repos_status.append({
                    "name": repo.name,
                    "status": "not_cloned",
                    "branch": None,
                    "dirty": False,
                    "unpushed": 0,
                })
                continue

            # Get git status
            branch_result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=local_path,
                capture_output=True,
                text=True,
            )
            branch = branch_result.stdout.strip() if branch_result.returncode == 0 else "unknown"

            status_result = subprocess.run(
                ["git", "status", "--short"],
                cwd=local_path,
                capture_output=True,
                text=True,
            )
            dirty = bool(status_result.stdout.strip())

            unpushed_result = subprocess.run(
                ["git", "log", "--oneline", "@{u}.."],
                cwd=local_path,
                capture_output=True,
                text=True,
            )
            unpushed = len([l for l in unpushed_result.stdout.strip().split("\n") if l])

            repos_status.append({
                "name": repo.name,
                "status": "cloned",
                "branch": branch,
                "dirty": dirty,
                "unpushed": unpushed,
            })

        return json.dumps({
            "success": True,
            "workspace": config.name,
            "repos": repos_status,
            "summary": {
                "total": len(config.repos),
                "cloned": sum(1 for r in repos_status if r["status"] == "cloned"),
                "dirty": sum(1 for r in repos_status if r["dirty"]),
                "unpushed": sum(r["unpushed"] for r in repos_status),
            },
        })
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
        })


@server.tool()
def loom_run_affected_tests(file: str, yaml_path: str) -> str:
    """Run tests in repositories affected by a file change.

    Args:
        file: File path that was changed
        yaml_path: Path to loom.yaml

    Returns:
        JSON string with test results
    """
    try:
        config = load_config(yaml_path)

        # Find affected repos
        affected_repos = set()
        for zone in config.impact_zones or []:
            if zone.source and zone.source.file and file.endswith(zone.source.file):
                if zone.target and zone.target.repo:
                    affected_repos.add(zone.target.repo)
            elif zone.target and zone.target.file and file.endswith(zone.target.file):
                if zone.source and zone.source.repo:
                    affected_repos.add(zone.source.repo)

        results = []
        for repo_name in sorted(affected_repos):
            repo = next((r for r in config.repos if r.name == repo_name), None)
            if not repo or not repo.test_command:
                continue

            local_path = repo.resolve_local_path()
            if not local_path.exists():
                results.append({
                    "repo": repo_name,
                    "status": "not_cloned",
                })
                continue

            result = subprocess.run(
                repo.test_command,
                shell=True,
                cwd=local_path,
                capture_output=True,
            )

            results.append({
                "repo": repo_name,
                "status": "passed" if result.returncode == 0 else "failed",
                "command": repo.test_command,
            })

        return json.dumps({
            "success": True,
            "file": file,
            "results": results,
            "passed": sum(1 for r in results if r["status"] == "passed"),
            "failed": sum(1 for r in results if r["status"] == "failed"),
        })
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
        })


@server.tool()
def loom_get_session_template(name: str, yaml_path: str) -> str:
    """Get a session template by name.

    Args:
        name: Template name (e.g., "Full Stack Testing", "Setup Workspace")
        yaml_path: Path to loom.yaml

    Returns:
        JSON string with template details (steps, checks, etc.)
    """
    try:
        from loom.generators import generate_session_templates

        config = load_config(yaml_path)
        templates_json = generate_session_templates(config)
        templates_data = json.loads(templates_json)

        for template in templates_data.get("templates", []):
            if template.get("name") == name:
                return json.dumps({
                    "success": True,
                    "template": template,
                })

        return json.dumps({
            "success": False,
            "error": f"Template '{name}' not found",
        })
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
        })


def start_server(config_path: str) -> None:
    """Start the MCP server with config already loaded.

    Args:
        config_path: Path to loom.yaml configuration
    """
    # Store config path in server context
    server.config_path = config_path
    server.run()
