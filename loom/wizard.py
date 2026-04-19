"""Interactive wizard for loom init command."""

from pathlib import Path

import questionary
from rich.console import Console

from loom.config import AITools, Dependency, Language, LoomConfig, Repo

console = Console()


def run_init_wizard() -> LoomConfig:
    """Run interactive wizard to create a new loom.yaml configuration.

    Returns:
        LoomConfig: Generated configuration
    """
    console.print(
        "[bold cyan]🧵 Project Loom — Interactive Workspace Setup[/bold cyan]\n"
    )

    # Workspace metadata
    name = questionary.text("Workspace name:", default="my-workspace").ask()
    description = questionary.text("Description:").ask()

    # Repositories
    repos = []
    console.print("\n[yellow]Add repositories (at least 1):[/yellow]")

    while True:
        repo = _prompt_repo(len(repos) + 1)
        if repo:
            repos.append(repo)

        if len(repos) > 0:
            add_more = questionary.confirm("Add another repository?", default=False).ask()
            if not add_more:
                break

    if not repos:
        raise ValueError("At least one repository is required")

    # Dependencies
    dependencies = []
    if len(repos) > 1:
        console.print("\n[yellow]Add dependencies (optional):[/yellow]")
        while True:
            dep = _prompt_dependency(repos)
            if dep:
                dependencies.append(dep)
            else:
                break

            if not questionary.confirm("Add another dependency?", default=False).ask():
                break

    # AI Tools
    console.print("\n[yellow]Enable AI tools:[/yellow]")
    ai_tools = AITools(
        claude_code=questionary.confirm("Claude Code", default=True).ask(),
        codex=questionary.confirm("Codex", default=False).ask(),
        cursor=questionary.confirm("Cursor", default=False).ask(),
        aider=questionary.confirm("Aider", default=False).ask(),
    )

    # Build config
    config = LoomConfig(
        name=name,
        description=description,
        repos=repos,
        dependencies=dependencies if dependencies else None,
        ai_tools=ai_tools,
    )

    return config


def _prompt_repo(index: int) -> Repo | None:
    """Prompt for a single repository configuration.

    Returns:
        Repo or None if user cancels
    """
    console.print(f"\n[dim]Repository {index}:[/dim]")

    name = questionary.text("  Name (e.g., my-service):").ask()
    if not name:
        return None

    url = questionary.text(
        "  Repository URL (https://...):",
        default=f"https://github.com/user/{name}",
    ).ask()

    local_path_input = questionary.text(
        "  Local path (default: ~/Projects/<name>):",
        default="",
    ).ask()
    local_path = local_path_input if local_path_input else None

    role = questionary.text("  Role in ecosystem:").ask()

    language = questionary.select(
        "  Primary language:",
        choices=[lang.value for lang in Language],
    ).ask()

    test_command = questionary.text(
        "  Test command (optional):",
        default="",
    ).ask()

    install_command = questionary.text(
        "  Install command (optional):",
        default="",
    ).ask()

    doctor_command = questionary.text(
        "  Health check command (optional, e.g., 'npm run doctor'):",
        default="",
    ).ask()

    return Repo(
        name=name,
        url=url,
        local_path=local_path,
        role=role,
        language=Language(language),
        test_command=test_command or None,
        install_command=install_command or None,
        doctor_command=doctor_command or None,
    )


def _prompt_dependency(repos: list[Repo]) -> Dependency | None:
    """Prompt for a single dependency.

    Args:
        repos: List of available repositories

    Returns:
        Dependency or None if user cancels
    """
    repo_names = [repo.name for repo in repos]

    from_repo = questionary.select(
        "  From (source):",
        choices=repo_names,
    ).ask()

    if not from_repo:
        return None

    to_repo = questionary.select(
        "  To (target):",
        choices=[r for r in repo_names if r != from_repo],
    ).ask()

    if not to_repo:
        return None

    description = questionary.text("  Description:").ask()

    return Dependency(
        from_repo=from_repo,
        to_repo=to_repo,
        description=description or "",
    )
