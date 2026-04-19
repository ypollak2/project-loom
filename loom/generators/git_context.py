"""Generator for live git context about workspace state."""

import json
import subprocess
from pathlib import Path

from loom.config import LoomConfig


def generate_git_context(config: LoomConfig, workspace_path: Path) -> str:
    """Generate .claude/git-context.json with live repo state.

    Returns JSON with git status, branches, and commit info for each repo.

    Args:
        config: LoomConfig
        workspace_path: Target workspace path

    Returns:
        str: JSON content for git-context.json
    """
    context = {
        "workspace": config.name,
        "generated_at": "",  # Will be set by workspace.py
        "repos": [],
    }

    for repo in config.repos:
        local_path = repo.resolve_local_path()
        if not local_path.exists():
            context["repos"].append({
                "name": repo.name,
                "url": repo.url,
                "status": "not_cloned",
            })
            continue

        # Get current branch
        branch_result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=local_path,
            capture_output=True,
            text=True,
        )
        current_branch = branch_result.stdout.strip() if branch_result.returncode == 0 else "unknown"

        # Get latest commit hash
        commit_result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=local_path,
            capture_output=True,
            text=True,
        )
        commit_hash = commit_result.stdout.strip()[:8] if commit_result.returncode == 0 else "unknown"

        # Check if dirty
        status_result = subprocess.run(
            ["git", "status", "--short"],
            cwd=local_path,
            capture_output=True,
            text=True,
        )
        is_dirty = bool(status_result.stdout.strip())

        # Get unpushed commits count
        unpushed_result = subprocess.run(
            ["git", "log", "--oneline", "@{u}.."],
            cwd=local_path,
            capture_output=True,
            text=True,
        )
        unpushed_count = len([line for line in unpushed_result.stdout.strip().split("\n") if line])

        context["repos"].append({
            "name": repo.name,
            "url": repo.url,
            "status": "cloned",
            "branch": current_branch,
            "commit": commit_hash,
            "dirty": is_dirty,
            "unpushed": unpushed_count,
        })

    return json.dumps(context, indent=2)
