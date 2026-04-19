"""Pydantic schema for loom.yaml configuration."""

from enum import Enum
from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, Field, field_validator


class Language(str, Enum):
    """Programming language enum."""

    PYTHON = "python"
    TYPESCRIPT = "typescript"
    GO = "golang"
    RUST = "rust"


class RiskLevel(str, Enum):
    """Risk level for impact zones."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class Repo(BaseModel):
    """Repository configuration."""

    name: str = Field(..., description="Repository name")
    url: str = Field(..., description="Repository URL")
    local_path: Optional[str] = Field(
        None, description="Local path (defaults to ~/Projects/<name>)"
    )
    role: str = Field(..., description="Role in the ecosystem")
    language: Language = Field(..., description="Primary language")
    test_command: Optional[str] = Field(None, description="Test command")
    install_command: Optional[str] = Field(None, description="Install command")
    doctor_command: Optional[str] = Field(None, description="Health check command")

    def resolve_local_path(self) -> Path:
        """Resolve local_path, defaulting to ~/Projects/<name>."""
        if self.local_path:
            return Path(self.local_path).expanduser()
        return Path.home() / "Projects" / self.name


class Dependency(BaseModel):
    """Inter-repo dependency."""

    from_repo: str = Field(alias="from", description="Source repo name")
    to_repo: str = Field(alias="to", description="Target repo name")
    description: str = Field(..., description="Dependency description")


class SourceTarget(BaseModel):
    """Source or target specification."""

    repo: Optional[str] = None
    file: Optional[str] = None
    function: Optional[str] = None
    tool: Optional[str] = None


class ImpactZone(BaseModel):
    """Cross-repo impact zone."""

    id: str = Field(..., description="Impact zone ID (e.g. IZ-001)")
    name: str = Field(..., description="Name of the impact zone")
    risk: RiskLevel = Field(..., description="Risk level")
    source: Optional[SourceTarget] = None
    target: Optional[SourceTarget] = None
    trigger: str = Field(..., description="When this zone is triggered")
    status: Optional[str] = Field(None, description="Implementation status")
    shared_env: Optional[list[str]] = Field(None, description="Shared environment variables")


class AITools(BaseModel):
    """AI tool configuration flags."""

    claude_code: bool = True
    codex: bool = False
    cursor: bool = False
    aider: bool = False


class LoomConfig(BaseModel):
    """Root configuration for loom.yaml."""

    name: str = Field(..., description="Workspace name")
    description: str = Field(..., description="Workspace description")
    repos: list[Repo] = Field(..., description="Repository list")
    dependencies: Optional[list[Dependency]] = None
    impact_zones: Optional[list[ImpactZone]] = None
    ai_tools: Optional[AITools] = Field(default_factory=AITools)

    model_config = {"populate_by_name": True}

    @field_validator("repos")
    @classmethod
    def repos_have_unique_names(cls, v: list[Repo]) -> list[Repo]:
        """Ensure all repo names are unique."""
        names = [repo.name for repo in v]
        if len(names) != len(set(names)):
            raise ValueError("Repo names must be unique")
        return v

    @staticmethod
    def load_yaml(path: Path | str) -> "LoomConfig":
        """Load LoomConfig from a YAML file."""
        path = Path(path)
        with open(path) as f:
            data = yaml.safe_load(f)
        return LoomConfig(**data)

    def save_yaml(self, path: Path | str) -> None:
        """Save LoomConfig to a YAML file."""
        path = Path(path)
        with open(path, "w") as f:
            # Use mode='json' to ensure Enums are serialized to their string values
            yaml.dump(self.model_dump(by_alias=True, exclude_none=True, mode="json"), f)
