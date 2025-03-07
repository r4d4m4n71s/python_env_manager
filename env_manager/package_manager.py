"""
Package Manager Module

This module provides functionality for managing packages in Python environments.
"""

import logging
from typing import Optional, List, Any
from env_manager.runners.irunner import IRunner

class PackageManager:
    """
    Package manager for Python environments.
    
    This class provides functionality for managing packages in Python environments,
    including installation, uninstallation, and checking if packages are installed.
    """
    
    def __init__(self, runner: Optional[IRunner] = None):
        """
        Initialize a PackageManager instance.
        
        Args:
            runner: The runner to use for package operations (optional).
        """
        self.runner = runner
        self.logger = logging.getLogger(__name__)
        
    def with_runner(self, runner: IRunner) -> 'PackageManager':
        """
        Configure the package manager with a runner.
        
        Args:
            runner: The runner to use for package operations.
            
        Returns:
            PackageManager: The configured package manager instance (self).
        """
        self.runner = runner
        if hasattr(runner, 'env_manager') and runner.env_manager:
            self.logger = runner.env_manager.logger
        return self
        
    def install(self, package: str, **options) -> 'PackageManager':
        """
        Install a package.
        
        Args:
            package: The package to install.
            **options: Additional options to pass to pip install.
            
        Returns:
            PackageManager: The package manager instance (self) for method chaining.
            
        Raises:
            ValueError: If no runner is configured.
            RuntimeError: If package installation fails.
        """
        if not self.runner:
            raise ValueError("Package manager not configured with a runner")
            
        try:
            # Build command with options
            cmd = ["pip", "install", package]
            for key, value in options.items():
                if value is True:
                    cmd.append(f"--{key.replace('_', '-')}")
                elif value is not False and value is not None:
                    cmd.append(f"--{key.replace('_', '-')}={value}")
                    
            # Execute command
            self.runner.run(*cmd)
            self.logger.info(f"Successfully installed package: {package}")
            return self
            
        except Exception as e:
            self.logger.error(f"Failed to install package {package}: {e}")
            raise RuntimeError(f"Failed to install package {package}") from e
            
    def uninstall(self, package: str, **options) -> 'PackageManager':
        """
        Uninstall a package.
        
        Args:
            package: The package to uninstall.
            **options: Additional options to pass to pip uninstall.
            
        Returns:
            PackageManager: The package manager instance (self) for method chaining.
            
        Raises:
            ValueError: If no runner is configured.
            RuntimeError: If package uninstallation fails.
        """
        if not self.runner:
            raise ValueError("Package manager not configured with a runner")
            
        try:
            # Build command with options
            cmd = ["pip", "uninstall", "-y", package]
            for key, value in options.items():
                if value is True:
                    cmd.append(f"--{key.replace('_', '-')}")
                elif value is not False and value is not None:
                    cmd.append(f"--{key.replace('_', '-')}={value}")
                    
            # Execute command
            self.runner.run(*cmd)
            self.logger.info(f"Successfully uninstalled package: {package}")
            return self
            
        except Exception as e:
            self.logger.error(f"Failed to uninstall package {package}: {e}")
            raise RuntimeError(f"Failed to uninstall package {package}") from e
            
    def is_installed(self, package: str) -> bool:
        """
        Check if a package is installed.
        
        Args:
            package: The package to check.
            
        Returns:
            bool: True if the package is installed, False otherwise.
            
        Raises:
            ValueError: If no runner is configured.
        """
        if not self.runner:
            raise ValueError("Package manager not configured with a runner")
            
        try:
            # Execute command
            result = self.runner.run("pip", "show", package, check=False, capture_output=True)
            return result.returncode == 0
            
        except Exception:
            return False
            
    def list_packages(self) -> List[str]:
        """
        List installed packages.
        
        Returns:
            List[str]: List of installed packages.
            
        Raises:
            ValueError: If no runner is configured.
            RuntimeError: If listing packages fails.
        """
        if not self.runner:
            raise ValueError("Package manager not configured with a runner")
            
        try:
            # Execute command
            result = self.runner.run("pip", "list", "--format=freeze", capture_output=True)
            
            # Parse output
            packages = []
            for line in result.stdout.splitlines():
                if line.strip():
                    package = line.split('==')[0]
                    packages.append(package)
                    
            return packages
            
        except Exception as e:
            self.logger.error(f"Failed to list packages: {e}")
            raise RuntimeError("Failed to list packages") from e
            
    def install_pkg(self, package: str) -> 'InstallPkgContextManager':
        """
        Install a package temporarily using a context manager.
        
        Args:
            package: The package to install.
            
        Returns:
            InstallPkgContextManager: A context manager for temporary package installation.
            
        Raises:
            ValueError: If no runner is configured.
        """
        if not self.runner:
            raise ValueError("Package manager not configured with a runner")
            
        return InstallPkgContextManager(self, package)


class InstallPkgContextManager:
    """Context manager for temporary package installation."""
    
    def __init__(self, pkg_manager: PackageManager, package: str):
        """
        Initialize and install the package.
        
        Args:
            pkg_manager: The package manager to use.
            package: The package to install.
            
        Raises:
            RuntimeError: If package installation fails.
        """
        self.pkg_manager = pkg_manager
        self.package = package
        
        # For backward compatibility with tests
        self._env_manager = pkg_manager
        
        try:
            self.pkg_manager.install(self.package)
        except Exception as e:
            self.pkg_manager.logger.error(f"Failed to install package {self.package}")
            raise RuntimeError(f"Failed to install package {self.package}") from e
            
    @property
    def env_manager(self):
        """For backward compatibility with tests."""
        return self._env_manager
            
    def __enter__(self) -> 'InstallPkgContextManager':
        """Context manager entry."""
        return self
            
    def __exit__(self, exc_type: Optional[type], exc_val: Optional[Exception],
                 exc_tb: Optional[Any]) -> None:
        """Context manager exit - uninstall the package."""
        try:
            self.pkg_manager.uninstall(self.package)
        except Exception as e:
            self.pkg_manager.logger.error(f"Failed to uninstall package {self.package}")
            raise RuntimeError(f"Failed to uninstall package {self.package}") from e