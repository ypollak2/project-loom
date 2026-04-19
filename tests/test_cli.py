"""Tests for loom.cli module."""

import tempfile
from pathlib import Path

import pytest

from loom.config import Language, LoomConfig, Repo


@pytest.fixture
def temp_loom_yaml(tmp_path: Path) -> Path:
    """Create a temporary loom.yaml for testing."""
    yaml_file = tmp_path / "loom.yaml"
    config = LoomConfig(
        name="Test Workspace",
        description="Test configuration",
        repos=[
            Repo(
                name="api",
                url="https://example.com/api",
                role="backend",
                language=Language.PYTHON,
                install_command="pip install -e .",
                test_command="pytest",
            ),
        ],
    )
    config.save_yaml(yaml_file)
    return yaml_file


class TestCLICommands:
    """Tests for CLI commands (basic validation)."""

    def test_config_can_be_loaded(self, temp_loom_yaml):
        """Test that a config YAML can be loaded."""
        config = LoomConfig.load_yaml(temp_loom_yaml)
        assert config.name == "Test Workspace"
        assert len(config.repos) == 1

    def test_config_roundtrip_preserves_structure(self, temp_loom_yaml):
        """Test that saving and loading preserves config structure."""
        config1 = LoomConfig.load_yaml(temp_loom_yaml)

        with tempfile.TemporaryDirectory() as tmpdir:
            new_yaml = Path(tmpdir) / "copied.yaml"
            config1.save_yaml(new_yaml)
            config2 = LoomConfig.load_yaml(new_yaml)

            assert config2.name == config1.name
            assert config2.repos[0].name == config1.repos[0].name
