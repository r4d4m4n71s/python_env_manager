"""
Test module for LocalRunner class.
"""

import sys
import subprocess
import logging
from unittest.mock import MagicMock, patch

import pytest

from env_manager.runners.local_runner import LocalRunner
from env_manager.env_local import PythonLocal
from env_manager import env_manager


@pytest.fixture
def mock_env_manager():
    """Create a mock environment manager for testing."""
    mock_env = MagicMock(spec=env_manager.EnvManager)
    mock_env.logger = MagicMock(spec=logging.Logger)
    return mock_env


@pytest.fixture
def local_runner(mock_env_manager):
    """Create a configured LocalRunner instance."""
    return LocalRunner().with_env(mock_env_manager)


class TestLocalRunner:
    """Test cases for the LocalRunner class."""

    def test_initialization(self):
        """Test that the runner is properly initialized."""
        runner = LocalRunner()
        assert isinstance(runner.logger, logging.Logger)

    def test_with_env(self, mock_env_manager):
        """Test that with_env properly configures the runner."""
        runner = LocalRunner()
        result = runner.with_env(mock_env_manager)
        
        assert runner.logger == mock_env_manager.logger
        assert result == runner  # Should return self

    @patch('env_manager.env_local.PythonLocal.find_base_executable')
    @patch('subprocess.run')
    def test_run_python_command(self, mock_subprocess_run, mock_find_base_executable, local_runner):
        """Test running a Python command uses base Python executable."""
        # Mock the base executable finder
        base_executable = '/path/to/base/python'
        mock_find_base_executable.return_value = base_executable
        
        # Mock subprocess.run
        mock_completed_process = MagicMock(spec=subprocess.CompletedProcess)
        mock_subprocess_run.return_value = mock_completed_process
        
        # Run a Python command
        result = local_runner.run('python', '-c', "print('test')")
        
        # Verify base executable was used
        mock_subprocess_run.assert_called_once()
        call_args = mock_subprocess_run.call_args[0][0]
        assert call_args[0] == base_executable
        assert call_args[1:] == ['-c', "print('test')"]
        
        # Verify success was logged
        local_runner.logger.info.assert_called_once()
        
        # Verify result
        assert result == mock_completed_process

    @patch('env_manager.env_local.PythonLocal.find_base_executable')
    @patch('subprocess.run')
    def test_run_non_python_command(self, mock_subprocess_run, mock_find_base_executable, local_runner):
        """Test running a non-Python command uses the command directly."""
        # Mock find_base_executable to return a path
        mock_find_base_executable.return_value = '/path/to/base/python'
        
        # Mock subprocess.run
        mock_completed_process = MagicMock(spec=subprocess.CompletedProcess)
        mock_subprocess_run.return_value = mock_completed_process
        
        # Run a non-Python command
        result = local_runner.run('pip', 'list')
        
        # Verify the command was used directly
        mock_subprocess_run.assert_called_once_with(
            ['pip', 'list'], 
            text=True, 
            check=True, 
            capture_output=True
        )
        
        # Verify success was logged
        local_runner.logger.info.assert_called_once()
        
        # Verify result
        assert result == mock_completed_process

    @patch('env_manager.env_local.PythonLocal.find_base_executable')
    @patch('subprocess.run')
    def test_run_with_custom_kwargs(self, mock_subprocess_run, mock_find_base_executable, local_runner):
        """Test running a command with custom kwargs."""
        # Mock find_base_executable to return a path
        mock_find_base_executable.return_value = '/path/to/base/python'
        
        # Mock subprocess.run
        mock_completed_process = MagicMock(spec=subprocess.CompletedProcess)
        mock_subprocess_run.return_value = mock_completed_process
        
        # Run a command with custom kwargs
        result = local_runner.run('pip', 'list', check=False, text=False, timeout=10)
        
        # Verify subprocess.run was called with the custom kwargs
        mock_subprocess_run.assert_called_once_with(
            ['pip', 'list'], 
            check=False, 
            text=False, 
            timeout=10,
            capture_output=True
        )
        
        # Verify result
        assert result == mock_completed_process

    @patch('env_manager.env_local.PythonLocal.find_base_executable')
    @patch('subprocess.run')
    def test_fallback_to_sys_executable(self, mock_subprocess_run, mock_find_base_executable, local_runner):
        """Test fallback to sys.executable when base executable not found."""
        # Mock find_base_executable to return None (not found)
        mock_find_base_executable.return_value = None
        
        # Mock subprocess.run
        mock_completed_process = MagicMock(spec=subprocess.CompletedProcess)
        mock_subprocess_run.return_value = mock_completed_process
        
        # Run a Python command
        with patch('sys.executable', '/current/python'):
            result = local_runner.run('python', '-c', "print('test')")
        
        # Verify sys.executable was used as fallback
        mock_subprocess_run.assert_called_once()
        call_args = mock_subprocess_run.call_args[0][0]
        assert call_args[0] == '/current/python'
        
        # Verify result
        assert result == mock_completed_process

    def test_run_no_command(self, local_runner):
        """Test that run raises ValueError when no command is provided."""
        with pytest.raises(ValueError, match="No command provided"):
            local_runner.run()

    @patch('env_manager.env_local.PythonLocal.find_base_executable')
    @patch('subprocess.run')
    def test_run_subprocess_error(self, mock_subprocess_run, mock_find_base_executable, local_runner):
        """Test handling of subprocess.CalledProcessError."""
        # Mock find_base_executable to return a path
        mock_find_base_executable.return_value = '/path/to/base/python'
        
        # Mock subprocess.run to raise CalledProcessError
        error = subprocess.CalledProcessError(1, ['pip', 'install', 'nonexistent-package'])
        error.stdout = "stdout content"
        error.stderr = "stderr content"
        mock_subprocess_run.side_effect = error
        
        # Run a command that will fail
        with pytest.raises(subprocess.CalledProcessError):
            local_runner.run('pip', 'install', 'nonexistent-package')
        
        # Verify error was logged
        local_runner.logger.error.assert_called()

    @patch('env_manager.env_local.PythonLocal.find_base_executable')
    @patch('subprocess.run')
    def test_run_general_exception(self, mock_subprocess_run, mock_find_base_executable, local_runner):
        """Test handling of general exceptions during execution."""
        # Mock find_base_executable to return a path
        mock_find_base_executable.return_value = '/path/to/base/python'
        
        # Mock subprocess.run to raise a general exception
        mock_subprocess_run.side_effect = Exception("Test error")
        
        # Run a command that will cause an exception
        with pytest.raises(RuntimeError, match="Failed to execute local command"):
            local_runner.run('pip', 'list')
        
        # Verify error was logged
        local_runner.logger.error.assert_called_once_with(
            "Failed to execute local command: Test error"
        )