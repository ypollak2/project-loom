# Changelog

All notable changes to Project Loom will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] — 2026-04-19

### Added

**Test Suite (34 tests, 47% coverage):**
- `tests/test_config.py` — Repo model path resolution, LoomConfig validation, YAML roundtrip serialization
- `tests/test_generators.py` — All 4 generators output validation (Claude Code, Codex, Cursor, Aider)
- `tests/test_workspace.py` — Directory setup, orchestration script generation, bash variable substitution
- `tests/test_cli.py` — Config loading and manipulation

**GitHub Actions CI/CD:**
- `.github/workflows/ci.yml` — Multi-version testing (Python 3.10, 3.11, 3.12)
  - Linting with ruff
  - Format checking with black
  - Testing with pytest + coverage
  - Codecov integration
- `.github/workflows/release.yml` — Release automation
  - Build wheel distribution
  - Create GitHub Release
  - Publish to PyPI (requires `PYPI_API_TOKEN` secret)

**Documentation & Templates:**
- `.github/ISSUE_TEMPLATE/bug.md` — Bug report template
- `.github/ISSUE_TEMPLATE/feature.md` — Feature request template
- Comprehensive README with use cases, configuration reference, and examples

### Changed

- **pyproject.toml**: Version bumped to 0.1.1 (tracking actual release tag)
- **Test infrastructure**: pytest, pytest-cov added to dev dependencies

## [0.1.1] — 2026-04-19

### Fixed

- **Bash orchestration script** (`loom/workspace.py`): Replaced broken `{{ }}` placeholders with proper per-repo command variable substitution using bash variable indirection (`${!repo_var}`). Script now correctly executes per-repo install/test commands.
- **Command escaping**: Added proper single-quote escaping in bash variables for commands containing special characters

### Added

- **`loom validate <yaml>`** command: Validate loom.yaml configuration against Pydantic schema with detailed error reporting
- **`loom pull`** command: `git pull --ff-only` across all repositories with status reporting
- **`loom sync-commit <msg>`** command: Atomic multi-repo commits with shared sync trailer format `Loom-Sync: LOOM-YYYY-MM-DD-<6hex>` (using 6-byte hex secrets for uniqueness)
- **Shared environment variables**: `.claudecode.md` now renders `shared_env` list from impact zones in a dedicated section
- **Documentation files**: `.gitignore` (Python project standards) and `CHANGELOG.md` (versioned changelog)
- **API schema validation**: `from_repo` and `to_repo` fields in Dependency model now properly alias `from` and `to`

### Technical Details

- Orchestration script now uses bash pattern expansion (`${repo##*/}`) to extract repo names from paths
- Sync ID generation: `datetime.now().strftime("%Y-%m-%d")` + `secrets.token_hex(3)` = 11-char unique identifier
- All new commands follow existing error handling patterns (file not found, validation errors)

## [0.1.0] — 2026-04-15

### Added

**Core CLI Commands:**
- `loom init` — Interactive wizard to create loom.yaml
- `loom apply` — Clone repos, create symlinks, generate AI configs
- `loom status` — Show git status across all repos
- `loom test-all` — Run tests in all repos
- `loom install` — Run install commands in all repos
- `loom doctor` — Run health checks in all repos
- `loom diff` — Show git diffs across all repos
- `loom logs` — Show recent commits across all repos

**Generators (Pure Functions):**
- `claude_code.py` — `.claudecode.md` for Claude Code AI tool
  - Ecosystem map table (repos, roles, languages, interfaces)
  - Dependency graph visualization
  - Impact zones table with risk levels
  - Quick reference (commands, paths)
- `codex.py` — `.codex-plugin/loom-context.md` for Codex
- `cursor.py` — `.cursorrules` for Cursor IDE
- `aider.py` — `AGENTS.md` for Aider AI pair programmer

**Configuration & Schema:**
- Pydantic schema validation for loom.yaml
- `Repo` model with auto-resolved local paths
- `Dependency` model for inter-repo relationships
- `ImpactZone` model for cross-repo impact tracking
- `AITools` flags for selective generator activation
- YAML serialization (save/load roundtrip)

**Workspace Setup:**
- Idempotent directory creation (`meta-workspace/services/`, `configs/`, `scripts/`)
- Repository cloning (with error handling)
- Symlink creation (services → local clones)
- Bash orchestration script generation (`meta-workspace/scripts/loom`)
- Dependency graph JSON export

**CLI Framework:**
- Typer-based CLI with command help and argument validation
- Rich console output with colors and formatting
- Error messages with actionable context
