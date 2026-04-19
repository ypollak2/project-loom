"""Tests for loom.analyzer module."""


from loom.analyzer import blast_radius, check_boundaries, find_dependents, get_impact_zones, trace_chain
from loom.config import (
    Boundary,
    Dependency,
    ImpactZone,
    Language,
    LoomConfig,
    Repo,
    RiskLevel,
    SourceTarget,
)


class TestGetImpactZones:
    """Tests for get_impact_zones function."""

    def test_file_matching_source(self):
        """Test finding zones where file matches source."""
        config = LoomConfig(
            name="Test",
            description="Test",
            repos=[
                Repo(name="api", url="https://example.com/api", role="api", language=Language.PYTHON),
                Repo(name="client", url="https://example.com/client", role="client", language=Language.TYPESCRIPT),
            ],
            impact_zones=[
                ImpactZone(
                    id="IZ-001",
                    name="Auth Change",
                    risk=RiskLevel.HIGH,
                    source=SourceTarget(repo="api", file="src/auth.py"),
                    target=SourceTarget(repo="client"),
                    trigger="When auth.py is modified",
                )
            ],
        )

        zones = get_impact_zones(config, "src/auth.py")
        assert len(zones) == 1
        assert zones[0]["id"] == "IZ-001"

    def test_partial_path_match(self):
        """Test that file paths are matched with endswith."""
        config = LoomConfig(
            name="Test",
            description="Test",
            repos=[
                Repo(name="api", url="https://example.com/api", role="api", language=Language.PYTHON),
            ],
            impact_zones=[
                ImpactZone(
                    id="IZ-001",
                    name="Config Change",
                    risk=RiskLevel.MEDIUM,
                    source=SourceTarget(file="config.py"),
                    trigger="When config.py is modified",
                )
            ],
        )

        zones = get_impact_zones(config, "services/api/src/config.py")
        assert len(zones) == 1

    def test_no_matching_zones(self):
        """Test when no zones match the file."""
        config = LoomConfig(
            name="Test",
            description="Test",
            repos=[
                Repo(name="api", url="https://example.com/api", role="api", language=Language.PYTHON),
            ],
            impact_zones=[
                ImpactZone(
                    id="IZ-001",
                    name="Auth Change",
                    risk=RiskLevel.HIGH,
                    source=SourceTarget(file="auth.py"),
                    trigger="When auth.py is modified",
                )
            ],
        )

        zones = get_impact_zones(config, "utils.py")
        assert len(zones) == 0

    def test_empty_impact_zones(self):
        """Test with no impact zones configured."""
        config = LoomConfig(
            name="Test",
            description="Test",
            repos=[
                Repo(name="api", url="https://example.com/api", role="api", language=Language.PYTHON),
            ],
        )

        zones = get_impact_zones(config, "src/auth.py")
        assert len(zones) == 0


class TestFindDependents:
    """Tests for find_dependents function."""

    def test_find_direct_dependents(self):
        """Test finding direct dependents."""
        config = LoomConfig(
            name="Test",
            description="Test",
            repos=[
                Repo(name="api", url="https://example.com/api", role="api", language=Language.PYTHON),
                Repo(name="client", url="https://example.com/client", role="client", language=Language.TYPESCRIPT),
            ],
            dependencies=[
                Dependency(**{"from": "client", "to": "api", "description": "REST API"}),
            ],
        )

        dependents = find_dependents(config, "api")
        assert len(dependents) == 1
        assert dependents[0]["repo"] == "client"

    def test_with_impact_zones(self):
        """Test that impact zones are counted."""
        config = LoomConfig(
            name="Test",
            description="Test",
            repos=[
                Repo(name="api", url="https://example.com/api", role="api", language=Language.PYTHON),
                Repo(name="client", url="https://example.com/client", role="client", language=Language.TYPESCRIPT),
            ],
            dependencies=[
                Dependency(**{"from": "client", "to": "api", "description": "REST API"}),
            ],
            impact_zones=[
                ImpactZone(
                    id="IZ-001",
                    name="Auth",
                    risk=RiskLevel.HIGH,
                    source=SourceTarget(repo="client"),
                    target=SourceTarget(repo="api"),
                    trigger="When client calls auth endpoint",
                )
            ],
        )

        dependents = find_dependents(config, "api")
        assert len(dependents) == 1
        assert dependents[0]["zone_count"] == 1

    def test_no_dependents(self):
        """Test when no dependents exist."""
        config = LoomConfig(
            name="Test",
            description="Test",
            repos=[
                Repo(name="api", url="https://example.com/api", role="api", language=Language.PYTHON),
            ],
        )

        dependents = find_dependents(config, "api")
        assert len(dependents) == 0


