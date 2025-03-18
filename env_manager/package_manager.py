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
    
    def __init__(self, runner: IRunner):
        """
        Initialize a PackageManager instance.
        
        Args:
            runner: The runner to use for package operations (optional).
        """
        self.runner = runner
        self.logger = logging.getLogger(__name__)
                
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
            
            # Handle pip_options if provided
            if 'pip_options' in options:
                pip_options = options.pop('pip_options')
                if isinstance(pip_options, list):
                    cmd.extend(pip_options)
            
            # Process other options
            for key, value in options.items():
                if value is True:
                    cmd.append(f"--{key.replace('_', '-')}")
                elif value is not False and value is not None:
                    cmd.append(f"--{key.replace('_', '-')}={value}")
                    
            # Execute command with capture_output=True
            self.runner.run(*cmd, capture_output=True)
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
                    
            # Execute command with capture_output=True
            self.runner.run(*cmd, capture_output=True)
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
            
    def install_pkg(self, *packages, **options) -> 'InstallPkgContextManager':
        """
        Install packages temporarily using a context manager.
        
        Args:
            *packages: One or more packages to install.
            **options: Additional options for installation.
                pip_options: List of pip options to pass to the install command.
            
        Returns:
            InstallPkgContextManager: A context manager for temporary package installation.
            
        Raises:
            ValueError: If no runner is configured.
        """
        if not self.runner:
            raise ValueError("Package manager not configured with a runner")
            
        if not packages:
            raise ValueError("At least one package must be specified")
            
        return InstallPkgContextManager(self, packages, **options)


class InstallPkgContextManager:
    """Context manager for temporary package installation."""
    
    def __init__(self, pkg_manager, packages, **options):
        """
        Initialize the context manager.
        
        Args:
            pkg_manager: The package manager to use or a runner.
            packages: The package(s) to install - can be a single string or list.
            **options: Additional options for installation.
        """
        # Handle both PackageManager and direct runner for backward compatibility
        if isinstance(pkg_manager, PackageManager):
            self.pkg_manager = pkg_manager
            self.runner = pkg_manager.runner
        else:
            # Direct runner mode (for tests)
            self.runner = pkg_manager
            self.pkg_manager = None
        
        # Convert to a tuple if a single package is passed
        if isinstance(packages, (list, tuple)):
            self.packages = packages
        else:
            self.packages = (packages,)
            
        self.options = options
        
        # For backward compatibility with tests
        self._env_manager = pkg_manager
        self._installed = False
            
    @property
    def env_manager(self):
        """For backward compatibility with tests."""
        return self._env_manager
            
    def __enter__(self) -> 'InstallPkgContextManager':
        """Context manager entry - install the packages."""
        try:
            for package in self.packages:
                pip_options = self.options.get('pip_options', [])
                self.pkg_manager.install(package, pip_options=pip_options)
            self._installed = True
            return self
        except Exception as e:
            self.pkg_manager.logger.error(f"Failed to install packages {self.packages}")
            raise RuntimeError(f"Failed to install packages {self.packages}") from e
            
    def __exit__(self, exc_type: Optional[type], exc_val: Optional[Exception],
                 exc_tb: Optional[Any]) -> None:
        """Context manager exit - uninstall the packages."""
        if not self._installed:
            return
            
        try:
            for package in self.packages:
                self.pkg_manager.uninstall(package)
        except Exception as e:
            self.pkg_manager.logger.error(f"Failed to uninstall packages {self.packages}")
            raise RuntimeError(f"Failed to uninstall packages {self.packages}") from e