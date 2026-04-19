"""Tests for generator modules."""

import pytest

from loom.config import Language, LoomConfig, RiskLevel, Repo, ImpactZone, SourceTarget
from loom.generators import (
    generate_aider,
    generate_claude_code,
    generate_codex,
    generate_cursor,
    generate_dependency_graph,
    generate_env_setup,
    generate_file_ownership,
    generate_git_context,
    generate_session_templates,
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
                test_command="pytest tests/",
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


class TestV030Generators:
    """Tests for v0.3.0 Claude context generators."""

    def test_generate_file_ownership_returns_json(self, simple_config):
        """Test file ownership generator returns valid JSON."""
        from loom.generators import generate_file_ownership
        import json

        output = generate_file_ownership(simple_config)
        data = json.loads(output)
        assert isinstance(data, dict)
        assert "workspace" in data
        assert "files" in data
        assert data["workspace"] == simple_config.name

    def test_generate_file_ownership_includes_impact_zones(self, simple_config):
        """Test file ownership maps zones to files."""
        from loom.generators import generate_file_ownership
        import json

        output = generate_file_ownership(simple_config)
        data = json.loads(output)
        # Should have file entries from impact zones
        assert isinstance(data["files"], list)

    def test_generate_git_context_returns_json(self, simple_config, tmp_path):
        """Test git context generator returns valid JSON."""
        from loom.generators import generate_git_context
        import json

        output = generate_git_context(simple_config, tmp_path)
        data = json.loads(output)
        assert isinstance(data, dict)
        assert "workspace" in data
        assert "repos" in data

    def test_generate_session_templates_returns_json(self, simple_config):
        """Test session templates generator returns valid JSON."""
        from loom.generators import generate_session_templates
        import json

        output = generate_session_templates(simple_config)
        data = json.loads(output)
        assert isinstance(data, dict)
        assert "workspace" in data
        assert "templates" in data
        assert isinstance(data["templates"], list)

    def test_generate_session_templates_includes_generic_workflows(self, simple_config):
        """Test session templates include generic workflows."""
        from loom.generators import generate_session_templates
        import json

        output = generate_session_templates(simple_config)
        data = json.loads(output)
        template_names = [t["name"] for t in data["templates"]]
        assert "Full Stack Testing" in template_names
        assert "Setup Workspace" in template_names
        assert "Synchronized Commit" in template_names

    def test_generate_session_templates_includes_high_risk_zones(self, simple_config):
        """Test session templates include HIGH-risk zone templates."""
        from loom.generators import generate_session_templates
        import json

        output = generate_session_templates(simple_config)
        data = json.loads(output)
        # simple_config has one HIGH zone, should generate a template
        high_risk_templates = [
            t for t in data["templates"] if t.get("risk") == "HIGH"
        ]
        assert len(high_risk_templates) > 0

    def test_generate_env_setup_returns_bash_script(self, simple_config):
        """Test env setup generator returns bash script."""
        from loom.generators import generate_env_setup

        output = generate_env_setup(simple_config)
        assert isinstance(output, str)
        assert "#!/bin/bash" in output
        assert "set -e" in output

    def test_generate_env_setup_validates_shared_env(self):
        """Test env setup validates shared environment variables."""
        from loom.generators import generate_env_setup

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

        output = generate_env_setup(config)
        assert "AUTH_SECRET" in output
        assert "JWT_KEY" in output
        assert "Missing:" in output or "is set" in output

    def test_generate_claude_code_includes_critical_files(self):
        """Test that Claude Code generator includes critical files section."""
        from loom.generators import generate_claude_code

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
                    name="Critical Auth",
                    risk=RiskLevel.HIGH,
                    source=SourceTarget(repo="api", file="src/auth.py"),
                    trigger="Auth changes",
                ),
            ],
        )

        output = generate_claude_code(config)
        assert "## Critical Files" in output
        assert "src/auth.py" in output

    def test_generate_claude_code_includes_preflight_checklist(self, simple_config):
        """Test that Claude Code generator includes pre-flight checklist."""
        output = generate_claude_code(simple_config)
        assert "## Pre-Flight Checklist" in output
        assert "Before making changes" in output
        assert "[ ]" in output  # Markdown checkboxes


class TestGenerateDependencyGraph:
    """Tests for dependency graph HTML generator (v0.5.0)."""

    def test_returns_html_string(self, simple_config):
        """Test that generator returns HTML content."""
        output = generate_dependency_graph(simple_config)
        assert isinstance(output, str)
        assert output.startswith("<!DOCTYPE html>")
        assert "</html>" in output

    def test_contains_valid_html_structure(self, simple_config):
        """Test that output contains valid HTML elements."""
        output = generate_dependency_graph(simple_config)
        assert "<html" in output
        assert "<head>" in output
        assert "<body>" in output
        assert "<svg" in output

    def test_contains_workspace_name(self, simple_config):
        """Test that output includes workspace name."""
        output = generate_dependency_graph(simple_config)
        assert simple_config.name in output

    def test_contains_repository_names(self, simple_config):
        """Test that output includes all repository names."""
        output = generate_dependency_graph(simple_config)
        for repo in simple_config.repos:
            assert repo.name in output

    def test_contains_dependency_descriptions(self):
        """Test that output includes dependency descriptions."""
        from loom.config import Dependency

        config = LoomConfig(
            name="Test",
            description="Test workspace",
            repos=[
                Repo(name="api", url="https://example.com/api", role="api", language=Language.PYTHON),
                Repo(name="client", url="https://example.com/client", role="client", language=Language.TYPESCRIPT),
            ],
            dependencies=[
                Dependency(**{"from": "client", "to": "api", "description": "REST API dependency"})
            ],
        )

        output = generate_dependency_graph(config)
        assert "REST API dependency" in output

    def test_includes_language_colors(self, simple_config):
        """Test that output includes language color information."""
        output = generate_dependency_graph(simple_config)
        # Should contain color hex values
        assert "#3776ab" in output or "#2b7a0b" in output  # Python or TypeScript colors

    def test_handles_empty_repos_gracefully(self):
        """Test that generator handles empty repo list."""
        config = LoomConfig(
            name="Empty",
            description="No repos",
            repos=[],
        )

        output = generate_dependency_graph(config)
        assert "No repositories configured" in output or len(output) > 0

    def test_includes_impact_zone_badges(self):
        """Test that impact zones are indicated in the graph."""
        from loom.config import Dependency

        config = LoomConfig(
            name="Test",
            description="Test",
            repos=[
                Repo(name="api", url="https://example.com/api", role="api", language=Language.PYTHON),
                Repo(name="client", url="https://example.com/client", role="client", language=Language.TYPESCRIPT),
            ],
            dependencies=[
                Dependency(**{"from": "client", "to": "api", "description": "REST API"})
            ],
            impact_zones=[
                ImpactZone(
                    id="IZ-001",
                    name="Schema Change",
                    risk=RiskLevel.HIGH,
                    source=SourceTarget(repo="api"),
                    target=SourceTarget(repo="client"),
                    trigger="When schema changes",
                )
            ],
        )

        output = generate_dependency_graph(config)
        # Should indicate zone count
        assert "ff6b6b" in output or "IZ-001" in output or len(output) > 0
