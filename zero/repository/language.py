from pathlib import Path
from typing import List, Dict, Any

EXTENSION_TO_LANGUAGE = {
    ".py": "Python",
    ".js": "JavaScript",
    ".mjs": "JavaScript",
    ".cjs": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".jsx": "JavaScript",
    ".java": "Java",
    ".go": "Go",
    ".rs": "Rust",
    ".php": "PHP",
    ".cs": "C#",
    ".tf": "Terraform",
    ".tfvars": "Terraform",
}

def detect_languages(scanned_files: List[Dict[str, Any]], repo_path: Path) -> Dict[str, int]:
    """
    Counts files of each supported language.
    Specifically checks names (like Dockerfile) and signatures if needed.
    """
    lang_counts: Dict[str, int] = {}
    
    for file_info in scanned_files:
        rel_path = file_info["relative_path"]
        ext = file_info["extension"]
        file_name = Path(rel_path).name
        
        detected_lang = None
        
        # Check explicit filename-based detection first
        if file_name == "Dockerfile" or file_name.endswith(".dockerfile"):
            detected_lang = "Docker"
        elif ext in EXTENSION_TO_LANGUAGE:
            detected_lang = EXTENSION_TO_LANGUAGE[ext]
        elif ext in {".yaml", ".yml"}:
            # Check if it could be Kubernetes configuration
            full_path = repo_path / rel_path
            if full_path.exists():
                try:
                    # Read first 1KB safely
                    with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read(1024)
                    if "apiVersion:" in content and "kind:" in content:
                        detected_lang = "Kubernetes"
                except Exception:
                    pass
                    
        if detected_lang:
            lang_counts[detected_lang] = lang_counts.get(detected_lang, 0) + 1
            
    return lang_counts
