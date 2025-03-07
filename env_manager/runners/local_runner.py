"""
Local Runner Module

This module provides a runner for executing commands with the local Python installation.
"""

import sys
import subprocess
import logging
from typing import Any

from env_manager.env_local import PythonLocal
from env_manager.runners.irunner import IRunner
from env_manager import env_manager

class LocalRunner(IRunner):
    """
    Local command runner for executing commands with the system Python.
    
    This runner uses the local Python installation, bypassing any virtual environment.
    """
    
    def __init__(self):
        """Initialize a LocalRunner instance."""
        self.logger = logging.getLogger(__name__)
        
    def with_env(self, env_manager: 'env_manager.EnvManager') -> 'LocalRunner':
        """
        Configure the runner with an environment manager.
        
        For LocalRunner, the environment manager is not used for command execution,
        but the logger is used for consistency.
        
        Args:
            env_manager: The environment manager to use for logging.
            
        Returns:
            LocalRunner: The configured runner instance (self).
        """
        self.logger = env_manager.logger
        return self
        
    def run(self, *cmd_args: str, capture_output: bool = True, **kwargs: Any) -> subprocess.CompletedProcess:
        """
        Execute a command using the local Python distribution.
        
        Args:
            *cmd_args: Command and arguments as separate strings.
            capture_output: Whether to capture command output (default: True).
            **kwargs: Additional arguments to pass to subprocess.run.
            
        Returns:
            subprocess.CompletedProcess: Result of the command execution.
            
        Raises:
            ValueError: If no command is provided.
            RuntimeError: If command execution fails.
        """
        if not cmd_args:
            raise ValueError("No command provided")
            
        # Set default kwargs
        kwargs.setdefault('text', True)
        kwargs.setdefault('check', True)
        kwargs.setdefault('capture_output', capture_output)
        
        # Find the local Python executable
        python_local = PythonLocal()
        base_exe = python_local.find_base_executable()
        
        if not base_exe:
            base_exe = sys.executable  # Fallback to current Python if base not found
            
        cmd_list = [str(arg) for arg in cmd_args]
        
        try:
            # If the command starts with 'python', use the base executable instead
            if cmd_list and cmd_list[0].lower() == 'python':
                shell_cmd = [base_exe] + cmd_list[1:]
            else:
                # For non-Python commands, use them directly
                shell_cmd = cmd_list
            
            # Execute command
            result = subprocess.run(shell_cmd, **kwargs)
            self.logger.info(f"Successfully executed command with local Python: {' '.join(cmd_list)}")
            return result
            
        except subprocess.CalledProcessError as e:
            # Let CalledProcessError propagate for proper error handling
            self.logger.error(f"Local command failed: {' '.join(cmd_list)}, return code: {e.returncode}")
            if hasattr(e, 'stdout') and e.stdout:
                self.logger.error(f"Command stdout: {e.stdout}")
            if hasattr(e, 'stderr') and e.stderr:
                self.logger.error(f"Command stderr: {e.stderr}")
            raise
        except Exception as e:
            self.logger.error(f"Failed to execute local command: {e}")
            raise RuntimeError(f"Failed to execute local command: {e}") from e