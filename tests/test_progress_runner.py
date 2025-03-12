"""
Test module for ProgressRunner class.
"""

import subprocess
import time
from unittest.mock import MagicMock, patch

import pytest
from rich.console import Console

from env_manager.runners.progress_runner import ProgressRunner
from env_manager import env_manager


@pytest.fixture
def mock_env_manager():
    """Create a mock environment manager for testing."""
    mock_env = MagicMock(spec=env_manager.EnvManager)
    mock_env.logger = MagicMock()
    
    # Set up a return value for prepare_command method
    mock_env.prepare_command.return_value = (
        ["echo", "test"],  # shell_cmd
        {"capture_output": True}  # run_kwargs
    )
    
    return mock_env


@pytest.fixture
def mock_console_status():
    """Mock the rich console status to avoid actual console interactions."""
    with patch('rich.console.Console.status') as mock_status:
        mock_status_context = MagicMock()
        mock_status.return_value.__enter__.return_value = mock_status_context
        yield mock_status, mock_status_context


@pytest.fixture
def progress_runner(mock_env_manager):
    """Create a configured ProgressRunner instance."""
    return ProgressRunner().with_env(mock_env_manager)


class TestProgressRunner:
    """Test cases for the ProgressRunner class."""

    def test_initialization(self):
        """Test that the runner is properly initialized."""
        runner = ProgressRunner()
        assert runner.env_manager is None
        assert isinstance(runner.console, Console)

    def test_with_env(self, mock_env_manager):
        """Test that with_env properly configures the runner."""
        runner = ProgressRunner()
        result = runner.with_env(mock_env_manager)
        
        assert runner.env_manager == mock_env_manager
        assert result == runner  # Should return self

    def test_run_without_env_manager(self):
        """Test that run raises ValueError when no env_manager is configured."""
        runner = ProgressRunner()
        
        with pytest.raises(ValueError, match="Runner not configured with an environment manager"):
            runner.run("echo", "test")

    @patch("subprocess.run")
    @patch("rich.console.Console.status")
    @patch("time.time")
    def test_run_success(self, mock_time, mock_status, mock_subprocess_run, mock_env_manager):
        """Test successful command execution with progress spinner."""
        # Mock time.time() to return increasing values
        mock_time.side_effect = [10.0, 10.5, 11.0, 11.5]
        
        # Mock the context manager for console.status
        mock_status_context = MagicMock()
        mock_status.return_value.__enter__.return_value = mock_status_context
        
        # Mock subprocess.run
        mock_completed_process = MagicMock(spec=subprocess.CompletedProcess)
        mock_subprocess_run.return_value = mock_completed_process
        
        # Create and configure runner
        runner = ProgressRunner().with_env(mock_env_manager)
        
        # Execute the run method
        result = runner.run("test", "command")
        
        # Verify prepare_command was called correctly
        mock_env_manager.prepare_command.assert_called_once_with(
            "test", "command", capture_output=True
        )
        
        # Verify subprocess.run was called with the prepared command
        mock_subprocess_run.assert_called_once()
        
        # Verify the spinner was updated
        mock_status_context.update.assert_called()
        
        # Verify success was logged
        mock_env_manager.logger.info.assert_called_once()
        
        # Verify the result
        assert result == mock_completed_process

    @patch("subprocess.run")
    @patch("rich.console.Console.status")
    def test_run_subprocess_error(self, mock_status, mock_subprocess_run, mock_env_manager):
        """Test handling of subprocess.CalledProcessError."""
        # Mock the context manager for console.status
        mock_status_context = MagicMock()
        mock_status.return_value.__enter__.return_value = mock_status_context
        
        # Mock subprocess.run to raise CalledProcessError
        error = subprocess.CalledProcessError(1, ["echo", "test"])
        error.stdout = b"stdout content"
        error.stderr = b"stderr content"
        mock_subprocess_run.side_effect = error
        
        # Create and configure runner
        runner = ProgressRunner().with_env(mock_env_manager)
        
        # Execute the run method and expect the error to propagate
        with pytest.raises(subprocess.CalledProcessError):
            runner.run("test", "command")
        
        # Verify error was logged
        mock_env_manager.logger.error.assert_called()

    @patch("subprocess.run")
    @patch("rich.console.Console.status")
    def test_run_general_exception(self, mock_status, mock_subprocess_run, mock_env_manager):
        """Test handling of general exceptions during execution."""
        # Mock the context manager for console.status
        mock_status_context = MagicMock()
        mock_status.return_value.__enter__.return_value = mock_status_context
        
        # Mock subprocess.run to raise a general exception
        mock_subprocess_run.side_effect = Exception("Test error")
        
        # Create and configure runner
        runner = ProgressRunner().with_env(mock_env_manager)
        
        # Execute the run method and expect RuntimeError
        with pytest.raises(RuntimeError, match="Failed to execute command"):
            runner.run("test", "command")
        
        # Verify error was logged
        mock_env_manager.logger.error.assert_called_once_with(
            "Failed to execute command: Test error"
        )