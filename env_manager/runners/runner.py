"""
Standard Runner Module

This module provides the standard runner for executing commands in a virtual environment.
"""

import os
import subprocess
from typing import Any

from env_manager.runners.irunner import IRunner
from env_manager import env_manager

class Runner(IRunner):
    """
    Standard command runner for executing commands in a virtual environment.
    
    This runner uses the environment manager's _prepare_command method to prepare
    commands for execution in the environment context.
    """
    
    def __init__(self):
        """Initialize a Runner instance."""
        self.env_manager = None
        
    def with_env(self, env_manager: 'env_manager.EnvManager') -> 'Runner':
        """
        Configure the runner with an environment manager.
        
        Args:
            env_manager: The environment manager to use for command execution.
            
        Returns:
            Runner: The configured runner instance (self).
        """
        self.env_manager = env_manager
        return self
        
    def run(self, *cmd_args: str, capture_output: bool = True, **kwargs: Any) -> subprocess.CompletedProcess:
        """
        Execute a command in the environment context.
        
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
        if not self.env_manager:
            raise ValueError("Runner not configured with an environment manager")
            
        try:
            # Prepare the command
            shell_cmd, run_kwargs = self.env_manager._prepare_command(
                *cmd_args, capture_output=capture_output, **kwargs
            )
            
            # Execute command
            result = subprocess.run(shell_cmd, env=os.environ, **run_kwargs)
            self.env_manager.logger.info(f"Successfully executed command: {' '.join([str(arg) for arg in cmd_args])}")
            return result
            
        except subprocess.CalledProcessError as e:
            # Let CalledProcessError propagate for proper error handling
            self.env_manager.logger.error(f"Command failed: {' '.join([str(arg) for arg in cmd_args])}, return code: {e.returncode}")
            if e.stdout:
                self.env_manager.logger.error(f"Command stdout: {e.stdout}")
            if e.stderr:
                self.env_manager.logger.error(f"Command stderr: {e.stderr}")
            raise
        except Exception as e:
            self.env_manager.logger.error(f"Failed to execute command: {e}")
            raise RuntimeError(f"Failed to execute command: {e}") from e