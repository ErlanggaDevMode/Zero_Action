from pathlib import Path
from typing import List, Dict, Any, Set

FRAMEWORK_DEP_MAPPING = {
    "fastapi": "FastAPI",
    "django": "Django",
    "flask": "Flask",
    "express": "Express",
    "react": "React",
    "next": "Next.js",
    "vue": "Vue",
    "angular": "Angular",
    "svelte": "Svelte",
    "nuxt": "Nuxt.js",
    "gatsby": "Gatsby",
    "nestjs": "NestJS",
    "laravel": "Laravel",
    "spring-boot": "Spring Boot",
    "spring-core": "Spring",
    "gin": "Gin",
    "fiber": "Fiber",
    "actix-web": "Actix-web",
    "rocket": "Rocket",
}

def detect_frameworks(scanned_files: List[Dict[str, Any]], dependencies: List[str], repo_path: Path) -> List[str]:
    """
    Detects frameworks based on:
    1. Extracted dependencies matching known frameworks.
    2. File existence and file patterns (e.g., manage.py, spring boot signatures).
    """
    detected: Set[str] = set()
    
    dep_set = {d.lower() for d in dependencies}
    for dep_key, framework_name in FRAMEWORK_DEP_MAPPING.items():
        if dep_key in dep_set:
            detected.add(framework_name)
            
    for dep in dep_set:
        if "spring-boot" in dep:
            detected.add("Spring Boot")
        elif "nestjs" in dep or "@nestjs" in dep:
            detected.add("NestJS")
            
    file_names = {Path(f["relative_path"]).name for f in scanned_files}
    
    if "manage.py" in file_names:
        detected.add("Django")
        
    for file_info in scanned_files:
        rel_path = file_info["relative_path"]
        name = Path(rel_path).name
        if name in ("pom.xml", "build.gradle", "build.gradle.kts"):
            full_path = repo_path / rel_path
            if full_path.exists():
                try:
                    content = full_path.read_text(encoding="utf-8", errors="ignore")
                    if "spring-boot" in content or "springframework" in content:
                        detected.add("Spring Boot")
                except Exception:
                    pass
                    
        if file_info["extension"] == ".java":
            full_path = repo_path / rel_path
            if full_path.exists():
                try:
                    with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read(1024)
                    if "@SpringBootApplication" in content:
                        detected.add("Spring Boot")
                except Exception:
                    pass
                    
    return sorted(list(detected))
