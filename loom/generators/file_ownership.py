"""Generator for file ownership and risk mapping."""

import json

from loom.config import LoomConfig


def generate_file_ownership(config: LoomConfig) -> str:
    """Generate .claude/file-ownership.json for Claude Code.

    Returns JSON mapping files to impact zones and risk levels.

    Returns:
        str: JSON content for file-ownership.json
    """
    ownership = {
        "workspace": config.name,
        "generated_at": "",  # Will be set by workspace.py
        "files": [],
    }

    # Process each impact zone
    for zone in config.impact_zones or []:
        # Get source files
        if zone.source and zone.source.file:
            source_repo = zone.source.repo or ""
            source_file = zone.source.file

            ownership["files"].append({
                "glob": f"services/{source_repo}/{source_file}" if source_repo else f"**/{source_file}",
                "owner_repo": source_repo,
                "risk": zone.risk.value,
                "impact_zones": [zone.id],
                "notes": f"Part of {zone.name}",
            })

        # Get target files
        if zone.target and zone.target.file:
            target_repo = zone.target.repo or ""
            target_file = zone.target.file

            ownership["files"].append({
                "glob": f"services/{target_repo}/{target_file}" if target_repo else f"**/{target_file}",
                "owner_repo": target_repo,
                "risk": zone.risk.value,
                "impact_zones": [zone.id],
                "notes": f"Affected by {zone.name}",
            })

    return json.dumps(ownership, indent=2)
