"""
Unit tests for the env_manager module with simplified structure.

These tests use mocking to ensure we're testing the module's logic
without creating actual virtual environments.
"""

import os
import sys
import shutil
import subprocess
from unittest import mock
import pytest

from env_manager import (
    Environment, EnvManager, InstallPkgContextManager,
    PackageManager
)


class TestEnvManager:
    """Tests for Environment and EnvManager classes."""

    @pytest.fixture
    def mock_env_builder(self):
        """Fixture to mock venv.EnvBuilder."""
        with mock.patch("venv.EnvBuilder") as mock_builder:
            mock_builder.return_value.create.return_value = None
            yield mock_builder

    @pytest.fixture
    def mock_environment(self):
        """Fixture to create a mock Environment object."""
        mock_env = mock.MagicMock()
        mock_env.root = "/test/venv/path"
        mock_env.bin = "/test/venv/path/bin"
        mock_env.lib = "/test/venv/path/lib"
        mock_env.python = "/test/venv/path/bin/python"
        mock_env.name = "path"
        mock_env.is_virtual = True
        
        with mock.patch('env_manager.env_manager.Environment', return_value=mock_env):
            yield mock_env

    @pytest.fixture
    def mock_subprocess(self):
        """Fixture to mock subprocess functions."""
        with mock.patch("env_manager.runners.runner.subprocess") as mock_subproc:
            mock_subproc.run.return_value = mock.MagicMock(returncode=0, stdout="success")
            mock_subproc.CalledProcessError = subprocess.CalledProcessError
            mock_subproc.Popen.return_value.communicate.return_value = ("VAR=value", "")
            mock_subproc.Popen.return_value.returncode = 0
            yield mock_subproc

    @pytest.fixture
    def mock_filesystem(self):
        """Fixture to mock filesystem operations."""
        with mock.patch("os.path.exists", return_value=True), \
             mock.patch("os.path.join", side_effect=os.path.join), \
             mock.patch("os.makedirs"), \
             mock.patch("shutil.rmtree") as mock_rmtree:
            yield mock_rmtree

    @pytest.fixture
    def mock_create_venv(self):
        """Fixture to prevent _create_venv from being called."""
        with mock.patch.object(EnvManager, '_create_venv', return_value=None):
            yield

    @pytest.fixture
    def mock_pkg_manager(self):
        """Fixture to create a mock PackageManager."""
        mock_manager = mock.MagicMock()
        mock_manager.install.return_value = mock_manager
        mock_manager.uninstall.return_value = mock_manager
        mock_manager.logger = mock.MagicMock()
        return mock_manager
            
    # Environment class tests
    
    def test_environment_init_with_path(self):
        """Test initializing Environment with explicit path."""
        test_path = "/test/venv/path"
        with mock.patch("os.path.abspath", return_value=test_path):
            env = Environment(path=test_path)
            assert env.root == test_path
            assert env.name == "path"

    def test_environment_init_with_virtual_env(self):
        """Test initializing Environment with VIRTUAL_ENV variable."""
        test_path = "/test/venv/path"
        with mock.patch.dict(os.environ, {"VIRTUAL_ENV": test_path}), \
             mock.patch("os.path.abspath", return_value=test_path), \
             mock.patch.object(Environment, "is_local", return_value=False):
            env = Environment()
            assert env.root == test_path
            assert env.is_virtual is True

    def test_environment_init_with_sys_prefix(self):
        """Test initializing Environment with sys.prefix."""
        test_path = "/test/sys/prefix"
        with mock.patch.dict(os.environ, {}, clear=True), \
             mock.patch("sys.prefix", test_path), \
             mock.patch("os.path.abspath", return_value=test_path), \
             mock.patch.object(Environment, "is_local", return_value=True):
            env = Environment()
            assert env.root == test_path
            assert env.is_virtual is False

    def test_environment_init_with_kwargs(self):
        """Test initializing Environment with kwargs."""
        env = Environment(
            root="/test/path",
            name="test-env",
            bin="/test/path/bin",
            lib="/test/path/lib",
            python="/test/path/bin/python",
            is_virtual=True
        )
        assert env.root == "/test/path"
        assert env.name == "test-env"
        assert env.bin == "/test/path/bin"
        assert env.lib == "/test/path/lib"
        assert env.python == "/test/path/bin/python"
        assert env.is_virtual is True

    def test_environment_is_local(self):
        """Test is_local method on different platforms."""
        # Windows tests
        with mock.patch("os.name", "nt"):
            assert Environment.is_local(r"C:\Python39") is True
            assert Environment.is_local(r"C:\Users\user\AppData\Local\Programs\Python\Python39") is True
            assert Environment.is_local(r"C:\Anaconda3") is True
            assert Environment.is_local(r"C:\venvs\my-env") is False

        # Unix tests
        with mock.patch("os.name", "posix"):
            assert Environment.is_local("/usr/bin") is True
            assert Environment.is_local("/usr/local/bin") is True
            assert Environment.is_local("/opt/homebrew/bin") is True
            assert Environment.is_local("/home/user/venvs/my-env") is False

    def test_environment_from_dict(self):
        """Test creating Environment from dictionary."""
        env_dict = {
            "root": "/test/path",
            "name": "test-env",
            "bin": "/test/path/bin",
            "lib": "/test/path/lib",
            "python": "/test/path/bin/python",
            "is_virtual": True
        }
        env = Environment.from_dict(env_dict)
        assert env.root == "/test/path"
        assert env.name == "test-env"
        assert env.bin == "/test/path/bin"
        assert env.lib == "/test/path/lib"
        assert env.python == "/test/path/bin/python"
        assert env.is_virtual is True

    # EnvManager initialization tests
    
    def test_manager_init_with_virtual_env(self, mock_environment, mock_filesystem, mock_env_builder):
        """Test EnvManager initialization with virtual env."""
        with mock.patch.object(EnvManager, '_create_venv', autospec=True) as patched_create_venv:
            manager = EnvManager("/test/venv/path")
            assert manager.env is mock_environment
            patched_create_venv.assert_called_once()

    def test_manager_init_with_local_env(self, mock_environment, mock_filesystem, mock_env_builder):
        """Test EnvManager initialization with local env."""
        mock_environment.is_virtual = False
        with mock.patch('env_manager.env_manager.EnvBuilder', return_value=mock_env_builder.return_value) as patched_builder:
            manager = EnvManager("/test/local/path")
            assert manager.env is mock_environment
            patched_builder.return_value.create.assert_not_called()

    # EnvManager venv creation tests
    
    def test_manager_create_venv(self, mock_environment, mock_filesystem, mock_env_builder):
        """Test creating a virtual environment."""
        custom_builder = mock.MagicMock()
        
        with mock.patch('env_manager.env_manager.Environment', return_value=mock_environment):
            # Skip venv creation during initialization
            with mock.patch.object(EnvManager, '_create_venv', return_value=None):
                manager = EnvManager("/test/venv/path", env_builder=custom_builder)
            
            # Test actual create_venv method
            manager._create_venv(clear=True)
            custom_builder.create.assert_called_once_with(mock_environment.root)

    def test_manager_create_venv_error(self, mock_environment, mock_filesystem, mock_env_builder):
        """Test error handling in venv creation."""
        error_builder = mock.MagicMock()
        error_builder.create.side_effect = Exception("Creation failed")
        
        with mock.patch('env_manager.env_manager.Environment', return_value=mock_environment):
            with mock.patch.object(EnvManager, '_create_venv', return_value=None):
                manager = EnvManager("/test/venv/path", env_builder=error_builder)
            
            with pytest.raises(RuntimeError, match="Failed to create virtual environment"):
                manager._create_venv()

    # EnvManager removal tests
    
    def test_manager_remove(self, mock_environment, mock_filesystem, mock_create_venv):
        """Test removing a virtual environment."""
        with mock.patch('env_manager.env_manager.Environment', return_value=mock_environment):
            manager = EnvManager("/test/venv/path")
            
            with mock.patch.object(manager, "is_active", return_value=False):
                manager.remove()
                mock_filesystem.assert_called_once_with(mock_environment.root)

    def test_manager_remove_active_env(self, mock_environment, mock_filesystem, mock_create_venv):
        """Test removing an active virtual environment."""
        with mock.patch('env_manager.env_manager.Environment', return_value=mock_environment):
            manager = EnvManager("/test/venv/path")
            mock_deactivate = mock.MagicMock()
            
            with mock.patch.object(manager, "is_active", return_value=True), \
                 mock.patch.object(manager, "deactivate", mock_deactivate):
                manager.remove()
                mock_deactivate.assert_called_once()
                mock_filesystem.assert_called_once_with(mock_environment.root)

    def test_manager_remove_error(self, mock_environment, mock_filesystem, mock_create_venv):
        """Test error handling when removing a virtual environment."""
        mock_filesystem.side_effect = Exception("Removal failed")
        
        with mock.patch('env_manager.env_manager.Environment', return_value=mock_environment):
            manager = EnvManager("/test/venv/path")
            
            with mock.patch.object(manager, "is_active", return_value=False), \
                 pytest.raises(RuntimeError, match="Failed to remove virtual environment"):
                manager.remove()

    # EnvManager run tests
    
    def test_manager_run_with_activation(self, mock_environment, mock_subprocess, mock_filesystem, mock_create_venv):
        """Test running a command with activation script."""
        with mock.patch('env_manager.env_manager.Environment', return_value=mock_environment):
            manager = EnvManager("/test/venv/path")
            
            # Test on Windows
            with mock.patch("os.name", "nt"), \
                 mock.patch('subprocess.run', side_effect=mock_subprocess.run):
                manager.run("pip", "install", "package")
                cmd = mock_subprocess.run.call_args[0][0]
                assert "activate.bat" in cmd and "pip install package" in cmd

            # Test on Unix
            mock_subprocess.run.reset_mock()
            with mock.patch("os.name", "posix"), \
                 mock.patch('subprocess.run', side_effect=mock_subprocess.run):
                manager.run("pip", "install", "package")
                cmd = mock_subprocess.run.call_args[0][0]
                assert "source" in cmd and "activate" in cmd and "pip install package" in cmd

    def test_manager_run_without_activation(self, mock_environment, mock_subprocess, mock_create_venv):
        """Test running a command without activation script."""
        with mock.patch('env_manager.env_manager.Environment', return_value=mock_environment):
            manager = EnvManager("/test/venv/path")
            
            with mock.patch("os.path.exists", return_value=False), \
                 mock.patch("sys.executable", mock_environment.python), \
                 mock.patch('subprocess.run', side_effect=mock_subprocess.run):
                
                manager.run("python", "-c", "print('hello')")
                
                args, kwargs = mock_subprocess.run.call_args
                command = args[0]
                
                # Check that python executable is used
                if isinstance(command, list):
                    assert command[0] == mock_environment.python
                else:
                    assert mock_environment.python in command
                
                # Verify options are passed correctly
                assert all([kwargs.get('text'), kwargs.get('check'), kwargs.get('capture_output')])

    def test_manager_run_error(self, mock_environment, mock_subprocess, mock_filesystem, mock_create_venv):
        """Test error handling when running a command fails."""
        mock_subprocess.run.side_effect = subprocess.CalledProcessError(
            1, "pip install package", stderr="Installation failed"
        )
        
        with mock.patch('env_manager.env_manager.Environment', return_value=mock_environment), \
             mock.patch('subprocess.run', side_effect=mock_subprocess.run):
            manager = EnvManager("/test/venv/path")
            
            with pytest.raises(subprocess.CalledProcessError):
                manager.run("pip", "install", "package")

    # EnvManager activate/deactivate tests
    
    def test_manager_activate(self, mock_environment, mock_create_venv):
        """Test activating a virtual environment."""
        with mock.patch('env_manager.env_manager.Environment', return_value=mock_environment):
            manager = EnvManager("/test/venv/path")
            
            # Create clean test environment
            clean_env = {}
            clean_path = []
            
            with mock.patch("os.path.exists", return_value=True), \
                 mock.patch.object(manager, "is_active", return_value=False), \
                 mock.patch.dict(os.environ, clean_env, clear=True), \
                 mock.patch("sys.path", clean_path[:]):
                
                manager.activate()
                
                # Check environment variables were set correctly
                assert os.environ["VIRTUAL_ENV"] == mock_environment.root
                assert mock_environment.bin in os.environ["PATH"]
                assert os.path.join(mock_environment.lib, "site-packages") in sys.path

    def test_manager_activate_already_active(self, mock_environment, mock_create_venv):
        """Test activating an already active environment."""
        with mock.patch('env_manager.env_manager.Environment', return_value=mock_environment):
            manager = EnvManager("/test/venv/path")
            
            test_env = {}
            test_path = []
            
            with mock.patch.object(manager, "is_active", return_value=True), \
                 mock.patch.dict(os.environ, test_env, clear=True), \
                 mock.patch("sys.path", test_path[:]):
                
                manager.activate()
                
                # Environment should remain unchanged
                assert "VIRTUAL_ENV" not in os.environ
                assert not sys.path

    def test_manager_deactivate(self, mock_environment, mock_create_venv):
        """Test deactivating a virtual environment."""
        with mock.patch('env_manager.env_manager.Environment', return_value=mock_environment):
            manager = EnvManager("/test/venv/path")
            
            # Set up original environment state
            original_env = {"PATH": "/original/path"}
            original_path = ["/original/site-packages"]
            manager._original_env = original_env.copy()
            manager._original_path = original_path.copy()
            
            # Set up current environment
            test_env = {"VIRTUAL_ENV": mock_environment.root, "PATH": f"{mock_environment.bin}:/other/path"}
            test_path = [os.path.join(mock_environment.lib, "site-packages"), mock_environment.lib]
            
            with mock.patch.object(manager, "is_active", return_value=True), \
                 mock.patch.dict(os.environ, test_env, clear=True), \
                 mock.patch("sys.path", test_path[:]):
                
                manager.deactivate()
                
                # Environment should be restored
                assert os.environ == original_env
                assert sys.path == original_path

    # EnvManager context manager and utility tests
    
    def test_manager_context_manager(self, mock_environment, mock_create_venv):
        """Test EnvManager as a context manager."""
        with mock.patch('env_manager.env_manager.Environment', return_value=mock_environment):
            manager = EnvManager("/test/venv/path")
            
            with mock.patch.object(manager, "activate") as mock_activate, \
                 mock.patch.object(manager, "deactivate") as mock_deactivate:
                mock_activate.return_value = manager
                
                with manager as env:
                    assert env is manager
                    mock_activate.assert_called_once()
                
                mock_deactivate.assert_called_once()

    def test_manager_is_active(self, mock_environment, mock_create_venv):
        """Test checking if a virtual environment is active."""
        with mock.patch('env_manager.env_manager.Environment', return_value=mock_environment):
            manager = EnvManager("/test/venv/path")
            
            # Test active environment
            with mock.patch.dict(os.environ, {"VIRTUAL_ENV": mock_environment.root}, clear=True):
                assert manager.is_active() is True
            
            # Test different active environment
            with mock.patch.dict(os.environ, {"VIRTUAL_ENV": "/other/path"}, clear=True):
                assert manager.is_active() is False
            
            # Test no active environment
            with mock.patch.dict(os.environ, {}, clear=True):
                assert manager.is_active() is False

    def test_manager_install_pkg(self, mock_environment, mock_subprocess, mock_create_venv):
        """Test installing a package."""
        with mock.patch('env_manager.env_manager.Environment', return_value=mock_environment):
            manager = EnvManager("/test/venv/path")
            
            # Mock dependencies
            mock_runner = mock.MagicMock()
            mock_pkg_manager = mock.MagicMock()
            mock_ctx_manager = mock.MagicMock()
            
            with mock.patch("env_manager.env_manager.RunnerFactory.create", return_value=mock_runner), \
                 mock.patch("env_manager.env_manager.PackageManager", return_value=mock_pkg_manager), \
                 mock.patch("env_manager.package_manager.InstallPkgContextManager", return_value=mock_ctx_manager):
                
                mock_runner.with_env.return_value = mock_runner
                mock_pkg_manager.install_pkg.return_value = mock_ctx_manager
                
                result = manager.install_pkg("package")
                
                # Verify correct methods were called
                mock_runner.with_env.assert_called_once_with(manager)
                mock_pkg_manager.install_pkg.assert_called_once_with("package")
                assert result is mock_ctx_manager

    # InstallPkgContextManager tests
    
    def test_install_pkg_context_manager_init(self, mock_pkg_manager):
        """Test initializing InstallPkgContextManager."""
        ctx = InstallPkgContextManager(mock_pkg_manager, "package")
        assert ctx.pkg_manager is mock_pkg_manager
        assert ctx.package == "package"
        mock_pkg_manager.install.assert_called_once_with("package")

    def test_install_pkg_context_manager_usage(self, mock_pkg_manager):
        """Test using InstallPkgContextManager as a context manager."""
        ctx = InstallPkgContextManager(mock_pkg_manager, "package")
        
        # Reset mocks to clear initialization calls
        mock_pkg_manager.install.reset_mock()
        mock_pkg_manager.uninstall.reset_mock()
        
        with ctx as result:
            assert result is ctx
            mock_pkg_manager.install.assert_not_called()  # Already installed in __init__
        
        # Uninstall should be called on exit
        mock_pkg_manager.uninstall.assert_called_once_with("package")
