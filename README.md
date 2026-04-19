# Project Loom

Unified AI-ready workspace generator for multi-repo projects. Generate a structured `meta-workspace/` with symlinks, cross-repo context docs, and first-class configurations for Claude Code, Codex, Cursor, and Aider.

## Motivation

When developing with multiple interconnected repositories, you need:
- **Single source of truth** for repo relationships and dependencies
- **Centralized AI context** that multiple AI tools can read
- **Coordinated workflows** for synchronized commits across repos
- **Impact zone tracking** to understand cross-repo consequences

Project Loom provides all of this via a single `loom.yaml` config file.

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

## Configuration (`loom.yaml`)

### Schema

```yaml
name: workspace-name
description: "Description of your workspace"

repos:
  - name: repo-name
    url: https://github.com/user/repo
    local_path: ~/Projects/repo  # optional; defaults to ~/Projects/<name>
    role: "Role in the ecosystem"
    language: python  # or typescript, golang, rust
    test_command: "pytest"
    install_command: "pip install -e ."
    doctor_command: "python -m myapp doctor"

dependencies:
  - from: repo-a
    to: repo-b
    description: "repo-b depends on repo-a"

impact_zones:
  - id: IZ-001
    name: "Feature Name"
    risk: HIGH  # HIGH, MEDIUM, LOW
    source:
      repo: repo-a
      file: src/module.py
      function: critical_function
    target:
      repo: repo-b
      file: src/other.py
      tool: mcp_tool_name
    trigger: "When this zone is triggered"

ai_tools:
  claude_code: true
  codex: false
  cursor: false
  aider: false
```

### Example: llm-router + chronicle

See `examples/llm-router-chronicle/loom.yaml` for a complete reference implementation with seven impact zones.

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
