"""CLI subcommand and wizard to manage shell aliases and keyboard shortcuts for Zero Action."""

import os
import sys
from pathlib import Path
from typing import List, Dict, Optional
import typer
from rich.console import Console
from rich.table import Table

def _get_shell_profiles() -> List[Path]:
    """Return list of potential shell profile paths to update based on OS."""
    profiles = []
    home = Path.home()
    
    if sys.platform == "win32":
        # PowerShell profiles
        profiles.append(home / "Documents" / "WindowsPowerShell" / "Microsoft.PowerShell_profile.ps1")
        profiles.append(home / "Documents" / "PowerShell" / "Microsoft.PowerShell_profile.ps1")
        # For OneDrive redirected folders
        profiles.append(home / "OneDrive" / "Documents" / "WindowsPowerShell" / "Microsoft.PowerShell_profile.ps1")
        profiles.append(home / "OneDrive" / "Documents" / "PowerShell" / "Microsoft.PowerShell_profile.ps1")
    else:
        # Bash / Zsh profiles
        profiles.append(home / ".bashrc")
        profiles.append(home / ".zshrc")
        profiles.append(home / ".bash_profile")
        profiles.append(home / ".profile")
        
    return [p for p in profiles]

def _read_aliases_from_profile(profile_path: Path) -> Dict[str, str]:
    """Parse existing Zero Action aliases from a profile file."""
    aliases = {}
    if not profile_path.exists():
        return aliases
        
    try:
        content = profile_path.read_text(encoding="utf-8")
        in_block = False
        for line in content.splitlines():
            line_strip = line.strip()
            if "ZERO ACTION ALIASES START" in line_strip:
                in_block = True
                continue
            if "ZERO ACTION ALIASES END" in line_strip:
                in_block = False
                break
                
            if in_block:
                if sys.platform == "win32":
                    # Parse: function name { zero command @args }
                    match = re.match(r'function\s+(\w+)\s*\{\s*zero\s+(.*?)\s*@args\s*\}', line_strip)
                    if match:
                        aliases[match.group(1)] = match.group(2)
                else:
                    # Parse: alias name='zero command'
                    match = re.match(r"alias\s+(\w+)=['\"]zero\s+(.*?)['\"]", line_strip)
                    if match:
                        aliases[match.group(1)] = match.group(2)
    except Exception:
        pass
    return aliases

import re

def _write_aliases_to_profile(profile_path: Path, aliases: Dict[str, str]) -> None:
    """Write zero aliases block into the shell profile."""
    # Ensure parent directory exists
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Read existing profile content
    content = ""
    if profile_path.exists():
        try:
            content = profile_path.read_text(encoding="utf-8")
        except Exception:
            pass
            
    # Prepare aliases block
    lines = ["# >>> ZERO ACTION ALIASES START >>>"]
    for name, cmd in sorted(aliases.items()):
        if sys.platform == "win32":
            lines.append(f"function {name} {{ zero {cmd} @args }}")
        else:
            lines.append(f"alias {name}='zero {cmd}'")
    lines.append("# <<< ZERO ACTION ALIASES END <<<")
    block_text = "\n".join(lines) + "\n"
    
    # Replace existing block or append to profile
    pattern = re.compile(r'# >>> ZERO ACTION ALIASES START >>>.*?# <<< ZERO ACTION ALIASES END <<<', re.DOTALL)
    if pattern.search(content):
        new_content = pattern.sub(block_text.strip(), content)
    else:
        new_content = content.rstrip() + "\n\n" + block_text
        
    profile_path.write_text(new_content, encoding="utf-8")

def run_shortcut(
    ctx: typer.Context,
    action: str = typer.Argument("list", help="Action to perform: list, add, remove"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Name of the shortcut alias (e.g. zask)"),
    command: Optional[str] = typer.Option(None, "--command", "-c", help="Zero subcommand to map to (e.g. 'ask')"),
) -> None:
    """Manage custom command aliases and shortcuts in your shell profile."""
    console = Console()
    action = action.lower()
    
    profiles = _get_shell_profiles()
    if not profiles:
        console.print("[bold red]Error:[/bold red] No compatible shell profiles found for your system.")
        raise typer.Exit(code=1)
        
    # Read existing configuration from the first profile that exists, or default to empty
    existing_aliases: Dict[str, str] = {}
    for p in profiles:
        if p.exists():
            existing_aliases = _read_aliases_from_profile(p)
            break
            
    if action == "list":
        if not existing_aliases:
            console.print("[yellow]No custom shell shortcuts configured yet.[/yellow]")
            console.print("Use [bold cyan]zero shortcut add -n zask -c ask[/bold cyan] to create one.")
            return
            
        table = Table(title="[bold green]Zero Action Shell Shortcuts[/bold green]", show_header=True, header_style="bold cyan")
        table.add_column("Alias", style="bold white")
        table.add_column("Maps To", style="green")
        
        for k, v in sorted(existing_aliases.items()):
            table.add_row(k, f"zero {v}")
            
        console.print(table)
        
    elif action == "add":
        if not name or not command:
            console.print("[bold red]Error:[/bold red] Both --name (-n) and --command (-c) are required to add a shortcut.")
            raise typer.Exit(code=1)
            
        name = name.strip().lower()
        command = command.strip()
        
        # Clean potential 'zero ' prefix
        if command.startswith("zero "):
            command = command[5:]
            
        existing_aliases[name] = command
        
        updated_count = 0
        for p in profiles:
            try:
                _write_aliases_to_profile(p, existing_aliases)
                updated_count += 1
            except Exception as e:
                console.print(f"[dim]Failed to write to profile {p}: {e}[/dim]")
                
        if updated_count > 0:
            console.print(f"[green]✓ Successfully added shortcut [bold cyan]'{name}'[/bold cyan] mapping to 'zero {command}' in shell profiles.[/green]")
            console.print("[yellow]Please reload/restart your shell terminal for changes to take effect.[/yellow]")
        else:
            console.print("[bold red]Error:[/bold red] Failed to write shortcuts to any shell profiles.")
            raise typer.Exit(code=1)
            
    elif action == "remove":
        if not name:
            console.print("[bold red]Error:[/bold red] Please specify the --name (-n) of the shortcut to remove.")
            raise typer.Exit(code=1)
            
        name = name.strip().lower()
        if name not in existing_aliases:
            console.print(f"[bold red]Error:[/bold red] Shortcut '{name}' not found.")
            raise typer.Exit(code=1)
            
        del existing_aliases[name]
        
        updated_count = 0
        for p in profiles:
            try:
                _write_aliases_to_profile(p, existing_aliases)
                updated_count += 1
            except Exception as e:
                console.print(f"[dim]Failed to update profile {p}: {e}[/dim]")
                
        if updated_count > 0:
            console.print(f"[green]✓ Successfully removed shortcut [bold cyan]'{name}'[/bold cyan] from shell profiles.[/green]")
        else:
            console.print("[bold red]Error:[/bold red] Failed to update shell profiles.")
            raise typer.Exit(code=1)
            
    else:
        console.print(f"[bold red]Error:[/bold red] Unknown action '{action}'. Valid options: list, add, remove")
        raise typer.Exit(code=1)
