"""
Unit tests for the env_manager module.

These tests focus on mocking external dependencies like the venv module and EnvBuilder
to ensure we're testing the module's logic without creating actual virtual environments.
"""

import os
import sys
import shutil
import subprocess
import logging
from unittest import mock
from pathlib import Path
import pytest
from venv import EnvBuilder

from env_manager import Environment, EnvManager, InstallPkgContextManager


class TestEnvironment:
    """Tests for the Environment class."""

    def test_init_with_path(self):
        """Test initializing Environment with an explicit path."""
        test_path = "/test/venv/path"
        with mock.patch("os.path.abspath", return_value=test_path):
            env = Environment(path=test_path)
            assert env.root == test_path
            assert env.name == "path"  # basename of test_path

    def test_init_with_virtual_env(self):
        """Test initializing Environment with VIRTUAL_ENV environment variable."""
        test_path = "/test/venv/path"
        with mock.patch.dict(os.environ, {"VIRTUAL_ENV": test_path}), \
             mock.patch("os.path.abspath", return_value=test_path), \
             mock.patch.object(Environment, "is_local", return_value=False):
            env = Environment()
            assert env.root == test_path
            assert env.is_virtual is True

    def test_init_with_sys_prefix(self):
        """Test initializing Environment with sys.prefix."""
        test_path = "/test/sys/prefix"
        with mock.patch.dict(os.environ, {}, clear=True), \
             mock.patch("sys.prefix", test_path), \
             mock.patch("os.path.abspath", return_value=test_path), \
             mock.patch.object(Environment, "is_local", return_value=True):
            env = Environment()
            assert env.root == test_path
            assert env.is_virtual is False

    def test_init_with_kwargs(self):
        """Test initializing Environment with direct kwargs."""
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

    def test_is_local_windows(self):
        """Test is_local method on Windows."""
        with mock.patch("os.name", "nt"):
            # Should match Windows patterns
            assert Environment.is_local(r"C:\Python39") is True
            assert Environment.is_local(r"C:\Users\user\AppData\Local\Programs\Python\Python39") is True
            assert Environment.is_local(r"C:\Anaconda3") is True
            # Should not match Windows patterns
            assert Environment.is_local(r"C:\venvs\my-env") is False

    def test_is_local_unix(self):
        """Test is_local method on Unix-like systems."""
        with mock.patch("os.name", "posix"):
            # Should match Unix patterns
            assert Environment.is_local("/usr/bin") is True
            assert Environment.is_local("/usr/local/bin") is True
            assert Environment.is_local("/opt/homebrew/bin") is True
            # Should not match Unix patterns
            assert Environment.is_local("/home/user/venvs/my-env") is False

    def test_from_dict(self):
        """Test creating Environment from a dictionary."""
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