class TestBlastRadius:
    """Tests for blast_radius function."""

    def test_score_calculation_low_risk(self):
        """Test score with LOW risk zones."""
        config = LoomConfig(
            name="Test",
            description="Test",
            repos=[
                Repo(name="api", url="https://example.com/api", role="api", language=Language.PYTHON),
            ],
            impact_zones=[
                ImpactZone(
                    id="IZ-001",
                    name="Test",
                    risk=RiskLevel.LOW,
                    source=SourceTarget(file="test.py"),
                    trigger="test",
                ),
            ],
        )

        result = blast_radius(config, "test.py")
        # 1 zone * 1 (LOW weight) = 1
        assert result["score"] == 1
        assert result["zone_count"] == 1

    def test_score_calculation_high_risk(self):
        """Test score with HIGH risk zones."""
        config = LoomConfig(
            name="Test",
            description="Test",
            repos=[
                Repo(name="api", url="https://example.com/api", role="api", language=Language.PYTHON),
            ],
            impact_zones=[
                ImpactZone(
                    id="IZ-001",
                    name="Test",
                    risk=RiskLevel.HIGH,
                    source=SourceTarget(file="test.py"),
                    trigger="test",
                ),
                ImpactZone(
                    id="IZ-002",
                    name="Test 2",
                    risk=RiskLevel.HIGH,
                    source=SourceTarget(file="test.py"),
                    trigger="test",
                ),
            ],
        )

        result = blast_radius(config, "test.py")
        # 2 zones * 5 (HIGH weight) = 10, capped at 10
        assert result["score"] == 10

    def test_score_capped_at_10(self):
        """Test that score is capped at 10."""
        zones = [
            ImpactZone(
                id=f"IZ-{i:03d}",
                name=f"Zone {i}",
                risk=RiskLevel.HIGH,
                source=SourceTarget(file="test.py"),
                trigger="test",
            )
            for i in range(5)
        ]

        config = LoomConfig(
            name="Test",
            description="Test",
            repos=[
                Repo(name="api", url="https://example.com/api", role="api", language=Language.PYTHON),
            ],
            impact_zones=zones,
        )

        result = blast_radius(config, "test.py")
        # 5 zones * 5 (HIGH weight) = 25, but capped at 10
        assert result["score"] == 10

    def test_affected_repos(self):
        """Test affected_repos extraction."""
        config = LoomConfig(
            name="Test",
            description="Test",
            repos=[
                Repo(name="api", url="https://example.com/api", role="api", language=Language.PYTHON),
                Repo(name="client", url="https://example.com/client", role="client", language=Language.TYPESCRIPT),
            ],
            impact_zones=[
                ImpactZone(
                    id="IZ-001",
                    name="Test",
                    risk=RiskLevel.LOW,
                    source=SourceTarget(repo="api", file="test.py"),
                    target=SourceTarget(repo="client"),
                    trigger="test",
                ),
            ],
        )

        result = blast_radius(config, "test.py")
        assert "api" in result["affected_repos"]
        assert "client" in result["affected_repos"]

    def test_no_zones_zero_score(self):
        """Test score is 0 when no zones match."""
        config = LoomConfig(
            name="Test",
            description="Test",
            repos=[
                Repo(name="api", url="https://example.com/api", role="api", language=Language.PYTHON),
            ],
        )

        result = blast_radius(config, "test.py")
        assert result["score"] == 0


