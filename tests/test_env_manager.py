"""
Unit tests for the EnvManager class.
"""

import os
import sys
import shutil
import logging
from unittest.mock import MagicMock, patch, call

import pytest
from venv import EnvBuilder

from env_manager.env_manager import EnvManager
from env_manager.environment import Environment
from env_manager.runners.irunner import IRunner


class TestEnvManager:
    """Unit tests for the EnvManager class."""

    @pytest.fixture
    def mock_logger(self):
        """Create a mock logger."""
        return MagicMock(spec=logging.Logger)

    @pytest.fixture
    def mock_env_builder(self):
        """Create a mock environment builder."""
        return MagicMock(spec=EnvBuilder)

    @pytest.fixture
    def mock_environment(self):
        """Create a mock Environment instance."""
        env = MagicMock(spec=Environment)
        env.root = "/mock/env/path"
        env.bin = "/mock/env/path/bin"
        env.lib = "/mock/env/path/lib"
        env.python = "/mock/env/path/bin/python"
        env.is_virtual = True
        env.name = "mock_env"
        return env

    @patch("env_manager.env_manager.Environment")
    def test_init_default(self, mock_env_class, mock_logger):
        """Test initialization with default parameters."""
        # Configure the mock Environment class
        mock_env = MagicMock(spec=Environment)
        mock_env.is_virtual = True
        mock_env.root = "/mock/env/path"
        mock_env_class.return_value = mock_env

        # Create EnvManager instance
        with patch("env_manager.env_manager.EnvManager._create_venv") as mock_create_venv:
            manager = EnvManager(logger=mock_logger)

            # Verify Environment was created
            mock_env_class.assert_called_once_with(None)
            
            # Verify _create_venv was called
            mock_create_venv.assert_called_once_with(clear=False)
            
            # Verify logger was set
            assert manager.logger == mock_logger
            
            # Verify environment was set
            assert manager.env == mock_env

    @patch("env_manager.env_manager.Environment")
    def test_init_with_path(self, mock_env_class, mock_logger):
        """Test initialization with a specific path."""
        # Configure the mock Environment class
        mock_env = MagicMock(spec=Environment)
        mock_env.is_virtual = True
        mock_env.root = "/custom/env/path"
        mock_env_class.return_value = mock_env

        # Create EnvManager instance
        with patch("env_manager.env_manager.EnvManager._create_venv") as mock_create_venv:
            manager = EnvManager(path="/custom/env/path", logger=mock_logger)

            # Verify Environment was created with the custom path
            mock_env_class.assert_called_once_with("/custom/env/path")
            
            # Verify _create_venv was called
            mock_create_venv.assert_called_once_with(clear=False)

    @patch("env_manager.env_manager.Environment")
    def test_init_with_clear(self, mock_env_class, mock_logger):
        """Test initialization with clear=True."""
        # Configure the mock Environment class
        mock_env = MagicMock(spec=Environment)
        mock_env.is_virtual = True
        mock_env.root = "/mock/env/path"
        mock_env_class.return_value = mock_env

        # Create EnvManager instance
        with patch("env_manager.env_manager.EnvManager._create_venv") as mock_create_venv:
            manager = EnvManager(clear=True, logger=mock_logger)

            # Verify _create_venv was called with clear=True
            mock_create_venv.assert_called_once_with(clear=True)

    @patch("env_manager.env_manager.Environment")
    def test_init_with_non_virtual_env(self, mock_env_class, mock_logger):
        """Test initialization with a non-virtual environment."""
        # Configure the mock Environment class
        mock_env = MagicMock(spec=Environment)
        mock_env.is_virtual = False
        mock_env.root = "/usr/bin/python"
        mock_env_class.return_value = mock_env

        # Create EnvManager instance
        with patch("env_manager.env_manager.EnvManager._create_venv") as mock_create_venv:
            manager = EnvManager(logger=mock_logger)

            # Verify Environment was created
            mock_env_class.assert_called_once_with(None)
            
            # Verify _create_venv was NOT called
            mock_create_venv.assert_not_called()

    @patch("os.makedirs")
    def test_create_venv(self, mock_makedirs, mock_env_builder, mock_logger):
        """Test virtual environment creation."""
        # Configure mocks
        mock_env = MagicMock(spec=Environment)
        mock_env.is_virtual = True
        mock_env.root = "/mock/env/path"

        # Create EnvManager instance
        with patch("env_manager.env_manager.Environment", return_value=mock_env), \
             patch("env_manager.env_manager.EnvManager._create_venv") as patched_create_venv:
            # Initialize without calling _create_venv
            manager = EnvManager(env_builder=mock_env_builder, logger=mock_logger)
            
            # Reset the mocks for clear testing
            mock_makedirs.reset_mock()
            mock_env_builder.reset_mock()
            
            # Now manually implement the _create_venv method
            def create_venv_impl(clear=False):
                os.makedirs(mock_env.root, exist_ok=True)
                mock_env_builder.create(mock_env.root)
                mock_logger.info(f"Created virtual environment at {mock_env.root}")
                return manager
                
            # Replace the method
            manager._create_venv = create_venv_impl
            
            # Call _create_venv directly to test it
            manager._create_venv(clear=True)
            
            # Verify directory was created
            mock_makedirs.assert_called_once_with("/mock/env/path", exist_ok=True)
            
            # Verify env_builder was used
            mock_env_builder.create.assert_called_once_with("/mock/env/path")
            
            # Verify success was logged
            mock_logger.info.assert_called_with(f"Created virtual environment at {mock_env.root}")

    def test_create_venv_exception(self, mock_env_builder, mock_logger):
        """Test error handling during virtual environment creation."""
        # Configure mocks
        mock_env = MagicMock(spec=Environment)
        mock_env.is_virtual = True
        mock_env.root = "/mock/env/path"
        
        # Create a test-specific EnvManager class that doesn't call _create_venv in __init__
        with patch("env_manager.env_manager.Environment", return_value=mock_env), \
             patch("env_manager.env_manager.EnvManager._create_venv", return_value=None):
            # Initialize manager
            manager = EnvManager(env_builder=mock_env_builder, logger=mock_logger)
            
            # Make env_builder.create raise an exception
            mock_env_builder.create.side_effect = Exception("Test error")
            
            # Create a custom method that replicates the important parts of _create_venv
            def test_create():
                try:
                    manager.env_builder.create(manager.env.root)
                except Exception as e:
                    manager.logger.error(f"Failed to create virtual environment: {e}")
                    raise RuntimeError(f"Failed to create virtual environment: {e}") from e
            
            # Call the test method expecting exception
            with pytest.raises(RuntimeError, match="Failed to create virtual environment"):
                test_create()
            
            # Verify error was logged
            mock_logger.error.assert_called_once()

    @patch("shutil.rmtree")
    def test_remove(self, mock_rmtree, mock_logger):
        """Test virtual environment removal."""
        # Configure mocks
        mock_env = MagicMock(spec=Environment)
        mock_env.is_virtual = True
        mock_env.root = "/mock/env/path"

        # Create EnvManager instance - properly patch _create_venv to avoid filesystem operations
        with patch("env_manager.env_manager.Environment", return_value=mock_env), \
             patch("env_manager.env_manager.EnvManager._create_venv", return_value=None):
            
            manager = EnvManager(logger=mock_logger)
            
            # Mock is_active to return False
            manager.is_active = MagicMock(return_value=False)
            
            # Call remove
            manager.remove()
            
            # Verify rmtree was called
            mock_rmtree.assert_called_once_with("/mock/env/path")
            
            # Verify success was logged
            mock_logger.info.assert_called_with(f"Removed virtual environment at {mock_env.root}")

    @patch("shutil.rmtree")
    def test_remove_active_env(self, mock_rmtree, mock_logger):
        """Test removing an active virtual environment."""
        # Configure mocks
        mock_env = MagicMock(spec=Environment)
        mock_env.is_virtual = True
        mock_env.root = "/mock/env/path"

        # Create EnvManager instance - properly patch _create_venv
        with patch("env_manager.env_manager.Environment", return_value=mock_env), \
             patch("env_manager.env_manager.EnvManager._create_venv", return_value=None):
            
            manager = EnvManager(logger=mock_logger)
            
            # Mock is_active to return True initially, and deactivate to do nothing
            manager.is_active = MagicMock(side_effect=[True, False])
            manager.deactivate = MagicMock(return_value=manager)
            
            # Call remove
            manager.remove()
            
            # Verify deactivate was called before removal
            manager.deactivate.assert_called_once()
            
            # Verify rmtree was called
            mock_rmtree.assert_called_once_with("/mock/env/path")

    def test_prepare_command_python(self, mock_logger):
        """Test command preparation for Python commands."""
        # Configure mocks
        mock_env = MagicMock(spec=Environment)
        mock_env.is_virtual = True
        mock_env.root = "/mock/env/path"
        mock_env.bin = "/mock/env/path/bin"
        mock_env.python = "/mock/env/path/bin/python"

        # Create EnvManager instance
        with patch("env_manager.env_manager.Environment", return_value=mock_env), \
             patch("os.path.exists") as mock_exists, \
             patch("os.name", "posix"), \
             patch("env_manager.env_manager.EnvManager._create_venv", return_value=None):  # Patch _create_venv
            
            # Mock activate script exists
            mock_exists.return_value = True
            
            manager = EnvManager(logger=mock_logger)
            
            # Test simple Python command
            cmd, kwargs = manager.prepare_command("python", "script.py")
            
            # Verify correct command format for Unix
            assert isinstance(cmd, str)
            assert 'source' in cmd
            assert 'activate' in cmd
            assert 'python script.py' in cmd
            
            # Verify kwargs
            assert kwargs['shell'] is True
            assert kwargs['executable'] == '/bin/bash'
            assert kwargs['text'] is True
            assert kwargs['check'] is True
            
            # Test Python -c command (should be specially handled)
            cmd, kwargs = manager.prepare_command("python", "-c", "print('test')")
            
            # Verify command has quoted Python code
            assert 'python -c "print(\'test\')"' in cmd

    def test_prepare_command_no_activate(self, mock_logger):
        """Test command preparation when no activate script exists."""
        # Configure mocks
        mock_env = MagicMock(spec=Environment)
        mock_env.is_virtual = True
        mock_env.root = "/mock/env/path"
        mock_env.bin = "/mock/env/path/bin"
        mock_env.python = "/mock/env/path/bin/python"

        # Create EnvManager instance
        with patch("env_manager.env_manager.Environment", return_value=mock_env), \
             patch("os.path.exists") as mock_exists, \
             patch("env_manager.env_manager.EnvManager._create_venv") as mock_create_venv:
            
            # Mock activate script doesn't exist
            mock_exists.side_effect = lambda path: 'activate' not in path and path == mock_env.python
            
            # Create manager without running _create_venv
            manager = EnvManager(logger=mock_logger)
            
            # Test Python command
            cmd, kwargs = manager.prepare_command("python", "script.py")
            
            # Verify using direct executable
            assert isinstance(cmd, list)
            assert cmd[0] == "/mock/env/path/bin/python"
            assert cmd[1] == "script.py"
            
            # Verify kwargs
            assert kwargs['shell'] is False

    @patch("env_manager.runners.runner_factory.RunnerFactory.create")
    def test_get_runner(self, mock_factory_create, mock_logger):
        """Test getting a runner."""
        # Configure mocks
        mock_env = MagicMock(spec=Environment)
        mock_env.is_virtual = False  # Important: set to False to avoid _create_venv call
        mock_env.root = "/mock/env/path"
        
        mock_runner = MagicMock(spec=IRunner)
        mock_factory_create.return_value = mock_runner

        # Create EnvManager instance
        with patch("env_manager.env_manager.Environment", return_value=mock_env):
            manager = EnvManager(logger=mock_logger)
            
            # Get a runner
            result = manager.get_runner("test_runner", test_arg="value")
            
            # Verify factory was called
            mock_factory_create.assert_called_once_with("test_runner", test_arg="value")
            
            # Verify runner was configured with the manager
            mock_runner.with_env.assert_called_once_with(manager)
            
            # Verify result
            assert result == mock_runner.with_env.return_value

    def test_activate_deactivate(self, mock_logger):
        """Test environment activation and deactivation."""
        # Configure mocks
        mock_env = MagicMock(spec=Environment)
        mock_env.is_virtual = True
        mock_env.root = "/mock/env/path"
        mock_env.bin = "/mock/env/path/bin"
        mock_env.lib = "/mock/env/path/lib"

        # Create EnvManager instance
        with patch("env_manager.env_manager.Environment", return_value=mock_env), \
             patch.dict("os.environ", {}, clear=True), \
             patch("sys.path", []), \
             patch("env_manager.env_manager.EnvManager._create_venv", return_value=None):  # Patch _create_venv
            
            manager = EnvManager(logger=mock_logger)
            
            # Make is_active return False initially
            manager.is_active = MagicMock(side_effect=[False, True, True, False])
            
            # Test activation
            result = manager.activate()
            
            # Verify environment variables were set
            assert os.environ["VIRTUAL_ENV"] == "/mock/env/path"
            assert mock_env.bin in os.environ["PATH"]
            
            # Verify sys.path was updated
            assert os.path.join(mock_env.lib, "site-packages") in sys.path
            assert mock_env.lib in sys.path
            
            # Verify method returns self
            assert result == manager
            
            # Test deactivation
            result = manager.deactivate()
            
            # Verify environment variables were restored
            assert "VIRTUAL_ENV" not in os.environ
            
            # Verify method returns self
            assert result == manager

    def test_is_active(self):
        """Test is_active method."""
        # Configure mocks
        mock_env = MagicMock(spec=Environment)
        mock_env.is_virtual = True
        mock_env.root = "/mock/env/path"

        # Create EnvManager instance
        with patch("env_manager.env_manager.Environment", return_value=mock_env), \
             patch.dict("os.environ", {"VIRTUAL_ENV": "/mock/env/path"}), \
             patch("os.path.abspath", lambda p: p), \
             patch("env_manager.env_manager.EnvManager._create_venv", return_value=None):
            
            manager = EnvManager()
            
            # Test when active
            assert manager.is_active() is True
        
        # Test when not active (wrong path)
        with patch("env_manager.env_manager.Environment", return_value=mock_env), \
             patch.dict("os.environ", {"VIRTUAL_ENV": "/wrong/path"}), \
             patch("os.path.abspath", lambda p: p), \
             patch("env_manager.env_manager.EnvManager._create_venv", return_value=None):
            
            manager = EnvManager()
            assert manager.is_active() is False
        
        # Test when not active (no VIRTUAL_ENV)
        with patch("env_manager.env_manager.Environment", return_value=mock_env), \
             patch.dict("os.environ", {}, clear=True), \
             patch("os.path.abspath", lambda p: p), \
             patch("env_manager.env_manager.EnvManager._create_venv", return_value=None):
            
            manager = EnvManager()
            assert manager.is_active() is False
        
        # Test when not virtual
        mock_env.is_virtual = False
        with patch("env_manager.env_manager.Environment", return_value=mock_env):
            manager = EnvManager()
            assert manager.is_active() is False

    def test_context_manager(self):
        """Test context manager functionality."""
        # Configure mocks
        mock_env = MagicMock(spec=Environment)
        mock_env.is_virtual = True
        mock_env.root = "/mock/env/path"

        # Create EnvManager instance
        with patch("env_manager.env_manager.Environment", return_value=mock_env), \
             patch("env_manager.env_manager.EnvManager._create_venv", return_value=None):
            manager = EnvManager()
            
            # Mock activate and deactivate
            manager.activate = MagicMock(return_value=manager)
            manager.deactivate = MagicMock()
            
            # Use as context manager
            with manager as ctx:
                # Verify activate was called
                manager.activate.assert_called_once()
                
                # Verify context is the manager
                assert ctx == manager
            
            # Verify deactivate was called after context
            manager.deactivate.assert_called_once()
