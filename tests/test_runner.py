"""
Test module for standard Runner class.
"""

import os
import subprocess
from unittest.mock import MagicMock, patch

import pytest

from env_manager.runners.runner import Runner
from env_manager import env_manager


@pytest.fixture
def mock_env_manager():
    """Create a mock environment manager for testing."""
    mock_env = MagicMock(spec=env_manager.EnvManager)
    mock_env.logger = MagicMock()
    
    # Set up a return value for prepare_command method
    mock_env.prepare_command.return_value = (
        ["python", "-m", "pip", "list"],  # shell_cmd
        {"capture_output": True, "text": True}  # run_kwargs
    )
    
    return mock_env


@pytest.fixture
def runner(mock_env_manager):
    """Create a configured Runner instance."""
    return Runner().with_env(mock_env_manager)


class TestRunner:
    """Test cases for the Runner class."""

    def test_initialization(self):
        """Test that the runner is properly initialized."""
        runner = Runner()
        assert runner.env_manager is None

    def test_with_env(self, mock_env_manager):
        """Test that with_env properly configures the runner."""
        runner = Runner()
        result = runner.with_env(mock_env_manager)
        
        assert runner.env_manager == mock_env_manager
        assert result == runner  # Should return self

    def test_run_without_env_manager(self):
        """Test that run raises ValueError when no env_manager is configured."""
        runner = Runner()
        
        with pytest.raises(ValueError, match="Runner not configured with an environment manager"):
            runner.run("python", "-c", "print('test')")

    @patch("subprocess.run")
    def test_run_success(self, mock_subprocess_run, runner, mock_env_manager):
        """Test successful command execution."""
        # Mock subprocess.run
        mock_completed_process = MagicMock(spec=subprocess.CompletedProcess)
        mock_subprocess_run.return_value = mock_completed_process
        
        # Execute the run method
        result = runner.run("python", "-m", "pip", "list")
        
        # Verify prepare_command was called correctly
        mock_env_manager.prepare_command.assert_called_once_with(
            "python", "-m", "pip", "list", capture_output=True
        )
        
        # Verify subprocess.run was called with the prepared command
        mock_subprocess_run.assert_called_once_with(
            ["python", "-m", "pip", "list"], 
            env=os.environ, 
            capture_output=True, 
            text=True
        )
        
        # Verify success was logged
        mock_env_manager.logger.info.assert_called_once()
        
        # Verify the result
        assert result == mock_completed_process

    @patch("subprocess.run")
    def test_run_subprocess_error(self, mock_subprocess_run, runner, mock_env_manager):
        """Test handling of subprocess.CalledProcessError."""
        # Mock subprocess.run to raise CalledProcessError
        error = subprocess.CalledProcessError(1, ["python", "-c", "exit(1)"])
        error.stdout = "stdout content"
        error.stderr = "stderr content"
        mock_subprocess_run.side_effect = error
        
        # Execute the run method and expect the error to propagate
        with pytest.raises(subprocess.CalledProcessError):
            runner.run("python", "-c", "exit(1)")
        
        # Verify error was logged
        mock_env_manager.logger.error.assert_called()

    @patch("subprocess.run")
    def test_run_general_exception(self, mock_subprocess_run, runner, mock_env_manager):
        """Test handling of general exceptions during execution."""
        # Mock subprocess.run to raise a general exception
        mock_subprocess_run.side_effect = Exception("Test error")
        
        # Execute the run method and expect RuntimeError
        with pytest.raises(RuntimeError, match="Failed to execute command"):
            runner.run("python", "-c", "print('test')")
        
        # Verify error was logged
        mock_env_manager.logger.error.assert_called_once_with(
            "Failed to execute command: Test error"
        )

    @patch("subprocess.run")
    def test_run_with_capture_output_false(self, mock_subprocess_run, mock_env_manager):
        """Test running command with capture_output=False."""
        # Override the default prepare_command return value
        mock_env_manager.prepare_command.return_value = (
            ["python", "-c", "print('test')"],
            {"capture_output": False}
        )
        
        runner = Runner().with_env(mock_env_manager)
        
        # Mock subprocess.run
        mock_completed_process = MagicMock(spec=subprocess.CompletedProcess)
        mock_subprocess_run.return_value = mock_completed_process
        
        # Execute the run method
        result = runner.run("python", "-c", "print('test')", capture_output=False)
        
        # Verify prepare_command was called with capture_output=False
        mock_env_manager.prepare_command.assert_called_once_with(
            "python", "-c", "print('test')", capture_output=False
        )
        
        # Verify subprocess.run was called with the prepared command
        mock_subprocess_run.assert_called_once_with(
            ["python", "-c", "print('test')"],
            env=os.environ,
            capture_output=False
        )