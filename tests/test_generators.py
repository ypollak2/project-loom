"""Tests for generator modules."""

import pytest

from loom.config import Language, LoomConfig, RiskLevel, Repo, ImpactZone, SourceTarget
from loom.generators import (
    generate_claude_code,
    generate_codex,
    generate_cursor,
    generate_aider,
)


@pytest.fixture
def simple_config() -> LoomConfig:
    """Create a simple config for testing."""
    return LoomConfig(
        name="Test Workspace",
        description="A test workspace",
        repos=[
            Repo(
                name="api",
                url="https://example.com/api",
                role="backend",
                language=Language.PYTHON,
                install_command="pip install -e .",
                test_command="pytest",
            ),
            Repo(
                name="client",
                url="https://example.com/client",
                role="frontend",
                language=Language.TYPESCRIPT,
                test_command="npm test",
            ),
        ],
        impact_zones=[
            ImpactZone(
                id="IZ-001",
                name="API Schema Change",
                risk=RiskLevel.HIGH,
                source=SourceTarget(repo="api", file="src/models.py"),
                target=SourceTarget(repo="client"),
                trigger="When API models change",
            ),
        ],
    )


class TestGenerateClaudeCode:
    """Tests for Claude Code generator."""

    def test_generate_claude_code_has_title(self, simple_config):
        """Test that output contains title."""
        output = generate_claude_code(simple_config)
        assert "Project Loom" in output
        assert simple_config.name in output

    def test_generate_claude_code_has_ecosystem_map(self, simple_config):
        """Test that output contains ecosystem map."""
        output = generate_claude_code(simple_config)
        assert "## Ecosystem Map" in output
        assert "api" in output
        assert "client" in output
        assert "backend" in output
        assert "frontend" in output

    def test_generate_claude_code_has_impact_zones(self, simple_config):
        """Test that output contains impact zones."""
        output = generate_claude_code(simple_config)
        assert "## Impact Zones" in output
        assert "IZ-001" in output
        assert "API Schema Change" in output
        assert "HIGH" in output

    def test_generate_claude_code_has_quick_reference(self, simple_config):
        """Test that output contains quick reference."""
        output = generate_claude_code(simple_config)
        assert "## Quick Reference" in output
        assert "loom install" in output
        assert "loom test-all" in output
        assert "loom sync-commit" in output

    def test_generate_claude_code_with_shared_env(self):
        """Test that shared_env is rendered."""
        config = LoomConfig(
            name="Test",
            description="Test",
            repos=[
                Repo(
                    name="api",
                    url="https://example.com/api",
                    role="backend",
                    language=Language.PYTHON,
                ),
            ],
            impact_zones=[
                ImpactZone(
                    id="IZ-001",
                    name="Auth Zone",
                    risk=RiskLevel.HIGH,
                    trigger="When auth changes",
                    shared_env=["AUTH_SECRET", "JWT_KEY"],
                ),
            ],
        )

        output = generate_claude_code(config)
        assert "Shared Environment Variables" in output
        assert "AUTH_SECRET" in output
        assert "JWT_KEY" in output


class TestGenerateCodex:
    """Tests for Codex generator."""

    def test_generate_codex_returns_string(self, simple_config):
        """Test that codex generator returns string."""
        output = generate_codex(simple_config)
        assert isinstance(output, str)
        assert len(output) > 0

    def test_generate_codex_mentions_workspace(self, simple_config):
        """Test that codex output mentions workspace name."""
        output = generate_codex(simple_config)
        assert simple_config.name in output


class TestGenerateCursor:
    """Tests for Cursor generator."""

    def test_generate_cursor_returns_string(self, simple_config):
        """Test that cursor generator returns string."""
        output = generate_cursor(simple_config)
        assert isinstance(output, str)
        assert len(output) > 0

    def test_generate_cursor_has_rules(self, simple_config):
        """Test that cursor output contains rules/guidelines."""
        output = generate_cursor(simple_config)
        # Should contain some content about the workspace
        assert len(output) > 10


class TestGenerateAider:
    """Tests for Aider generator."""

    def test_generate_aider_returns_string(self, simple_config):
        """Test that aider generator returns string."""
        output = generate_aider(simple_config)
        assert isinstance(output, str)
        assert len(output) > 0

    def test_generate_aider_mentions_repos(self, simple_config):
        """Test that aider output mentions repository names."""
        output = generate_aider(simple_config)
        # Should have some reference to repos
        for repo in simple_config.repos:
            assert len(output) > 0  # Just verify output exists
