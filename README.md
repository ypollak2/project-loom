# Project Loom — Multi-Repo AI Workspace Generator

[![CI Status](https://github.com/ypollak2/project-loom/actions/workflows/ci.yml/badge.svg)](https://github.com/ypollak2/project-loom/actions)
[![Tests](https://img.shields.io/badge/tests-79%20passing-brightgreen)](tests/)
[![Coverage](https://img.shields.io/badge/coverage-85%25-brightgreen)](tests/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Project Loom unifies multi-repository development by generating AI-ready workspace configurations. Define your repos, dependencies, and impact zones once—Loom generates everything: symlinks, orchestration scripts, and AI tool configs (Claude Code, Codex, Cursor, Aider).

## Why Project Loom?

When you're working across 3+ repositories:

- **Scattered configs** — Claude Code, Codex, Cursor, Aider each need different markdown formats
- **Manual orchestration** — Running tests/installs across repos is shell-script spaghetti
- **Lost context** — Which files are risky to change? Which repos will break?
- **Repeated setup** — Every team member re-discovers the same patterns

**Loom solves this:**

```bash
# Define your workspace once
loom init

# Apply to your local machine
loom apply

# Everything works together
loom install          # Install all repos
loom test-all         # Run all tests
loom status           # Git status across workspace
loom sync-commit "bugfix: auth token expires correctly"  # Atomic multi-repo commit
```

## Quick Start

### Installation

```bash
pip install project-loom
```

Or install from source:

```bash
git clone https://github.com/ypollak2/project-loom
cd project-loom
pip install -e .
```

### Usage

#### 1. Create a configuration (interactive)

```bash
loom init
```

This launches an interactive wizard that asks about your repos, dependencies, and AI tools. Outputs `loom.yaml`.

#### 2. Apply the configuration

```bash
loom apply loom.yaml
```

This:
- Clones repositories (if not already cloned)
- Creates symlinks in `meta-workspace/services/`
- Generates AI tool configs (`.claudecode.md`, `.cursorrules`, etc.)
- Generates `scripts/loom` orchestration CLI

#### 3. Use the workspace

```bash
# Run tests in all repos
loom test-all

# Git status across all repos
loom status

# Health check all repos
loom doctor

# Synchronized commit across dirty repos
loom sync-commit "message"
```

## Core Commands

| Command | Purpose |
|---------|---------|
| `loom init` | Interactive wizard to create `loom.yaml` |
| `loom apply [yaml]` | Clone repos, create symlinks, generate AI configs |
| `loom validate [yaml]` | Validate YAML against schema |
| `loom install` | Run install commands in all repos |
| `loom test-all` | Run tests in all repos |
| `loom doctor` | Run health checks in all repos |
| `loom status` | Git status across all repos |
| `loom diff` | Git diffs across all repos |
| `loom pull` | Git pull --ff-only across all repos |
| `loom logs [--count N]` | Recent commits across all repos |
| `loom sync-commit <msg>` | Commit to all dirty repos with shared trailer |

## Configuration (`loom.yaml`)

### Complete Schema

```yaml
# Workspace metadata
name: my-workspace              # Workspace name (required)
description: "Your description" # Workspace description (required)

# Repositories
repos:
  - name: api                   # Unique repo name
    url: https://github.com/user/api
    role: backend               # Role in ecosystem
    language: python            # python | typescript | golang | rust
    local_path: ~/Projects/api  # Optional; defaults to ~/Projects/<name>
    install_command: pip install -e .
    test_command: pytest
    doctor_command: python -m app doctor

# Cross-repo dependencies
dependencies:
  - from: client
    to: api
    description: REST API calls

# Cross-repo impact zones
impact_zones:
  - id: IZ-001
    name: Auth Flow Changes
    risk: HIGH                  # HIGH | MEDIUM | LOW
    source:
      repo: api
      file: src/auth.py
      function: verify_token
    target:
      repo: client
    trigger: When auth middleware changes
    shared_env:                 # Shared environment variables
      - AUTH_SECRET
      - JWT_EXPIRY

# AI tool configuration flags
ai_tools:
  claude_code: true             # Generate .claudecode.md
  codex: false                  # Generate .codex-plugin/
  cursor: false                 # Generate .cursorrules
  aider: false                  # Generate AGENTS.md
```

### Real-World Example

See `examples/llm-router-chronicle/loom.yaml` for a complete implementation with:
- 2 repos (Go + Python services)
- 1 dependency (REST API)
- 7 impact zones tracking auth, caching, and protocol changes

## Generated Artifacts

After running `loom apply`, you get:

```
meta-workspace/
├── .claudecode.md         # Claude Code AI context
├── .cursorrules           # Cursor IDE rules
├── .codex-plugin/         # Codex configuration
│   └── loom-context.md
├── AGENTS.md              # Aider task agents
├── services/
│   ├── repo-a → ~/Projects/repo-a  (symlink)
│   └── repo-b → ~/Projects/repo-b  (symlink)
├── configs/
│   └── dependency-graph.json
└── scripts/
    └── loom               # Bash orchestration CLI
```

## Commands

### `loom init [--output PATH]`

Interactive wizard to create `loom.yaml`.

### `loom apply YAML [--workspace PATH]`

Apply configuration: clone repos, create symlinks, generate AI configs.

### `loom status [--config PATH]`

Git status of all repos.

### `loom test-all [--config PATH]`

Run tests in all repos.

### `loom install [--config PATH]`

Install all repos (run `install_command` for each).

### `loom doctor [--config PATH]`

Health check all repos (run `doctor_command` for each).

### `loom diff [--config PATH]`

Git diff summary all repos.

### `loom logs [--config PATH] [--count N]`

Show last N commits per repo.

## Design Principles

1. **`loom.yaml` is the single source of truth** — commit it to version control so your whole team can run `loom apply` and get identical workspaces.

2. **Generators are pure functions** — they take `LoomConfig` and return strings. Easy to test, easy to extend.

3. **`apply` is idempotent** — safe to re-run. Won't duplicate content or break existing symlinks.

4. **No mutation of existing code** — loom only creates net-new files under `meta-workspace/`. Your repos are untouched.

5. **Impact zones are explicit** — document cross-repo dependencies upfront so teams understand consequences before coding.

## Extending Loom

### Adding a New AI Tool

1. Create `loom/generators/mytool.py` with a `generate_mytool(config: LoomConfig) -> str` function
2. Add to `loom/generators/__init__.py`
3. Add to `loom/workspace.py`'s `_generate_ai_configs()`
4. Add to `AITools` model in `loom/config.py`

### Customizing Generators

Edit `loom/generators/*.py` to change output format for any AI tool. For example, to add custom rules to `.claudecode.md`, modify `loom/generators/claude_code.py`.

## Development

```bash
# Install with dev dependencies
pip install -e '.[dev]'

# Run tests
pytest

# Format code
black loom

# Lint
ruff check loom
```

## License

MIT

## See Also

- [Chronicle](https://github.com/ypollak2/chronicle) — Architectural decision memory layer
- [LLM Router](https://github.com/ypollak2/llm-router) — LLM dispatch and budget management
