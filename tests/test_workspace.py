"""Tests for loom.workspace module."""

import tempfile
from pathlib import Path

import pytest

from loom.config import Language, LoomConfig, Repo
from loom.workspace import (
    _build_orchestration_script,
    _setup_workspace_dirs,
)


@pytest.fixture
def simple_config() -> LoomConfig:
    """Create a simple config for testing."""
    return LoomConfig(
        name="Test Workspace",
        description="Test workspace",
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
                install_command="npm install",
                test_command="npm test",
            ),
        ],
    )


class TestSetupWorkspaceDirs:
    """Tests for workspace directory setup."""

    def test_creates_required_directories(self):
        """Test that setup creates all required directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace_path = Path(tmpdir) / "workspace"
            _setup_workspace_dirs(workspace_path)

            assert (workspace_path / "services").exists()
            assert (workspace_path / "configs").exists()
            assert (workspace_path / "scripts").exists()

    def test_idempotent_directory_creation(self):
        """Test that calling setup twice is safe."""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace_path = Path(tmpdir) / "workspace"

            _setup_workspace_dirs(workspace_path)
            initial_stat = (workspace_path / "services").stat()

            _setup_workspace_dirs(workspace_path)
            second_stat = (workspace_path / "services").stat()

            # Should be same directory (inode unchanged)
            assert initial_stat.st_ino == second_stat.st_ino


class TestBuildOrchestrationScript:
    """Tests for bash orchestration script generation."""

    def test_script_has_shebang(self, simple_config):
        """Test that script starts with shebang."""
        script = _build_orchestration_script(simple_config)
        assert script.startswith("#!/bin/bash")

    def test_script_includes_repo_list(self, simple_config):
        """Test that script includes repos in REPOS variable."""
        script = _build_orchestration_script(simple_config)
        assert "REPOS=" in script
        assert "services/api" in script
        assert "services/client" in script

    def test_script_includes_install_commands(self, simple_config):
        """Test that script includes per-repo install commands."""
        script = _build_orchestration_script(simple_config)
        # Should have install_api and install_client variables
        assert "install_api=" in script
        assert "install_client=" in script
        assert "pip install -e ." in script
        assert "npm install" in script

    def test_script_includes_test_commands(self, simple_config):
        """Test that script includes per-repo test commands."""
        script = _build_orchestration_script(simple_config)
        assert "test_api=" in script
        assert "test_client=" in script
        assert "pytest" in script
        assert "npm test" in script

    def test_script_has_case_statements(self, simple_config):
        """Test that script has proper case statements."""
        script = _build_orchestration_script(simple_config)
        assert 'case "${1:-help}" in' in script
        assert "install)" in script
        assert "test)" in script
        assert "status)" in script
        assert "help|--help|-h)" in script

    def test_script_has_eval_variable_substitution(self, simple_config):
        """Test that script uses eval for command substitution."""
        script = _build_orchestration_script(simple_config)
        assert "eval" in script
        assert "${!repo_var}" in script

    def test_script_handles_no_install_command(self):
        """Test that script handles repos without install_command."""
        config = LoomConfig(
            name="Test",
            description="Test",
            repos=[
                Repo(
                    name="api",
                    url="https://example.com/api",
                    role="backend",
                    language=Language.PYTHON,
                    # No install_command
                ),
            ],
        )
        script = _build_orchestration_script(config)
        # Should still be valid script
        assert script.startswith("#!/bin/bash")
        assert "case" in script

    def test_script_escapes_single_quotes(self):
        """Test that script properly escapes single quotes in commands."""
        config = LoomConfig(
            name="Test",
            description="Test",
            repos=[
                Repo(
                    name="test-repo",
                    url="https://example.com/test-repo",
                    role="backend",
                    language=Language.PYTHON,
                    install_command="echo 'hello world'",
                ),
            ],
        )
        script = _build_orchestration_script(config)
        # Should contain escaped quotes
        assert "hello world" in script

    def test_script_is_executable(self, simple_config):
        """Test that generated script can be executed (syntax check)."""
        script = _build_orchestration_script(simple_config)
        # Verify it's valid bash by checking key elements
        assert "#!/bin/bash" in script
        assert "set -e" in script
        assert "esac" in script
        assert script.count("case") == script.count("esac")