class TestEnvManager:
    """Tests for the EnvManager class."""

    @pytest.fixture
    def mock_env_builder(self):
        """Fixture to mock EnvBuilder."""
        with mock.patch("env_manager.env_manager.EnvBuilder") as mock_builder:
            mock_instance = mock_builder.return_value
            mock_instance.create.return_value = None
            yield mock_builder

    @pytest.fixture
    def mock_environment(self):
        """Fixture to mock Environment class."""
        with mock.patch("env_manager.env_manager.Environment") as mock_env_class:
            mock_env = mock.MagicMock()
            mock_env.root = "/test/venv/path"
            mock_env.bin = "/test/venv/path/bin"
            mock_env.lib = "/test/venv/path/lib"
            mock_env.python = "/test/venv/path/bin/python"
            mock_env.name = "path"
            mock_env.is_virtual = True
            mock_env_class.return_value = mock_env
            yield mock_env

    @pytest.fixture
    def mock_subprocess(self):
        """Fixture to mock subprocess module."""
        with mock.patch("env_manager.env_manager.subprocess") as mock_subproc:
            mock_result = mock.MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "success"
            mock_subproc.run.return_value = mock_result
            mock_subproc.CalledProcessError = subprocess.CalledProcessError
            mock_subproc.Popen.return_value.communicate.return_value = ("VAR=value", "")
            mock_subproc.Popen.return_value.returncode = 0
            yield mock_subproc

    @pytest.fixture
    def mock_os_path(self):
        """Fixture to mock os.path functions."""
        with mock.patch("os.path.exists", return_value=True), \
             mock.patch("os.path.join", side_effect=os.path.join), \
             mock.patch("os.makedirs"):
            yield

    @pytest.fixture
    def mock_shutil(self):
        """Fixture to mock shutil module."""
        with mock.patch("shutil.rmtree") as mock_rmtree:
            yield mock_rmtree

    def test_init_with_virtual_env(self, mock_environment, mock_os_path, mock_env_builder):
        """Test that EnvBuilder is called when initializing with a virtual environment."""
        # Initialize the manager (mock_environment.is_virtual is True by default)
        manager = EnvManager("/test/venv/path")
        
        # Verify environment is set and EnvBuilder was called
        assert manager.env is mock_environment
        mock_env_builder.assert_called_once()

    def test_init_with_local_env(self, mock_env_builder, mock_environment, mock_os_path):
        """Test that EnvBuilder is not called when initializing with a local environment."""
        # Set environment to non-virtual
        mock_environment.is_virtual = False
        
        # Initialize the manager
        manager = EnvManager("/test/local/path")
        
        # Verify environment is set and EnvBuilder was not called
        assert manager.env is mock_environment
        mock_env_builder.assert_not_called()

    def test_create_venv(self, mock_environment, mock_os_path, mock_env_builder):
        """Test creating a virtual environment with specific parameters."""
        custom_builder = mock.MagicMock(spec=EnvBuilder)
        manager = EnvManager("/test/venv/path", env_builder=custom_builder)
        
        custom_builder.create.reset_mock()
        manager._create_venv(clear=True)
        
        # Verify custom builder was used and default builder was not
        custom_builder.create.assert_called_once_with(mock_environment.root)
        mock_env_builder.assert_not_called()

    def test_create_venv_with_custom_builder(self, mock_environment, mock_os_path, mock_env_builder):
        """Test creating a virtual environment with a custom EnvBuilder."""
        custom_builder = mock.MagicMock(spec=EnvBuilder)
        manager = EnvManager("/test/venv/path", env_builder=custom_builder)
        
        mock_env_builder.reset_mock()
        custom_builder.create.reset_mock()
        manager._create_venv()
        
        # Verify custom builder was used and default builder was not
        custom_builder.create.assert_called_once_with(mock_environment.root)
        mock_env_builder.assert_not_called()

    def test_create_venv_error(self, mock_env_builder, mock_environment, mock_os_path):
        """Test error handling when creating a virtual environment fails."""
        # Set up the mock to raise an exception
        mock_env_builder.return_value.create.side_effect = Exception("Creation failed")
        
        # Verify that RuntimeError is raised with the correct message
        with pytest.raises(RuntimeError, match="Failed to create virtual environment"):
            EnvManager("/test/venv/path")

    def test_remove(self, mock_environment, mock_shutil, mock_env_builder):
        """Test that remove method doesn't use EnvBuilder."""
        # Create manager and reset mock to focus only on the remove operation
        manager = EnvManager("/test/venv/path")
        mock_env_builder.reset_mock()
        
        # Execute remove method (with is_active mocked to False)
        with mock.patch.object(manager, "is_active", return_value=False):
            manager.remove()
        
        # Verify shutil.rmtree was called and EnvBuilder was not
        mock_shutil.assert_called_once_with(mock_environment.root)
        mock_env_builder.assert_not_called()

    def test_remove_active_env(self, mock_environment, mock_shutil, mock_env_builder):
        """Test removing an active virtual environment."""
        # Create manager and reset mock
        manager = EnvManager("/test/venv/path")
        mock_env_builder.reset_mock()
        
        # Create a mock for the deactivate method
        mock_deactivate = mock.MagicMock()
        
        # Mock is_active to return True and replace deactivate with our mock
        with mock.patch.object(manager, "is_active", return_value=True), \
             mock.patch.object(manager, "deactivate", mock_deactivate):
            manager.remove()
        
        # Verify deactivate was called, shutil.rmtree was called, and EnvBuilder was not used
        mock_deactivate.assert_called_once()
        mock_shutil.assert_called_once_with(mock_environment.root)
        mock_env_builder.assert_not_called()

    def test_remove_error(self, mock_environment, mock_shutil, mock_env_builder):
        """Test error handling when removing a virtual environment fails."""
        # Set up mock to raise an exception
        mock_shutil.side_effect = Exception("Removal failed")
        
        # Create manager and reset mock
        manager = EnvManager("/test/venv/path")
        mock_env_builder.reset_mock()
        
        # Verify that RuntimeError is raised with the correct message
        with mock.patch.object(manager, "is_active", return_value=False), \
             pytest.raises(RuntimeError, match="Failed to remove virtual environment"):
            manager.remove()
        
        # Verify EnvBuilder was not used
        mock_env_builder.assert_not_called()

    def test_run_with_activation_script(self, mock_environment, mock_subprocess, mock_os_path, mock_env_builder):
        """Test running a command with an activation script."""
        manager = EnvManager("/test/venv/path")
        mock_env_builder.reset_mock()
        
        # Test on Windows
        with mock.patch("os.name", "nt"):
            manager.run("pip", "install", "package")
            
            # Verify subprocess was called correctly
            mock_env_builder.assert_not_called()
            mock_subprocess.run.assert_called_with(
                mock.ANY, env=os.environ, text=True, check=True,
                capture_output=True, shell=True
            )
            cmd = mock_subprocess.run.call_args[0][0]
            assert "activate.bat" in cmd and "pip install package" in cmd

        # Test on Unix
        mock_subprocess.run.reset_mock()
        with mock.patch("os.name", "posix"):
            manager.run("pip", "install", "package")
            
            # Verify subprocess was called correctly
            mock_env_builder.assert_not_called()
            mock_subprocess.run.assert_called_with(
                mock.ANY, env=os.environ, text=True, check=True,
                capture_output=True, shell=True, executable='/bin/bash'
            )
            cmd = mock_subprocess.run.call_args[0][0]
            assert "source" in cmd and "activate" in cmd and "pip install package" in cmd

    def test_run_without_activation_script(self, mock_environment, mock_subprocess, mock_env_builder):
        """Test running a command without an activation script."""
        manager = EnvManager("/test/venv/path")
        mock_env_builder.reset_mock()
        
        with mock.patch("os.path.exists", return_value=False), \
             mock.patch("sys.executable", mock_environment.python):
            
            # Test python command
            manager.run("python", "-c", "print('hello')")
            
            # Verify command execution
            mock_env_builder.assert_not_called()
            
            # Verify command contains expected parts
            args, kwargs = mock_subprocess.run.call_args
            command = args[0]
            
            if isinstance(command, list):
                assert command[0] == mock_environment.python
                assert "-c" in command and "print('hello')" in command
            else:
                assert mock_environment.python in command
                assert "-c" in command and "print('hello')" in command
            
            # Verify kwargs
            assert all([kwargs.get('text'), kwargs.get('check'), kwargs.get('capture_output')])
            
            # Test pip command
            mock_subprocess.run.reset_mock()
            manager.run("pip", "install", "package")
            mock_env_builder.assert_not_called()
            assert mock_subprocess.run.call_count > 0

    def test_run_error(self, mock_environment, mock_subprocess, mock_os_path, mock_env_builder):
        """Test error handling when running a command fails."""
        mock_subprocess.run.side_effect = subprocess.CalledProcessError(
            1, "pip install package", stderr="Installation failed"
        )
        manager = EnvManager("/test/venv/path")
        
        # Reset mock to focus on run method
        mock_env_builder.reset_mock()
        
        with pytest.raises(subprocess.CalledProcessError):
            manager.run("pip", "install", "package")
            
        # Verify EnvBuilder was not called during run
        mock_env_builder.assert_not_called()

    def test_activate(self, mock_environment, mock_env_builder):
        """Test activating a virtual environment."""
        manager = EnvManager("/test/venv/path")
        
        with mock.patch("os.path.exists", return_value=True), \
             mock.patch.object(manager, "is_active", return_value=False), \
             mock.patch.dict(os.environ, {}, clear=True), \
             mock.patch("sys.path", []):
            
            manager.activate()
            
            # Verify environment variables and sys.path were updated correctly
            assert os.environ["VIRTUAL_ENV"] == mock_environment.root
            assert mock_environment.bin in os.environ["PATH"]
            assert os.path.join(mock_environment.lib, "site-packages") in sys.path
            assert mock_environment.lib in sys.path

    def test_activate_already_active(self, mock_environment, mock_env_builder):
        """Test activating an already active virtual environment."""
        manager = EnvManager("/test/venv/path")
        mock_env_builder.reset_mock()
        
        with mock.patch.object(manager, "is_active", return_value=True), \
             mock.patch.dict(os.environ, {}), \
             mock.patch("sys.path", []):
            manager.activate()
            
            # Verify environment was not modified
            assert "VIRTUAL_ENV" not in os.environ
            assert not sys.path

    def test_activate_error(self, mock_environment, mock_env_builder):
        """Test error handling when activating a virtual environment fails."""
        manager = EnvManager("/test/venv/path")
        
        with mock.patch("os.path.exists", return_value=True), \
             mock.patch.object(manager, "is_active", return_value=False), \
             mock.patch.dict(os.environ, {}, clear=True), \
             mock.patch("sys.path", []):
            
            # Mock os.environ to raise an exception when updating PATH
            def mock_environ_get(key, default=None):
                if key == "PATH":
                    raise Exception("Activation failed")
                return default
            
            with mock.patch.object(os.environ, "get", side_effect=mock_environ_get), \
                 pytest.raises(RuntimeError, match="Failed to activate environment"):
                manager.activate()
            
            # Verify environment was restored
            assert "VIRTUAL_ENV" not in os.environ
            assert not sys.path

    def test_deactivate(self, mock_environment, mock_env_builder):
        """Test deactivating a virtual environment."""
        manager = EnvManager("/test/venv/path")
        mock_env_builder.reset_mock()
        
        # Set up original environment state
        original_env = {"PATH": "/original/path"}
        original_path = ["/original/site-packages"]
        manager._original_env = original_env
        manager._original_path = original_path
        
        with mock.patch.object(manager, "is_active", return_value=True), \
             mock.patch.dict(os.environ, {"VIRTUAL_ENV": mock_environment.root,
                                         "PATH": f"{mock_environment.bin}:/other/path"}), \
             mock.patch("sys.path", [os.path.join(mock_environment.lib, "site-packages"),
                                    mock_environment.lib]):
            manager.deactivate()
            
            # Verify environment was restored
            assert os.environ == original_env
            assert sys.path == original_path

    def test_deactivate_not_active(self, mock_environment, mock_env_builder):
        """Test deactivating a non-active virtual environment."""
        manager = EnvManager("/test/venv/path")
        mock_env_builder.reset_mock()
        
        with mock.patch.object(manager, "is_active", return_value=False):
            original_env = dict(os.environ)
            original_path = list(sys.path)
            
            manager.deactivate()
            
            # Verify environment was not modified
            assert dict(os.environ) == original_env
            assert list(sys.path) == original_path

    def test_deactivate_error(self, mock_environment, mock_env_builder):
        """Test error handling when deactivating a virtual environment fails."""
        manager = EnvManager("/test/venv/path")
        mock_env_builder.reset_mock()
        
        with mock.patch.object(manager, "is_active", return_value=True), \
             mock.patch.object(os.environ, "clear", side_effect=Exception("Deactivation failed")), \
             pytest.raises(RuntimeError, match="Failed to deactivate environment"):
            manager.deactivate()

    def test_is_active(self, mock_environment, mock_env_builder):
        """Test checking if a virtual environment is active."""
        manager = EnvManager("/test/venv/path")
        mock_env_builder.reset_mock()
        
        # Test all three cases for is_active
        with mock.patch.dict(os.environ, {"VIRTUAL_ENV": mock_environment.root}):
            assert manager.is_active() is True
        
        with mock.patch.dict(os.environ, {"VIRTUAL_ENV": "/other/path"}):
            assert manager.is_active() is False
        
        with mock.patch.dict(os.environ, {}, clear=True):
            assert manager.is_active() is False

    def test_context_manager(self, mock_environment, mock_env_builder):
        """Test using EnvManager as a context manager."""
        manager = EnvManager("/test/venv/path")
        mock_env_builder.reset_mock()
        
        with mock.patch.object(manager, "activate") as mock_activate, \
             mock.patch.object(manager, "deactivate") as mock_deactivate:
            with manager as env:
                assert env is manager
                mock_activate.assert_called_once()
            mock_deactivate.assert_called_once()
        
        mock_env_builder.assert_not_called()

    def test_install_pkg(self, mock_environment, mock_env_builder):
        """Test installing a package."""
        manager = EnvManager("/test/venv/path")
        mock_env_builder.reset_mock()
        
        with mock.patch("env_manager.env_manager.InstallPkgContextManager") as mock_ctx_manager:
            result = manager.install_pkg("package")
            mock_ctx_manager.assert_called_once_with(manager, "package")
            assert result is mock_ctx_manager.return_value


