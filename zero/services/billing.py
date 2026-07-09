import os
import uuid
import litellm
from pathlib import Path
from typing import Dict, Any, Optional
from zero.storage.sqlite import SQLiteDatabase

def log_tokens(model: str, prompt_tokens: int, completion_tokens: int, db_path: Optional[Path] = None) -> float:
    """Calculate the cost using LiteLLM and log the token usage to the SQLite DB."""
    if db_path is None:
        home = os.environ.get("ZERO_HOME")
        if home:
            config_dir = Path(home)
        else:
            config_dir = Path.home() / ".zero"
        db_path = config_dir / "memory.db"
    
    clean_model = model
    # Clean typical provider prefixes to match LiteLLM's internal naming map
    if "/" in model:
        parts = model.split("/")
        # If openrouter/google/gemini-2.0-flash, use google/gemini-2.0-flash
        if len(parts) > 2:
            clean_model = "/".join(parts[1:])
        else:
            # e.g., gemini/gemini-1.5-flash -> gemini-1.5-flash
            clean_model = parts[-1]
            
    try:
        prompt_cost, completion_cost = litellm.cost_per_token(
            model=clean_model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens
        )
        total_cost = prompt_cost + completion_cost
    except Exception:
        # Fallback estimation if model not found in registry (e.g., $10 per 1M tokens)
        total_cost = (prompt_tokens + completion_tokens) * 0.00001
        
    try:
        db = SQLiteDatabase(db_path)
        db.execute(
            "INSERT INTO billing_log (id, model, prompt_tokens, completion_tokens, cost) VALUES (?, ?, ?, ?, ?);",
            (str(uuid.uuid4())[:8], model, prompt_tokens, completion_tokens, total_cost)
        )
    except Exception:
        # Fail silently to prevent interrupting application flows on database locks
        pass
        
    return total_cost

def get_billing_summary(db_path: Optional[Path] = None) -> Dict[str, Any]:
    """Retrieve summarized statistics from the billing logs."""
    if db_path is None:
        home = os.environ.get("ZERO_HOME")
        config_dir = Path(home) if home else Path.home() / ".zero"
        db_path = config_dir / "memory.db"
        
    try:
        db = SQLiteDatabase(db_path)
        summary = db.fetch_one(
            "SELECT COUNT(*) as total_calls, SUM(prompt_tokens) as total_prompt_tokens, SUM(completion_tokens) as total_completion_tokens, SUM(cost) as total_cost FROM billing_log;"
        )
    except Exception:
        return {
            "total_calls": 0,
            "total_prompt_tokens": 0,
            "total_completion_tokens": 0,
            "total_cost": 0.0
        }
        
    if not summary or summary["total_calls"] == 0:
        return {
            "total_calls": 0,
            "total_prompt_tokens": 0,
            "total_completion_tokens": 0,
            "total_cost": 0.0
        }
        
    return {
        "total_calls": summary["total_calls"],
        "total_prompt_tokens": summary["total_prompt_tokens"] or 0,
        "total_completion_tokens": summary["total_completion_tokens"] or 0,
        "total_cost": summary["total_cost"] or 0.0
    }
