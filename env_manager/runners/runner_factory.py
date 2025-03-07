"""
Runner Factory Module

This module provides a factory for creating command runners.
"""

from typing import Dict, List, Type
from env_manager.runners.irunner import IRunner

class RunnerFactory:
    """
    Factory for creating command runners.
    
    This static factory allows registering and creating different types of runners
    without modifying the EnvManager class.
    """
    
    _runners: Dict[str, Type[IRunner]] = {}
    
    @classmethod
    def register(cls, name: str, runner_class: Type[IRunner]) -> None:
        """
        Register a runner class with a name.
        
        Args:
            name: The name to register the runner under.
            runner_class: The runner class to register.
        """
        cls._runners[name] = runner_class
    
    @classmethod
    def create(cls, name: str) -> IRunner:
        """
        Create a runner instance by name.
        
        Args:
            name: The name of the runner to create.
            
        Returns:
            IRunner: A new instance of the requested runner.
            
        Raises:
            ValueError: If the runner name is not registered.
        """
        if name not in cls._runners:
            raise ValueError(f"Unknown runner type: {name}. Available types: {', '.join(cls._runners.keys())}")
        return cls._runners[name]()
    
    @classmethod
    def available_runners(cls) -> List[str]:
        """
        Get a list of available runner names.
        
        Returns:
            List[str]: List of registered runner names.
        """
        return list(cls._runners.keys())