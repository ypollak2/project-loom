"""Impact analysis functions for cross-repo dependencies."""

from loom.config import LoomConfig, RiskLevel


def get_impact_zones(config: LoomConfig, file: str) -> list[dict]:
    """Get impact zones affected by a file.

    Args:
        config: LoomConfig instance
        file: File path (e.g., src/auth.py)

    Returns:
        List of impact zone dicts affecting this file
    """
    affected_zones = []
    for zone in config.impact_zones or []:
        touches_file = False

        # Check source
        if zone.source and zone.source.file and file.endswith(zone.source.file):
            touches_file = True

        # Check target
        if zone.target and zone.target.file and file.endswith(zone.target.file):
            touches_file = True

        if touches_file:
            affected_zones.append({
                "id": zone.id,
                "name": zone.name,
                "risk": zone.risk.value,
                "trigger": zone.trigger,
                "source": {
                    "repo": zone.source.repo if zone.source else None,
                    "file": zone.source.file if zone.source else None,
                } if zone.source else None,
                "target": {
                    "repo": zone.target.repo if zone.target else None,
                    "file": zone.target.file if zone.target else None,
                } if zone.target else None,
                "shared_env": zone.shared_env or [],
            })

    return affected_zones


def find_dependents(config: LoomConfig, repo: str) -> list[dict]:
    """Find repositories that depend on a given repo.

    Args:
        config: LoomConfig instance
        repo: Repository name

    Returns:
        List of dependent repo dicts with impact zone counts
    """
    dependents = []
    for dep in config.dependencies or []:
        if dep.to_repo == repo:
            # Find impact zones for this dependency
            zones_for_dep = []
            for zone in config.impact_zones or []:
                if zone.source and zone.source.repo == dep.from_repo:
                    if zone.target and zone.target.repo == dep.to_repo:
                        zones_for_dep.append(zone.id)

            dependents.append({
                "repo": dep.from_repo,
                "dependency_description": dep.description,
                "impact_zones": zones_for_dep,
                "zone_count": len(zones_for_dep),
            })

    return dependents


def blast_radius(config: LoomConfig, file: str) -> dict:
    """Calculate impact blast radius for a file.

    Computes score based on: number of impact zones × risk weight,
    capped at 10. Risk weights: LOW=1, MEDIUM=3, HIGH=5.

    Args:
        config: LoomConfig instance
        file: File path

    Returns:
        Dict with zones, affected_repos, max_risk, and score (0-10)
    """
    zones = get_impact_zones(config, file)

    # Extract affected repos and max risk
    affected_repos = set()
    max_risk = RiskLevel.LOW
    risk_weights = {RiskLevel.LOW: 1, RiskLevel.MEDIUM: 3, RiskLevel.HIGH: 5}

    for zone in zones:
        if zone["source"] and zone["source"]["repo"]:
            affected_repos.add(zone["source"]["repo"])
        if zone["target"] and zone["target"]["repo"]:
            affected_repos.add(zone["target"]["repo"])

        zone_risk = RiskLevel(zone["risk"])
        if risk_weights[zone_risk] > risk_weights[max_risk]:
            max_risk = zone_risk

    # Calculate score: zone_count * max_risk_weight, capped at 10
    if zones:
        raw_score = len(zones) * risk_weights[max_risk]
        score = min(raw_score, 10)
    else:
        score = 0

    return {
        "file": file,
        "impact_zones": zones,
        "zone_count": len(zones),
        "affected_repos": sorted(affected_repos),
        "max_risk": max_risk.value,
        "score": score,
    }


def trace_chain(config: LoomConfig, repo: str) -> dict:
    """Trace transitive dependency chain for a repo.

    Args:
        config: LoomConfig instance
        repo: Repository name

    Returns:
        Dict with chain and impact zones along the path
    """
    chain = [repo]
    visited = {repo}
    current = repo

    # Follow the dependency chain
    while True:
        # Find next dependency
        next_repo = None
        dep_description = ""
        for dep in config.dependencies or []:
            if dep.from_repo == current:
                next_repo = dep.to_repo
                dep_description = dep.description
                break

        if not next_repo or next_repo in visited:
            break

        chain.append(next_repo)
        visited.add(next_repo)
        current = next_repo

    # Collect impact zones along the chain
    zones_along_chain = []
    for zone in config.impact_zones or []:
        if zone.source and zone.source.repo in chain:
            if zone.target and zone.target.repo in chain:
                zones_along_chain.append({
                    "id": zone.id,
                    "name": zone.name,
                    "risk": zone.risk.value,
                    "from": zone.source.repo,
                    "to": zone.target.repo,
                })

    return {
        "repo": repo,
        "chain": chain,
        "chain_length": len(chain),
        "impact_zones": zones_along_chain,
    }


def check_boundaries(config: LoomConfig, from_repo: str, to_repo: str) -> list[dict]:
    """Check boundaries between two repositories.

    Args:
        config: LoomConfig instance
        from_repo: Source repo name
        to_repo: Target repo name

    Returns:
        List of boundary dicts matching the repo pair
    """
    matching = []
    for boundary in config.boundaries or []:
        if boundary.from_repo == from_repo and boundary.to_repo == to_repo:
            matching.append({
                "from_repo": boundary.from_repo,
                "to_repo": boundary.to_repo,
                "interface": boundary.interface,
                "protocol": boundary.protocol,
                "test_command": boundary.test_command,
            })

    return matching
