import os
import ast
import typer
from pathlib import Path
from typing import Dict, Any, List
from rich.console import Console
from rich.tree import Tree
from rich.panel import Panel

def find_models_and_routes(directory: Path) -> Dict[str, Any]:
    """Scan and parse Python files for database models and REST API router paths."""
    results: Dict[str, Any] = {
        "models": {},
        "routes": []
    }
    
    exclude_dirs = {".git", ".venv", "venv", "__pycache__", "tests", "build", "dist"}
    
    for root, dirs, files in os.walk(directory):
        dirs_list: List[str] = dirs  # type: ignore[assignment]
        dirs_list[:] = [d for d in dirs_list if d not in exclude_dirs]
        for file in files:
            if not file.endswith(".py"):
                continue
            file_path = Path(root) / file
            try:
                rel_path = file_path.relative_to(directory).as_posix()
            except Exception:
                rel_path = file_path.name
            
            try:
                content = file_path.read_text(encoding="utf-8", errors="replace")
                tree = ast.parse(content, filename=str(file_path))
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        is_model = False
                        for base in node.bases:
                            if isinstance(base, ast.Name) and base.id in ("Base", "Model", "DeclarativeBase", "BaseModel"):
                                is_model = True
                                break
                        
                        fields = []
                        for subnode in node.body:
                            if isinstance(subnode, ast.Assign):
                                for target in subnode.targets:
                                    if isinstance(target, ast.Name):
                                        val = subnode.value
                                        if isinstance(val, ast.Call):
                                            func_name = ""
                                            if isinstance(val.func, ast.Name):
                                                func_name = val.func.id
                                            elif isinstance(val.func, ast.Attribute):
                                                func_name = val.func.attr
                                            
                                            if func_name in ("Column", "Field", "relationship", "ForeignKey"):
                                                is_model = True
                                                fields.append(target.id)
                                                
                        if is_model:
                            if rel_path not in results["models"]:
                                results["models"][rel_path] = []
                            results["models"][rel_path].append({
                                "name": node.name,
                                "fields": fields
                            })
                            
                    elif isinstance(node, ast.FunctionDef):
                        for dec in node.decorator_list:
                            dec_str = ""
                            target_dec = dec
                            if isinstance(dec, ast.Call):
                                target_dec = dec.func
                            
                            if isinstance(target_dec, ast.Attribute):
                                if isinstance(target_dec.value, ast.Name):
                                    dec_str = f"{target_dec.value.id}.{target_dec.attr}"
                            elif isinstance(target_dec, ast.Name):
                                dec_str = target_dec.id
                                
                            if any(x in dec_str for x in ("router.", "app.", "api_route")):
                                results["routes"].append({
                                    "file": rel_path,
                                    "function": node.name,
                                    "decorator": dec_str
                                })
            except Exception:
                pass
                
    return results

def schema(ctx: typer.Context) -> None:
    """Scan workspace code structure and display database schema & REST endpoint maps."""
    console = Console()
    cwd = Path.cwd().resolve()
    
    console.print(f"[yellow]Scanning workspace schema inside [bold]{cwd}[/bold]...[/yellow]")
    scan_results = find_models_and_routes(cwd)
    
    root_tree = Tree("[bold green]Workspace Structural Schema Map[/bold green]")
    
    models_node = root_tree.add("[bold cyan]Database Models & Schemas[/bold cyan]")
    if scan_results["models"]:
        for file, classes in scan_results["models"].items():
            file_node = models_node.add(f"[white]{file}[/white]")
            for cls in classes:
                cls_node = file_node.add(f"[yellow]Class: {cls['name']}[/yellow]")
                for f in cls["fields"]:
                    cls_node.add(f"[dim green]Field: {f}[/dim green]")
    else:
        models_node.add("[dim]No database models found in python files[/dim]")
        
    routes_node = root_tree.add("[bold magenta]REST API Router Endpoints[/bold magenta]")
    if scan_results["routes"]:
        for r in scan_results["routes"]:
            routes_node.add(f"[dim white]{r['file']}[/dim white] -> [cyan]@{r['decorator']}[/cyan] -> [green]{r['function']}()[/green]")
    else:
        routes_node.add("[dim]No REST endpoints / router decorators found[/dim]")
        
    console.print(Panel(root_tree, border_style="blue", expand=False))
