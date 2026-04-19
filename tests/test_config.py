"""Tests for loom.config module."""

import tempfile
from pathlib import Path

import pytest
from pydantic import ValidationError

from loom.config import Language, LoomConfig, RiskLevel, Repo


class TestRepo:
    """Tests for Repo model."""

    def test_resolve_local_path_default(self):
        """Test resolve_local_path defaults to ~/Projects/<name>."""
        repo = Repo(
            name="test-repo",
            url="https://github.com/test/test-repo",
            role="test",
            language=Language.PYTHON,
        )
        expected = Path.home() / "Projects" / "test-repo"
        assert repo.resolve_local_path() == expected

    def test_resolve_local_path_custom(self):
        """Test resolve_local_path with custom local_path."""
        custom_path = "/tmp/my-repo"
        repo = Repo(
            name="test-repo",
            url="https://github.com/test/test-repo",
            role="test",
            language=Language.PYTHON,
            local_path=custom_path,
        )
        assert repo.resolve_local_path() == Path(custom_path)

    def test_resolve_local_path_expands_tilde(self):
        """Test resolve_local_path expands ~ in custom paths."""
        repo = Repo(
            name="test-repo",
            url="https://github.com/test/test-repo",
            role="test",
            language=Language.PYTHON,
            local_path="~/custom/path",
        )
        assert "~" not in str(repo.resolve_local_path())


class TestLoomConfig:
    """Tests for LoomConfig model."""

    def test_config_requires_name(self):
        """Test that name is required."""
        with pytest.raises(ValidationError):
            LoomConfig(
                description="Test",
                repos=[],
            )

    def test_config_requires_description(self):
        """Test that description is required."""
        with pytest.raises(ValidationError):
            LoomConfig(
                name="Test",
                repos=[],
            )

    def test_config_requires_repos(self):
        """Test that repos is required."""
        with pytest.raises(ValidationError):
            LoomConfig(
                name="Test",
                description="Test",
            )

    def test_repo_names_must_be_unique(self):
        """Test that repo names must be unique."""
        with pytest.raises(ValidationError) as exc_info:
            LoomConfig(
                name="Test",
                description="Test",
                repos=[
                    Repo(
                        name="repo1",
                        url="https://example.com/repo1",
                        role="test",
                        language=Language.PYTHON,
                    ),
                    Repo(
                        name="repo1",
                        url="https://example.com/repo1-duplicate",
                        role="test",
                        language=Language.PYTHON,
                    ),
                ],
            )
        assert "unique" in str(exc_info.value)

    def test_config_with_dependencies(self):
        """Test config with dependencies."""
        config = LoomConfig(
            name="Test",
            description="Test workspace",
            repos=[
                Repo(
                    name="repo1",
                    url="https://example.com/repo1",
                    role="api",
                    language=Language.PYTHON,
                ),
                Repo(
                    name="repo2",
                    url="https://example.com/repo2",
                    role="client",
                    language=Language.PYTHON,
                ),
            ],
            dependencies=[
                {"from": "repo2", "to": "repo1", "description": "REST API dependency"}
            ],
        )
        assert len(config.dependencies) == 1
        assert config.dependencies[0].from_repo == "repo2"

    def test_load_yaml_valid(self, tmp_path):
        """Test loading valid YAML."""
        yaml_file = tmp_path / "loom.yaml"
        yaml_file.write_text(
            """
name: Test Workspace
description: Test configuration
repos:
  - name: repo1
    url: https://example.com/repo1
    role: api
    language: python
    install_command: pip install -e .
    test_command: pytest
"""
        )

        config = LoomConfig.load_yaml(yaml_file)
        assert config.name == "Test Workspace"
        assert len(config.repos) == 1
        assert config.repos[0].name == "repo1"
        assert config.repos[0].install_command == "pip install -e ."

    def test_save_and_load_roundtrip(self, tmp_path):
        """Test save and load roundtrip."""
        yaml_file = tmp_path / "loom.yaml"

        config = LoomConfig(
            name="Test",
            description="Test workspace",
            repos=[
                Repo(
                    name="repo1",
                    url="https://example.com/repo1",
                    role="test",
                    language=Language.PYTHON,
                    test_command="pytest",
                ),
            ],
        )

        config.save_yaml(yaml_file)
        loaded = LoomConfig.load_yaml(yaml_file)

        assert loaded.name == config.name
        assert loaded.description == config.description
        assert len(loaded.repos) == 1
        assert loaded.repos[0].test_command == "pytest"