class TestTraceChain:
    """Tests for trace_chain function."""

    def test_linear_chain(self):
        """Test tracing a linear dependency chain."""
        config = LoomConfig(
            name="Test",
            description="Test",
            repos=[
                Repo(name="api", url="https://example.com/api", role="api", language=Language.PYTHON),
                Repo(name="gateway", url="https://example.com/gateway", role="gateway", language=Language.GO),
                Repo(name="client", url="https://example.com/client", role="client", language=Language.TYPESCRIPT),
            ],
            dependencies=[
                Dependency(**{"from": "gateway", "to": "api", "description": "Calls API"}),
                Dependency(**{"from": "client", "to": "gateway", "description": "Calls Gateway"}),
            ],
        )

        result = trace_chain(config, "client")
        # Should follow client -> gateway -> api
        assert result["chain"] == ["client", "gateway", "api"]

    def test_no_dependencies(self):
        """Test chain with no dependencies."""
        config = LoomConfig(
            name="Test",
            description="Test",
            repos=[
                Repo(name="api", url="https://example.com/api", role="api", language=Language.PYTHON),
            ],
        )

        result = trace_chain(config, "api")
        assert result["chain"] == ["api"]

    def test_zones_along_chain(self):
        """Test impact zones along chain."""
        config = LoomConfig(
            name="Test",
            description="Test",
            repos=[
                Repo(name="api", url="https://example.com/api", role="api", language=Language.PYTHON),
                Repo(name="gateway", url="https://example.com/gateway", role="gateway", language=Language.GO),
            ],
            dependencies=[
                Dependency(**{"from": "gateway", "to": "api", "description": "Calls API"}),
            ],
            impact_zones=[
                ImpactZone(
                    id="IZ-001",
                    name="Auth",
                    risk=RiskLevel.HIGH,
                    source=SourceTarget(repo="gateway"),
                    target=SourceTarget(repo="api"),
                    trigger="When gateway calls auth endpoint",
                )
            ],
        )

        result = trace_chain(config, "gateway")
        assert len(result["impact_zones"]) == 1
        assert result["impact_zones"][0]["id"] == "IZ-001"


class TestCheckBoundaries:
    """Tests for check_boundaries function."""

    def test_find_matching_boundary(self):
        """Test finding a matching boundary."""
        config = LoomConfig(
            name="Test",
            description="Test",
            repos=[
                Repo(name="api", url="https://example.com/api", role="api", language=Language.PYTHON),
                Repo(name="client", url="https://example.com/client", role="client", language=Language.TYPESCRIPT),
            ],
            boundaries=[
                Boundary(
                    from_repo="client",
                    to_repo="api",
                    interface="REST API",
                    protocol="HTTP",
                    test_command="pytest tests/integration",
                )
            ],
        )

        boundaries = check_boundaries(config, "client", "api")
        assert len(boundaries) == 1
        assert boundaries[0]["interface"] == "REST API"

    def test_no_matching_boundary(self):
        """Test when no boundary exists."""
        config = LoomConfig(
            name="Test",
            description="Test",
            repos=[
                Repo(name="api", url="https://example.com/api", role="api", language=Language.PYTHON),
            ],
        )

        boundaries = check_boundaries(config, "client", "api")
        assert len(boundaries) == 0

    def test_boundary_optional_test_command(self):
        """Test boundary with no test_command."""
        config = LoomConfig(
            name="Test",
            description="Test",
            repos=[
                Repo(name="api", url="https://example.com/api", role="api", language=Language.PYTHON),
                Repo(name="client", url="https://example.com/client", role="client", language=Language.TYPESCRIPT),
            ],
            boundaries=[
                Boundary(
                    from_repo="client",
                    to_repo="api",
                    interface="REST API",
                    protocol="HTTP",
                )
            ],
        )

        boundaries = check_boundaries(config, "client", "api")
        assert len(boundaries) == 1
        assert boundaries[0]["test_command"] is None
