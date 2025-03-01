"""
Pytest configuration file for test setup and teardown.
Handles cleanup of temporary test directories that may be left behind.
"""

import os
import shutil
import pytest
import tempfile
import time
from pathlib import Path

def pytest_sessionfinish(session, exitstatus):
    """
    Clean up pytest temporary directories after the test session completes.
    This ensures no pytest-* directories are left behind.
    """
    temp_dir = Path(tempfile.gettempdir())
    
    # Wait briefly to ensure file operations complete
    time.sleep(0.5)
    
    # Look for any pytest-of-* directories in the temp directory
    for pytest_root in temp_dir.glob("pytest-of-*"):
        if pytest_root.is_dir():
            # Loop through all pytest-* subdirectories
            for tmp_dir in pytest_root.glob("pytest-*"):
                try:
                    # Use robust removal with retry
                    _safe_remove_path(tmp_dir)
                except Exception as e:
                    print(f"Warning: Failed to remove temporary directory {tmp_dir}: {e}")
            
            # Try to remove the parent directory if empty
            try:
                if pytest_root.exists() and not any(pytest_root.iterdir()):
                    _safe_remove_path(pytest_root)
            except Exception:
                pass

def _safe_remove_path(path, max_retries=3, retry_delay=0.5):
    """
    Safely remove a directory with retry mechanism to handle file locking issues.
    
    Args:
        path: Path to remove
        max_retries: Maximum number of removal attempts
        retry_delay: Delay between retry attempts in seconds
    """
    if not path.exists():
        return True
        
    for attempt in range(max_retries):
        try:
            if path.is_file():
                path.unlink()
            else:
                shutil.rmtree(path, ignore_errors=True)
            return True
        except (PermissionError, OSError):
            # Wait before retry to allow file locks to be released
            time.sleep(retry_delay)
    
    # If we couldn't remove it after retries, attempt with ignore_errors
    try:
        shutil.rmtree(path, ignore_errors=True)
        return True
    except:
        return False