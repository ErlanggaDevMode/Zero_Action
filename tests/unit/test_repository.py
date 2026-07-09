import pytest
from zero.repository.scanner import get_gitignore_spec, scan_repository
from zero.repository.language import detect_languages
from zero.repository.dependency import extract_dependencies
from zero.repository.framework import detect_frameworks
from zero.repository.docker import detect_docker
from zero.repository.git import get_git_metrics
from zero.repository.analyzer import analyze_repository

def test_get_gitignore_spec(tmp_path):
    # No .gitignore
    spec = get_gitignore_spec(tmp_path)
    assert spec.match_file("test.py") is False

    # With .gitignore
    gitignore = tmp_path / ".gitignore"
    gitignore.write_text("*.log\ntemp/\n")
    spec = get_gitignore_spec(tmp_path)
    assert spec.match_file("test.log") is True
    assert spec.match_file("main.py") is False
    assert spec.match_file("temp/data.txt") is True

def test_scan_repository(tmp_path):
    # Setup test workspace layout
    (tmp_path / "src").mkdir()
    (tmp_path / ".git").mkdir()
    (tmp_path / ".venv").mkdir()
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "temp").mkdir()

    # Create files
    (tmp_path / "src" / "main.py").write_text("print('hello')")
    (tmp_path / "src" / "utils.py").write_text("def helper(): pass")
    (tmp_path / ".git" / "config").write_text("[core]")
    (tmp_path / ".venv" / "bin_file").write_text("exec")
    (tmp_path / "node_modules" / "some.js").write_text("console.log()")
    (tmp_path / "temp" / "log.txt").write_text("some logs")
    (tmp_path / "readme.md").write_text("# Readme")

    # Gitignore ignoring temp/
    (tmp_path / ".gitignore").write_text("temp/\n")

    files = scan_repository(tmp_path)
    
    # Extract relative paths
    paths = {f["relative_path"] for f in files}
    
    # Should include:
    assert "src/main.py" in paths
    assert "src/utils.py" in paths
    assert "readme.md" in paths
    assert ".gitignore" in paths

    # Should NOT include standard ignored folders and gitignored folders:
    assert ".git/config" not in paths
    assert ".venv/bin_file" not in paths
    assert "node_modules/some.js" not in paths
    assert "temp/log.txt" not in paths

def test_detect_languages(tmp_path):
    scanned_files = [
        {"relative_path": "main.py", "extension": ".py", "size_bytes": 100},
        {"relative_path": "app.js", "extension": ".js", "size_bytes": 150},
        {"relative_path": "index.ts", "extension": ".ts", "size_bytes": 200},
        {"relative_path": "Dockerfile", "extension": "", "size_bytes": 50},
        {"relative_path": "k8s.yaml", "extension": ".yaml", "size_bytes": 100},
    ]

    # Write mock Kubernetes configuration file
    k8s_file = tmp_path / "k8s.yaml"
    k8s_file.write_text("apiVersion: v1\nkind: Pod\nmetadata:\n  name: mypod")

    lang_counts = detect_languages(scanned_files, tmp_path)
    assert lang_counts.get("Python") == 1
    assert lang_counts.get("JavaScript") == 1
    assert lang_counts.get("TypeScript") == 1
    assert lang_counts.get("Docker") == 1
    assert lang_counts.get("Kubernetes") == 1

