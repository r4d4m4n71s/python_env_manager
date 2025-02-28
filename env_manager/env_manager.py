"""
Environment Manager Module

This module provides functionality to manage Python environments, both local and virtual.
It handles environment creation, activation, deactivation, and package management.
"""

import os
import sys
import re
import shutil
import subprocess
import logging
from venv import EnvBuilder
from typing import Optional, Any, Dict, List, Union

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
                r"/usr/(local/)?bin$",
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

class EnvManager:
    """
    Environment Manager for handling Python environments.
    
    Provides functionality to manage both local and virtual Python environments,
    including creation, activation, deactivation, and package management and 
    tasks execution.
    """
    
    def __init__(
        self,
        path: Optional[str] = None,
        clear: bool = False,
        env_builder: Optional[EnvBuilder] = None,
        logger: Optional[logging.Logger] = None
    ) -> None:
        """Initialize an EnvManager instance."""
        self.logger = logger or logging.getLogger(__name__)
        self.env = Environment(path)
        self.env_builder = env_builder
        self._original_env = dict(os.environ)
        self._original_path = list(sys.path)
        
        # Create virtual environment if needed
        if self.env.is_virtual:
            self._create_venv(clear=clear)

    def _create_venv(self, clear: bool = False) -> 'EnvManager':
        """Create a virtual environment at the specified path."""
        if not self.env_builder:
            self.env_builder = EnvBuilder(
                system_site_packages=False,
                clear=clear,
                with_pip=True,
                upgrade_deps=True
            )
        try:
            os.makedirs(self.env.root, exist_ok=True)
            self.env_builder.create(self.env.root)
            self.logger.info(f"Created virtual environment at {self.env.root}")
        except Exception as e:
            self.logger.error(f"Failed to create virtual environment: {e}")
            raise RuntimeError(f"Failed to create virtual environment: {e}") from e
        return self

    def remove(self) -> None:
        """Remove the virtual environment if it exists."""
        if not self.env.is_virtual:
            return
            
        if self.is_active():
            self.deactivate()
            
        try:
            shutil.rmtree(self.env.root)
            self.logger.info(f"Removed virtual environment at {self.env.root}")
        except Exception as e:
            self.logger.error(f"Failed to remove virtual environment: {e}")
            raise RuntimeError(f"Failed to remove virtual environment: {e}") from e

    def run(self, *cmd_args: str, capture_output: bool = True, **kwargs: Any) -> subprocess.CompletedProcess:
        """Execute a command in the environment context."""
        if not cmd_args:
            raise ValueError("No command provided")
            
        # Set default kwargs
        kwargs.setdefault('text', True)
        kwargs.setdefault('check', True)
        kwargs.setdefault('capture_output', capture_output)
        
        try:
            is_windows = os.name == "nt"
            cmd_list = [str(arg) for arg in cmd_args]
            
            # Determine command execution strategy
            activate_script = os.path.join(
                self.env.bin,
                "activate.bat" if is_windows else "activate"
            )
            
            if os.path.exists(activate_script):
                # Virtual environment with activation script
                if is_windows:
                    shell_cmd = f'"{activate_script}" && {" ".join(cmd_list)}'
                    kwargs['shell'] = True
                else:
                    shell_cmd = f'source "{activate_script}" && {" ".join(cmd_list)}'
                    kwargs['executable'] = '/bin/bash'
                    kwargs['shell'] = True
            else:
                # Local Python or no activation script
                kwargs['shell'] = False
                
                if cmd_list and cmd_list[0].lower() == 'python':
                    # Use environment's Python executable
                    python_exe = self.env.python if os.path.exists(self.env.python) else sys.executable
                    shell_cmd = [python_exe] + cmd_list[1:]
                else:
                    # Look for command in environment's bin directory
                    cmd_path = os.path.join(
                        self.env.bin,
                        cmd_list[0] + (".exe" if is_windows else "")
                    )
                    if not os.path.exists(cmd_path):
                        cmd_path = cmd_list[0]
                    shell_cmd = [cmd_path] + cmd_list[1:]
            
            # Execute command
            result = subprocess.run(shell_cmd, env=os.environ, **kwargs)
            self.logger.info(f"Successfully executed command: {' '.join(cmd_list)}")
            return result
            
        except subprocess.CalledProcessError:
            # Let CalledProcessError propagate for proper error handling
            self.logger.error(f"Command failed: {' '.join(cmd_list)}")
            raise
        except Exception as e:
            self.logger.error(f"Failed to execute command: {e}")
            raise RuntimeError(f"Failed to execute command: {e}") from e

    def activate(self) -> None:
        """Activate the Python environment."""
        if self.is_active():
            return
            
        # Store original environment state
        self._original_env = dict(os.environ)
        self._original_path = list(sys.path)
        
        # Skip activation for non-virtual environments
        if not self.env.is_virtual:
            return
            
        try:
            # Set environment variables
            os.environ["VIRTUAL_ENV"] = self.env.root
            
            # Update PATH
            if self.env.bin not in os.environ.get("PATH", ""):
                os.environ["PATH"] = self.env.bin + os.pathsep + os.environ.get("PATH", "")
            
            # Update Python path
            site_packages = os.path.join(self.env.lib, "site-packages")
            for path in [site_packages, self.env.lib]:
                if path not in sys.path:
                    sys.path.insert(0, path)
            
            self.logger.info(f"Activated environment at {self.env.root}")
            
        except Exception as e:
            # Restore original state on failure
            os.environ.clear()
            os.environ.update(self._original_env)
            sys.path[:] = self._original_path
            self.logger.error(f"Failed to activate environment: {e}")
            raise RuntimeError(f"Failed to activate environment: {e}") from e

    def deactivate(self) -> None:
        """Deactivate the current Python environment and restore original state."""
        if not self.is_active():
            return
            
        try:
            # Restore original environment state
            os.environ.clear()
            os.environ.update(self._original_env)
            sys.path[:] = self._original_path
            self.logger.info(f"Deactivated environment at {self.env.root}")
        except Exception as e:
            self.logger.error(f"Failed to deactivate environment: {e}")
            raise RuntimeError(f"Failed to deactivate environment: {e}") from e

    def is_active(self) -> bool:
        """Check if the current environment is active."""
        if not self.env.is_virtual:
            return False
            
        return (
            "VIRTUAL_ENV" in os.environ and
            os.path.abspath(os.environ["VIRTUAL_ENV"]) == os.path.abspath(self.env.root)
        )
            
    def __enter__(self) -> 'EnvManager':
        """Context manager entry point that activates the environment."""
        self.activate()
        return self
        
    def __exit__(self, exc_type: Optional[type], exc_val: Optional[Exception],
                 exc_tb: Optional[Any]) -> None:
        """Context manager exit point that deactivates the environment."""
        self.deactivate()

    def install_pkg(self, package: str) -> 'InstallPkgContextManager':
        """
        Install a package in the Python environment.
        
        Can be used as a regular method or as a context manager:
        - Regular: env_manager.install_pkg("package")
        - Context: with env_manager.install_pkg("package"): ...
        """
        return InstallPkgContextManager(self, package)
        
class InstallPkgContextManager:
    """Context manager for temporary package installation."""
    
    def __init__(self, env_manager: 'EnvManager', package: str):
        """Initialize and install the package."""
        self.env_manager = env_manager
        self.package = package
        
        try:
            self.env_manager.run("pip", "install", self.package)
        except subprocess.CalledProcessError as e:
            self.env_manager.logger.error(f"Failed to install package {self.package}")
            raise RuntimeError(f"Failed to install package {self.package}") from e
            
    def __enter__(self) -> 'InstallPkgContextManager':
        """Context manager entry."""
        return self
            
    def __exit__(self, exc_type: Optional[type], exc_val: Optional[Exception],
                 exc_tb: Optional[Any]) -> None:
        """Context manager exit - uninstall the package."""
        try:
            self.env_manager.run("pip", "uninstall", "-y", self.package)
        except subprocess.CalledProcessError as e:
            self.env_manager.logger.error(f"Failed to uninstall package {self.package}")
            raise RuntimeError(f"Failed to uninstall package {self.package}") from e