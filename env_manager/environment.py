"""
Environment Module

This module provides the Environment class for representing Python environments.
"""

import os
import re
import sys
from typing import Optional, Any, Dict


class Environment:
    """
    Python environment information and paths.
    
    Represents a Python environment (virtual or local) with all its relevant paths
    and properties.
    
    Attributes:
        name: Environment name (derived from directory name)
        root: Root directory of the environment
        bin: Directory containing executables (Scripts on Windows, bin on Unix)
        lib: Directory containing libraries
        python: Path to the Python executable
        is_virtual: Whether the environment is a virtual environment
    """
    
    def __init__(self, path: Optional[str] = None, **kwargs):
        """Initialize an Environment instance."""
        # Direct attribute initialization (for advanced use cases)
        if kwargs:
            for key, value in kwargs.items():
                setattr(self, key, value)
            return

        # Determine environment root path
        self.root = os.path.abspath(
            path or os.environ.get("VIRTUAL_ENV") or sys.prefix
        )
        
        # Set platform-specific paths
        is_windows = os.name == "nt"
        self.bin = os.path.join(self.root, "Scripts" if is_windows else "bin")
        self.lib = os.path.join(self.root, "Lib" if is_windows else "lib")
        self.python = os.path.join(self.bin, "python.exe" if is_windows else "python")
        
        # Use system executable for non-virtual environments
        self.is_virtual = not self.is_local(self.root)
        if not self.is_virtual:
            self.python = sys.executable
                
        # Extract environment name from directory
        self.name = os.path.basename(self.root)

    @staticmethod
    def is_local(path: str) -> bool:
        """Determine if a path points to a local Python installation."""
        patterns = {
            "nt": [  # Windows patterns
                r"Python\d+",
                r"AppData\\Local\\Programs\\Python\\Python\d+",
                r"(Ana|Mini)conda3"
            ],
            "posix": [  # Unix patterns
                r"/usr(/local)?$",
                r"/usr(/local)?/bin$",
                r"/opt/homebrew/bin$",
                r"/Library/Frameworks/Python\.framework",
                r"/(ana|mini)conda3?/bin$"
            ]
        }
        os_patterns = patterns.get(os.name, patterns["posix"])
        return any(re.search(pattern, path) for pattern in os_patterns)
        
    @classmethod
    def from_dict(cls, env_dict: Dict[str, Any]) -> 'Environment':
        """Create an Environment instance from a dictionary of attributes."""
        instance = cls.__new__(cls)
        for key, value in env_dict.items():
            setattr(instance, key, value)
        return instance