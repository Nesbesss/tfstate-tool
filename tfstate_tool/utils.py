"""
Utility functions for tfstate-tool.
"""

import os
import sys
from pathlib import Path
from typing import List

def find_state_files(directory: str = ".") -> List[str]:
    """Find all .tfstate files in a directory."""
    path = Path(directory)
    return [str(f) for f in path.rglob("*.tfstate")]

def validate_state_file_path(state_file: str) -> bool:
    """Validate that a state file path exists and is readable."""
    path = Path(state_file)
    return path.exists() and path.is_file() and os.access(path, os.R_OK)

def get_state_file_size(state_file: str) -> int:
    """Get the size of a state file in bytes."""
    return Path(state_file).stat().st_size

def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"

def confirm_destructive_action(action: str, target: str) -> bool:
    """Get user confirmation for destructive actions."""
    print(f"\n⚠️  WARNING: This will {action} {target}")
    print("This action cannot be easily undone.")
    
    response = input("Type 'yes' to confirm: ").lower().strip()
    return response == 'yes'

def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    import logging
    
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger('tfstate-tool')