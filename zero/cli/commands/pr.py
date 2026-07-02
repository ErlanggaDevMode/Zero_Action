"""CLI subcommand to automate Git branch checkout, conventional commits, pushing, and PR creation."""

import asyncio
import re
import shutil
import subprocess
import urllib.parse
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from zero.services.logging import logger

app = typer.Typer()

def _parse_github_url(remote_url: str) -> Optional[str]:
    """Parse git remote URL into a clean GitHub repository https URL."""
    # Matches git@github.com:owner/repo.git or https://github.com/owner/repo.git
    cleaned = remote_url.strip()
    if cleaned.endswith(".git"):
        cleaned = cleaned[:-4]
        
    if "github.com" in cleaned:
        if cleaned.startswith("git@"):
            # Format: git@github.com:owner/repo -> https://github.com/owner/repo
            path_part = cleaned.split("github.com:")[-1]
            return f"https://github.com/{path_part}"
        elif cleaned.startswith("https://"):
            return cleaned
    return None

def _parse_ai_pr_response(text: str) -> tuple[str, str, str, str]:
    """Parse structured AI response to extract branch, commit, title, and body."""
    branch = ""
    commit = ""
    title = ""
    body = ""
    
    # Simple regex matches
    branch_match = re.search(r"^BRANCH:\s*(.+)$", text, re.MULTILINE | re.IGNORECASE)
    commit_match = re.search(r"^COMMIT:\s*(.+)$", text, re.MULTILINE | re.IGNORECASE)
    title_match = re.search(r"^TITLE:\s*(.+)$", text, re.MULTILINE | re.IGNORECASE)
    body_match = re.search(r"^BODY:\s*\n?(.*)$", text, re.MULTILINE | re.DOTALL | re.IGNORECASE)
    
    if branch_match:
        branch = branch_match.group(1).strip()
    if commit_match:
        commit = commit_match.group(1).strip()
    if title_match:
        title = title_match.group(1).strip()
    if body_match:
        body = body_match.group(1).strip()
        
    # Clean fallback if branch format has bad characters
    branch = re.sub(r"[^a-zA-Z0-9_\-\./]", "", branch)
    if not branch:
        branch = "feat/auto-updates"
        
    return branch, commit, title, body

