import json
from pathlib import Path
from zero.services.ai import AIService
from zero.services.config import ZeroSettings

def test_get_system_prompt_no_cache(tmp_path):
    settings = ZeroSettings()
    ai = AIService(settings, tmp_path)
    
    prompt = ai.get_system_prompt(Path("/workspace"))
    assert "Zero Action" in prompt
    assert "CURRENT WORKSPACE CONTEXT" not in prompt

def test_get_system_prompt_with_cache(tmp_path):
    settings = ZeroSettings()
    ai = AIService(settings, tmp_path)
    
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    cache_file = cache_dir / "repo_summary.json"
    
    summary_data = {
        "total_files": 42,
        "total_size_bytes": 1000,
        "languages": {"Python": 10, "Markdown": 2},
        "frameworks": ["FastAPI"],
        "git_branch": "feature-branch",
        "git_is_dirty": True
    }
    cache_file.write_text(json.dumps(summary_data))
    
    prompt = ai.get_system_prompt(Path("/workspace"))
    assert "Zero Action" in prompt
    assert "CURRENT WORKSPACE CONTEXT" in prompt
    assert "Total files: 42" in prompt
    assert "Languages: Python (10 files), Markdown (2 files)" in prompt
    assert "Frameworks: FastAPI" in prompt
    assert "Git branch: feature-branch" in prompt
    assert "Git status: dirty" in prompt
