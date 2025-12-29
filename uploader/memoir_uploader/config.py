"""
Configuration management for memoir-uploader.
"""

import json
from pathlib import Path
from typing import Dict, Any

CONFIG_DIR = Path.home() / ".memoir-uploader"
CONFIG_FILE = CONFIG_DIR / "config.json"


def load_config() -> Dict[str, Any]:
    """Load configuration from file."""
    if not CONFIG_FILE.exists():
        return {}
    
    try:
        return json.loads(CONFIG_FILE.read_text())
    except (json.JSONDecodeError, IOError):
        return {}


def save_config(config: Dict[str, Any]) -> None:
    """Save configuration to file."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    
    # Merge with existing config
    existing = load_config()
    existing.update(config)
    
    CONFIG_FILE.write_text(json.dumps(existing, indent=2))
    
    # Set restrictive permissions (owner read/write only)
    CONFIG_FILE.chmod(0o600)