def test_extract_dependencies(tmp_path):
    # Requirements.txt
    req_file = tmp_path / "requirements.txt"
    req_file.write_text("requests==2.31.0\npytest>=8.0.0\n# comment\n-r other.txt\n")

    # pyproject.toml
    pyproj_file = tmp_path / "pyproject.toml"
    pyproj_file.write_text("""
[project]
dependencies = [
    "typer>=0.12.0",
    "rich"
]
[tool.poetry.dependencies]
python = "^3.12"
click = "^8.1.7"
""")

    # package.json
    pkg_file = tmp_path / "package.json"
    pkg_file.write_text('{"dependencies": {"express": "^4.18.2"}, "devDependencies": {"jest": "^29.7.0"}}')

    # go.mod
    go_file = tmp_path / "go.mod"
    go_file.write_text("module myapp\n\ngo 1.22\n\nrequire github.com/gin-gonic/gin v1.9.1\n")

    # Cargo.toml
    cargo_file = tmp_path / "Cargo.toml"
    cargo_file.write_text("[dependencies]\ntokio = { version = '1.35' }\n")

    scanned_files = [
        {"relative_path": "requirements.txt", "extension": ".txt"},
        {"relative_path": "pyproject.toml", "extension": ".toml"},
        {"relative_path": "package.json", "extension": ".json"},
        {"relative_path": "go.mod", "extension": ".mod"},
        {"relative_path": "Cargo.toml", "extension": ".toml"},
    ]

    deps = extract_dependencies(scanned_files, tmp_path)
    
    assert "requests" in deps
    assert "pytest" in deps
    assert "typer" in deps
    assert "rich" in deps
    assert "click" in deps
    assert "express" in deps
    assert "jest" in deps
    assert "github.com/gin-gonic/gin" in deps
    assert "tokio" in deps

def test_detect_frameworks(tmp_path):
    scanned_files = [
        {"relative_path": "manage.py", "extension": ".py"},
        {"relative_path": "src/App.java", "extension": ".java"},
    ]
    (tmp_path / "src").mkdir(exist_ok=True)
    (tmp_path / "src" / "App.java").write_text("@SpringBootApplication\npublic class App {}")

    dependencies = ["fastapi", "react", "spring-boot-starter-web"]

    frameworks = detect_frameworks(scanned_files, dependencies, tmp_path)
    assert "FastAPI" in frameworks
    assert "React" in frameworks
    assert "Spring Boot" in frameworks
    assert "Django" in frameworks

def test_detect_docker():
    scanned_files = [
        {"relative_path": "Dockerfile", "extension": ""},
        {"relative_path": "docker-compose.yml", "extension": ".yml"},
    ]
    has_docker, has_compose = detect_docker(scanned_files)
    assert has_docker is True
    assert has_compose is True

def test_git_metrics_fallback(tmp_path):
    # Non-git directory
    metrics = get_git_metrics(tmp_path)
    assert metrics["git_branch"] is None
    assert metrics["git_commit_hash"] is None
    assert metrics["git_is_dirty"] is False
    assert metrics["git_uncommitted_changes"] == []
    assert metrics["git_untracked_files"] == []

def test_git_metrics_real(tmp_path):
    try:
        import git
    except ImportError:
        pytest.skip("gitpython not installed")

    # Initialize a real git repo
    repo = git.Repo.init(tmp_path)
    
    # Initial commit is needed to avoid detached/empty repo errors for head check
    test_file = tmp_path / "test.txt"
    test_file.write_text("initial contents")
    repo.index.add(["test.txt"])
    repo.index.commit("Initial commit message")

    metrics = get_git_metrics(tmp_path)
    
    assert metrics["git_branch"] is not None
    assert metrics["git_commit_hash"] is not None
    assert metrics["git_commit_message"] == "Initial commit message"
    assert metrics["git_is_dirty"] is False

    # Make it dirty
    test_file.write_text("updated contents")
    # Add an untracked file
    untracked_file = tmp_path / "untracked.py"
    untracked_file.write_text("print(1)")

    metrics_dirty = get_git_metrics(tmp_path)
    assert metrics_dirty["git_is_dirty"] is True
    assert "test.txt" in metrics_dirty["git_uncommitted_changes"]
    assert "untracked.py" in metrics_dirty["git_untracked_files"]

def test_analyze_repository(tmp_path):
    # Test end to end analysis
    (tmp_path / "main.py").write_text("print('hello')")
    (tmp_path / "requirements.txt").write_text("fastapi==0.100.0\n")
    
    summary = analyze_repository(tmp_path)
    assert summary.total_files == 2
    assert "Python" in summary.languages
    assert "fastapi" in summary.dependencies
    assert "FastAPI" in summary.frameworks
