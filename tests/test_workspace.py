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
                install_command="pip install -e .",
                test_command="pytest tests/",
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

    def test_script_includes_test_commands(self, simple_config):
        """Test that script includes per-repo test commands."""
        script = _build_orchestration_script(simple_config)
        assert "test_api=" in script
        assert "test_client=" in script
        assert "pytest" in script

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


class TestGenerateClaudeContextFiles:
    """Tests for v0.3.0 Claude context file generation."""

    def test_claude_context_directory_created(self, simple_config, tmp_path):
        """Test that .claude/ directory is created during workspace setup."""
        from loom.workspace import _setup_workspace_dirs

        workspace_path = tmp_path / "workspace"
        _setup_workspace_dirs(workspace_path)

        assert (workspace_path / ".claude").exists()
        assert (workspace_path / ".claude").is_dir()

    def test_generate_claude_context_files(self, simple_config, tmp_path):
        """Test that all Claude context files are generated."""
        from loom.workspace import _generate_claude_context_files

        workspace_path = tmp_path / "workspace"
        workspace_path.mkdir(parents=True)
        (workspace_path / ".claude").mkdir()

        _generate_claude_context_files(simple_config, workspace_path)

        # Verify all files are created
        assert (workspace_path / ".claude" / "file-ownership.json").exists()
        assert (workspace_path / ".claude" / "git-context.json").exists()
        assert (workspace_path / ".claude" / "session-templates.json").exists()
        assert (workspace_path / ".claude" / "env-setup.sh").exists()

    def test_env_setup_script_is_executable(self, simple_config, tmp_path):
        """Test that env-setup.sh is executable."""
        from loom.workspace import _generate_claude_context_files
        import stat

        workspace_path = tmp_path / "workspace"
        workspace_path.mkdir(parents=True)
        (workspace_path / ".claude").mkdir()

        _generate_claude_context_files(simple_config, workspace_path)

        script_path = workspace_path / ".claude" / "env-setup.sh"
        assert script_path.exists()
        # Check if executable
        assert script_path.stat().st_mode & stat.S_IXUSR

    def test_git_context_includes_timestamp(self, simple_config, tmp_path):
        """Test that git-context.json includes generated_at timestamp."""
        from loom.workspace import _generate_claude_context_files
        import json

        workspace_path = tmp_path / "workspace"
        workspace_path.mkdir(parents=True)
        (workspace_path / ".claude").mkdir()

        _generate_claude_context_files(simple_config, workspace_path)

        context_path = workspace_path / ".claude" / "git-context.json"
        data = json.loads(context_path.read_text())
        assert "generated_at" in data
        assert data["generated_at"] is not None
        assert len(data["generated_at"]) > 0


class TestGenerateMCPConfig:
    """Tests for v0.4.0 MCP server configuration generation."""

    def test_mcp_config_is_generated(self, simple_config, tmp_path):
        """Test that .mcp.json is generated."""
        from loom.workspace import _generate_mcp_config
        import json

        workspace_path = tmp_path / "workspace"
        workspace_path.mkdir(parents=True)

        _generate_mcp_config(workspace_path)

        mcp_path = workspace_path / ".mcp.json"
        assert mcp_path.exists()

        # Verify content
        config = json.loads(mcp_path.read_text())
        assert "mcpServers" in config
        assert "loom" in config["mcpServers"]

    def test_mcp_config_has_correct_structure(self, simple_config, tmp_path):
        """Test that MCP config has correct structure."""
        from loom.workspace import _generate_mcp_config
        import json

        workspace_path = tmp_path / "workspace"
        workspace_path.mkdir(parents=True)

        _generate_mcp_config(workspace_path)

        mcp_path = workspace_path / ".mcp.json"
        config = json.loads(mcp_path.read_text())

        loom_server = config["mcpServers"]["loom"]
        assert loom_server["command"] == "loom"
        assert loom_server["args"] == ["serve", "loom.yaml"]
