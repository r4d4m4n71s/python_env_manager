"""
IRunner Interface Module

This module defines the interface for command runners.
"""

import subprocess
from abc import ABC, abstractmethod
from typing import Any

from env_manager import env_manager


class IRunner(ABC):
    """
    Interface for command runners.
    
    This abstract base class defines the interface for all command runners.
    Implementations handle different execution strategies (standard, progress, local).
    """
    
    @abstractmethod
    def with_env(self, env_manager: 'env_manager.EnvManager') -> 'IRunner':
        """
        Configure the runner with an environment manager.
        
        Args:
            env_manager: The environment manager to use for command execution.
            
        Returns:
            IRunner: The configured runner instance (self).
        """
        pass
    
    @abstractmethod
    def run(self, *cmd_args: str, **kwargs: Any) -> subprocess.CompletedProcess:
        """
        Execute a command.
        
        Args:
            *cmd_args: Command and arguments as separate strings.
            **kwargs: Additional arguments to pass to subprocess.run.
            
        Returns:
            subprocess.CompletedProcess: Result of the command execution.
            
        Raises:
            ValueError: If no command is provided.
            RuntimeError: If command execution fails.
        """
        pass