class TestInstallPkgContextManager:
    """Tests for the InstallPkgContextManager class."""

    @pytest.fixture
    def mock_env_manager(self):
        """Fixture to mock EnvManager."""
        mock_manager = mock.MagicMock()
        mock_manager.run.return_value = mock.MagicMock()
        mock_manager.logger = mock.MagicMock()
        return mock_manager

    def test_init(self, mock_env_manager):
        """Test initializing InstallPkgContextManager."""
        ctx = InstallPkgContextManager(mock_env_manager, "package")
        assert ctx.env_manager is mock_env_manager
        assert ctx.package == "package"
        mock_env_manager.run.assert_called_once_with("pip", "install", "package")

    def test_init_error(self, mock_env_manager):
        """Test error handling when package installation fails."""
        error = subprocess.CalledProcessError(1, "pip install package", stderr="Installation failed")
        mock_env_manager.run.side_effect = error
        
        with pytest.raises(RuntimeError, match="Failed to install package"):
            InstallPkgContextManager(mock_env_manager, "package")

    def test_context_manager(self, mock_env_manager):
        """Test using InstallPkgContextManager as a context manager."""
        ctx = InstallPkgContextManager(mock_env_manager, "package")
        
        # Reset the mock to clear the call from __init__
        mock_env_manager.run.reset_mock()
        
        with ctx as result:
            assert result is ctx
            # Package is already installed in __init__, so no calls here
            mock_env_manager.run.assert_not_called()
        
        # Check that uninstall was called on exit
        mock_env_manager.run.assert_called_once_with("pip", "uninstall", "-y", "package")

    def test_context_manager_uninstall_error(self, mock_env_manager):
        """Test error handling when package uninstallation fails."""
        ctx = InstallPkgContextManager(mock_env_manager, "package")
        
        # Reset the mock to clear the call from __init__
        mock_env_manager.run.reset_mock()
        
        # Set up the error for uninstallation
        error = subprocess.CalledProcessError(1, "pip uninstall -y package", stderr="Uninstallation failed")
        mock_env_manager.run.side_effect = error
        
        with pytest.raises(RuntimeError, match="Failed to uninstall package"):
            with ctx:
                pass
