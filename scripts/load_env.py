#!/usr/bin/env python3
"""
VELOS Environment Loader
Loads environment variables from .env file or sets defaults
"""

import os
import sys
from pathlib import Path
from typing import Dict, Optional

def load_env_file(env_path: Path) -> Dict[str, str]:
    """Load environment variables from .env file"""
    env_vars = {}
    
    if not env_path.exists():
        return env_vars
    
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key.strip()] = value.strip()
    except Exception as e:
        print(f"Warning: Could not load .env file: {e}")
    
    return env_vars

def setup_velos_env(root_path: Optional[str] = None) -> Dict[str, str]:
    """Setup VELOS environment variables"""
    
    # Determine root path
    if root_path is None:
        root_path = os.getenv('VELOS_ROOT', 'C:/giwanos')
    
    root = Path(root_path)
    
    # Default environment variables
    default_env = {
        'VELOS_ROOT': str(root),
        'VELOS_MODE': 'dev',
        'VELOS_REPORT_DIR': str(root / 'data' / 'reports'),
        'EMAIL_ENABLED': '0',
        'VELOS_DB_PATH': str(root / 'data' / 'velos.db'),
        'VELOS_MEMORY_DB_PATH': str(root / 'data' / 'memory' / 'velos_memory.db'),
        'VELOS_LOG_LEVEL': 'INFO',
        'VELOS_LOG_FILE': str(root / 'logs' / 'velos.log')
    }
    
    # Load from .env file if it exists
    env_file = root / '.env'
    file_env = load_env_file(env_file)
    
    # Merge environment variables (file overrides defaults)
    final_env = {**default_env, **file_env}
    
    # Set environment variables
    for key, value in final_env.items():
        os.environ[key] = value
    
    return final_env

def get_velos_env(key: str, default: Optional[str] = None) -> str:
    """Get a VELOS environment variable"""
    return os.getenv(key, default)

def print_velos_env():
    """Print current VELOS environment variables"""
    velos_keys = [k for k in os.environ.keys() if k.startswith('VELOS_')]
    velos_keys.extend(['EMAIL_ENABLED'])
    
    print("VELOS Environment Variables:")
    for key in sorted(velos_keys):
        value = os.getenv(key, 'NOT_SET')
        print(f"  {key}: {value}")

if __name__ == "__main__":
    # Setup environment
    env_vars = setup_velos_env()
    
    # Print environment
    print_velos_env()
    
    # Test environment
    print(f"\nTest: VELOS_ROOT = {get_velos_env('VELOS_ROOT')}")
    print(f"Test: VELOS_MODE = {get_velos_env('VELOS_MODE')}")
