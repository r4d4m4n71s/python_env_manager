"""
Test module for PackageManager class.
"""

import subprocess
from unittest.mock import MagicMock, patch, call

import pytest

from env_manager.package_manager import PackageManager, InstallPkgContextManager


class TestPackageManager:
    """Test cases for the PackageManager class."""

    @pytest.fixture
    def mock_runner(self):
        """Create a mock runner for testing."""
        runner = MagicMock()
        # Configure the runner's run method to return a MagicMock with stdout attribute
        runner.run.return_value = MagicMock(stdout="")
        return runner

    @pytest.fixture
    def package_manager(self, mock_runner):
        """Create a PackageManager instance with mock runner."""
        return PackageManager().with_runner(mock_runner)

    def test_initialization(self):
        """Test that PackageManager initializes correctly."""
        pm = PackageManager()
        assert pm.runner is None

    def test_with_runner(self, mock_runner):
        """Test with_runner method correctly configures the package manager."""
        pm = PackageManager()
        result = pm.with_runner(mock_runner)
        
        assert pm.runner == mock_runner
        assert result == pm  # Should return self for chaining

    def test_install_pkg_context_manager(self, package_manager, mock_runner):
        """Test the install_pkg context manager."""
        # Use the context manager
        with package_manager.install_pkg("test-package") as cm:
            # Verify it's the right type
            assert isinstance(cm, InstallPkgContextManager)
            
            # Verify runner.run was called to install package
            mock_runner.run.assert_called_with(
                "pip", "install", "test-package", capture_output=True
            )

        # Verify runner.run was called to uninstall package after context exit
        calls = mock_runner.run.call_args_list
        assert len(calls) == 2
        assert calls[1] == call("pip", "uninstall", "-y", "test-package", capture_output=True)

    def test_install_multiple_packages(self, package_manager, mock_runner):
        """Test installing multiple packages."""
        # Use the context manager with multiple packages
        packages = ["pkg1", "pkg2", "pkg3"]
        with package_manager.install_pkg(*packages) as cm:
            # Verify runner.run was called for each package
            assert mock_runner.run.call_count == 3
            
            # Verify all packages were installed
            for package in packages:
                mock_runner.run.assert_any_call("pip", "install", package, capture_output=True)
            
            # Reset the mock to track only uninstall calls
            mock_runner.reset_mock()

        # Verify uninstall was called for each package (3 calls for installs + 3 calls for uninstalls)
        assert mock_runner.run.call_count == 3
            
        # Verify all packages were uninstalled
        for package in packages:
            mock_runner.run.assert_any_call("pip", "uninstall", "-y", package, capture_output=True)

    def test_install_with_options(self, package_manager, mock_runner):
        """Test installing with pip options."""
        # Use the context manager with pip options
        with package_manager.install_pkg(
            "test-package", pip_options=["--no-cache-dir", "--upgrade"]
        ) as cm:
            # Verify runner.run was called with the pip options
            mock_runner.run.assert_called_once()
            install_args = mock_runner.run.call_args[0]
            assert "--no-cache-dir" in install_args
            assert "--upgrade" in install_args

    def test_no_runner_error(self):
        """Test error when no runner is configured."""
        pm = PackageManager()
        with pytest.raises(ValueError, match="Package manager not configured with a runner"):
            with pm.install_pkg("test-package"):
                pass

    def test_install_pkg_command_error(self, package_manager, mock_runner):
        """Test handling of command errors during installation."""
        # Configure runner to raise an exception for install
        mock_runner.run.side_effect = [
            subprocess.CalledProcessError(1, ["pip", "install"],
                                          stderr="Installation error"),
            None  # For uninstall (shouldn't be called)
        ]
        
        # Use the context manager
        with pytest.raises(RuntimeError, match="Failed to install"):
            with package_manager.install_pkg("test-package"):
                pytest.fail("Context manager should not execute body if installation fails")
        
        # Verify uninstall wasn't called (only install was attempted)
        assert mock_runner.run.call_count == 1

    def test_uninstall_error_handling(self, package_manager, mock_runner):
        """Test handling of command errors during uninstallation."""
        # Configure runner to succeed for install but fail for uninstall
        mock_runner.run.side_effect = [
            MagicMock(stdout=""),  # Install succeeds
            subprocess.CalledProcessError(1, ["pip", "uninstall"],
                                         stderr="Uninstallation error")
        ]
        
        # Use the context manager - should raise RuntimeError during context exit
        with pytest.raises(RuntimeError, match="Failed to uninstall"):
            with package_manager.install_pkg("test-package") as cm:
                pass
        
        # Both install and uninstall should have been called
        assert mock_runner.run.call_count == 2


class TestInstallPkgContextManager:
    """Test cases for the InstallPkgContextManager class."""

    @pytest.fixture
    def mock_runner(self):
        """Create a mock runner for testing."""
        runner = MagicMock()
        runner.run.return_value = MagicMock(stdout="")
        return runner

    @pytest.fixture
    def package_manager(self, mock_runner):
        """Create a PackageManager instance with mock runner."""
        return PackageManager().with_runner(mock_runner)

    def test_context_manager_enter_exit(self, package_manager, mock_runner):
        """Test the __enter__ and __exit__ methods."""
        # Create context manager with package manager
        package = "test-package"
        cm = InstallPkgContextManager(package_manager, package)
        
        # Reset mock before testing
        mock_runner.reset_mock()
        
        # Enter the context
        result = cm.__enter__()
        
        # Verify __enter__ returned self
        assert result == cm
        
        # Verify installation was performed
        mock_runner.run.assert_called_once()
        
        # Reset mock before testing exit
        mock_runner.reset_mock()
        
        # Exit the context
        cm.__exit__(None, None, None)
        
        # Verify uninstallation was performed
        assert mock_runner.run.call_count == 1

    def test_exception_during_context(self, package_manager, mock_runner):
        """Test exception handling during context execution."""
        # Create context manager with package manager
        package = "test-package"
        cm = InstallPkgContextManager(package_manager, package)
        
        # Reset mock before testing
        mock_runner.reset_mock()
        
        # Enter context
        cm.__enter__()
        
        # Reset mock before testing exit
        mock_runner.reset_mock()
        
        # Simulate exception in context
        exception = ValueError("Test exception")
        cm.__exit__(ValueError, exception, None)
        
        # Verify uninstallation was still performed
        assert mock_runner.run.call_count == 1
        
        # And exception wasn't suppressed
        assert cm.__exit__(ValueError, exception, None) is None