def pr(
    ctx: typer.Context,
    branch: Optional[str] = typer.Option(None, "--branch", "-b", help="Branch name (auto-generated if omitted)"),
    title: Optional[str] = typer.Option(None, "--title", "-t", help="PR Title (auto-generated if omitted)"),
    body: Optional[str] = typer.Option(None, "--body", "-d", help="PR Description body (auto-generated if omitted)"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Auto-approve commit and branch checkout"),
    push: bool = typer.Option(True, "--push/--no-push", help="Push branch and trigger PR creation"),
) -> None:
    """Automate branch creation, conventional commit generation, pushing, and Pull Request creation."""
    from zero.services.ai import AIService
    from zero.core.exceptions import ConfigError
    
    console = Console()
    cli_context = ctx.obj
    settings = cli_context.settings
    config_dir = cli_context.config_dir

    # 1. Resolve Provider
    try:
        ai_service = AIService(settings, config_dir)
        provider = ai_service.get_provider()
    except ConfigError as e:
        console.print(f"[bold red]Error:[/bold red] {e.message}")
        console.print("[yellow]Please run 'zero setup' first to configure your active provider.[/yellow]")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[bold red]Error resolving AI provider:[/bold red] {e}")
        raise typer.Exit(code=1)

    # 2. Check Git Repo
    try:
        import git
    except ImportError:
        console.print("[bold red]Error:[/bold red] 'gitpython' package is required but not installed.")
        raise typer.Exit(code=1)

    try:
        repo = git.Repo(Path.cwd(), search_parent_directories=True)
    except (git.exc.InvalidGitRepositoryError, git.exc.NoSuchPathError):
        console.print("[bold red]Error:[/bold red] Current workspace is not a Git repository.")
        raise typer.Exit(code=1)

    # Detect current branch and dirty state
    is_dirty = repo.is_dirty(untracked_files=True)
    active_branch_name = repo.active_branch.name if not repo.head.is_detached else "DETACHED_HEAD"
    
    console.print("\n[bold green]Zero Action Git Auto-Pilot[/bold green]")
    console.print(f"Current Branch: [cyan]{active_branch_name}[/cyan] | Dirty State: {'[red]Dirty[/red]' if is_dirty else '[green]Clean[/green]'}")

    if not is_dirty:
        console.print("\n[green]No uncommitted changes detected in repository.[/green]")
        # Check if there are committed changes to push
        if active_branch_name in ("main", "master", "develop", "DETACHED_HEAD"):
            console.print("[yellow]You are on a main branch and have no uncommitted changes. Aborting.[/yellow]\n")
            raise typer.Exit(code=0)
            
        confirm_push = True
        if not yes:
            confirm_push = Confirm.ask(f"Push current branch '[cyan]{active_branch_name}[/cyan]' and create PR?", default=True)
        if not confirm_push:
            raise typer.Exit(code=0)
            
        generated_branch = active_branch_name
        # Fetch last 3 commits to generate PR info
        try:
            commits = list(repo.iter_commits(f"origin/main..{active_branch_name}", max_count=5))
        except Exception:
            try:
                commits = list(repo.iter_commits("HEAD", max_count=3))
            except Exception:
                commits = []
                
        commit_summaries = "\n".join(
            f"- {c.summary.decode('utf-8', errors='replace') if isinstance(c.summary, bytes) else c.summary}"
            for c in commits
        )
        
        user_prompt = f"Generate a PR title and markdown PR description based on these recent commits:\n{commit_summaries}"
        messages = [
            {"role": "system", "content": "You are a PR assistant. Generate a TITLE line starting with 'TITLE: ' followed by the title. Then generate a BODY block starting with 'BODY: ' followed by description markdown."},
            {"role": "user", "content": user_prompt}
        ]
        
        console.print("[yellow]Querying AI for PR title and description...[/yellow]")
        try:
            from zero.core.ui import stream_completion_with_timer
            raw_response = asyncio.run(stream_completion_with_timer(provider, messages, console))
            _, _, generated_title, generated_body = _parse_ai_pr_response(raw_response)
        except Exception as e:
            console.print(f"[bold red]AI Completion failed:[/bold red] {e}")
            generated_title = f"PR: Updates on {generated_branch}"
            generated_body = "Automated updates."
            
        pr_title = title or generated_title
        pr_body = body or generated_body
        generated_commit = ""
    else:
        # Dirty repository: generate branch name, commit message, and PR info
        diff_output = repo.git.diff()
        untracked = repo.untracked_files
        if untracked:
            diff_output += "\n\nUntracked files:\n" + "\n".join(untracked)

        system_context = ai_service.get_system_prompt(Path.cwd())
        system_prompt = (
            f"{system_context}\n\n"
            "You are a Git assistant. Analyze the changes (diff) and generate:\n"
            "1. A short, descriptive git branch name (alphanumeric, hyphens only, lowercase, e.g. feat/add-logging).\n"
            "2. A Conventional Commit message (e.g. feat(cli): add logs option).\n"
            "3. A Pull Request Title.\n"
            "4. A Pull Request Description in Markdown.\n\n"
            "Output format MUST be EXACTLY:\n"
            "BRANCH: <branch_name>\n"
            "COMMIT: <commit_message>\n"
            "TITLE: <pr_title>\n"
            "BODY:\n"
            "<pr_description>"
        )
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Here is the git diff:\n```diff\n{diff_output[:8000]}\n```"}
        ]
        
        console.print("[yellow]Querying AI for branch, conventional commit, and PR specs...[/yellow]")
        try:
            from zero.core.ui import stream_completion_with_timer
            raw_response = asyncio.run(stream_completion_with_timer(provider, messages, console))
            generated_branch, generated_commit, generated_title, generated_body = _parse_ai_pr_response(raw_response)
        except Exception as e:
            console.print(f"[bold red]AI Completion failed:[/bold red] {e}")
            raise typer.Exit(code=1)

        # Allow overrides
        branch_name = branch or generated_branch
        commit_msg = generated_commit
        pr_title = title or generated_title
        pr_body = body or generated_body

        console.print("\n[bold cyan]Proposed Git Actions:[/bold cyan]")
        console.print(f"New Branch:  [white]{branch_name}[/white]")
        console.print(f"Commit Msg:  [white]{commit_msg}[/white]")
        console.print(f"PR Title:    [white]{pr_title}[/white]")
        console.print(f"PR Description:\n[dim]{pr_body}[/dim]\n")

        # Confirm before action
        if not yes:
            confirm = Confirm.ask("Apply these actions (checkout, stage, commit)?", default=True)
            if not confirm:
                console.print("[yellow]Git Auto-Pilot aborted.[/yellow]")
                raise typer.Exit(code=0)

        # Stage and commit
        try:
            console.print("Staging files...")
            repo.git.add(A=True)
            console.print(f"Checking out new branch '[cyan]{branch_name}[/cyan]'...")
            repo.git.checkout("-b", branch_name)
            console.print("Committing changes...")
            repo.git.commit("-m", commit_msg)
            console.print("[green]✓ Staged and committed successfully![/green]")
            generated_branch = branch_name
        except Exception as e:
            console.print(f"[bold red]Git checkout/commit execution failed:[/bold red] {e}")
            raise typer.Exit(code=1)

    # 3. Pushing & PR Creation
    if push:
        try:
            console.print(f"Pushing branch [cyan]{generated_branch}[/cyan] to remote [magenta]origin[/magenta]...")
            repo.git.push("-u", "origin", generated_branch)
            console.print("[green]✓ Push completed successfully![/green]")
        except Exception as e:
            console.print(f"[bold yellow]Warning: Failed to push to remote origin:[/bold yellow] {e}")
            console.print("[yellow]Proceeding to generate PR link anyway...[/yellow]")

        # GitHub CLI integration
        gh_path = shutil.which("gh")
        if gh_path:
            console.print("\n[cyan]GitHub CLI (gh) detected. Attempting to create PR...[/cyan]")
            try:
                # Run `gh pr create`
                cmd = ["gh", "pr", "create", "--title", pr_title, "--body", pr_body]
                pr_result = subprocess.run(cmd, capture_output=True, text=True)
                if pr_result.returncode == 0:
                    console.print("\n[bold green]✓ Pull Request created successfully via GitHub CLI![/bold green]")
                    console.print(pr_result.stdout)
                    raise typer.Exit(code=0)
                else:
                    console.print(f"[bold yellow]Warning: gh pr create returned non-zero:[/bold yellow]\n{pr_result.stderr}")
            except Exception as e:
                console.print(f"[bold yellow]Warning: GitHub CLI execution failed:[/bold yellow] {e}")

        # Fallback Markdown comparison URL
        try:
            remote_url = repo.remotes.origin.url
            repo_web_url = _parse_github_url(remote_url)
            if repo_web_url:
                title_enc = urllib.parse.quote(pr_title)
                body_enc = urllib.parse.quote(pr_body)
                pr_link = f"{repo_web_url}/compare/main...{generated_branch}?expand=1&title={title_enc}&body={body_enc}"
                
                console.print(
                    Panel(
                        f"[bold green]✓ Pull Request Setup Ready![/bold green]\n\n"
                        f"Open the link below to review and create your PR:\n"
                        f"[bold white]{pr_link}[/bold white]",
                        title="[bold green]DevOps Auto-Pilot[/bold green]",
                        border_style="green",
                        expand=False
                    )
                )
            else:
                console.print("\n[yellow]Could not resolve remote origin URL for compare link generation.[/yellow]")
        except Exception as e:
            logger.bind(category="cli").debug(f"Failed to generate compare link: {e}")
