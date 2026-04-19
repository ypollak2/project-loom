# Changelog

All notable changes to Project Loom will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.1] — 2026-04-19

### Fixed
- **Bash orchestration script**: Fixed broken `{{ }}` placeholders in generated install/test commands; now properly resolves per-repo commands via shell variable indirection
- **`sync-commit` command**: Implemented missing CLI command to commit changes across all repos with a shared sync trailer (`LOOM-YYYY-MM-DD-<6hex>`)

### Added
- **`validate` command**: Validate loom.yaml configuration against Pydantic schema with detailed error reporting
- **`pull` command**: Pull latest changes from all repositories using `git pull --ff-only`
- **.gitignore**: Standard Python project ignore rules
- **CHANGELOG.md**: Versioned changelog documentation

## [0.1.0] — 2026-04-15

### Added
- Initial release: Core functionality for multi-repo workspace configuration
  - `init`: Interactive wizard to create loom.yaml
  - `apply`: Clone repos, create symlinks, generate AI configs
  - `status`: Show git status across all repos
  - `test_all`: Run tests in all repos
  - `install`: Run install commands in all repos
  - `doctor`: Run health checks in all repos
  - `diff`: Show git diffs across all repos
  - `logs`: Show recent commits across all repos
- 4 generators: Claude Code, Codex, Cursor, Aider
- Bash orchestration script generator
- Dependency graph JSON export
- Pydantic schema validation for loom.yaml
- CLI with Typer framework
