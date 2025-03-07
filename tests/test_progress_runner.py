"""
Test module for ProgressRunner class.
"""

import os
import subprocess
import time
from unittest.mock import MagicMock, patch

import pytest
from rich.console import Console
from rich.spinner import Spinner

from env_manager.runners.progress_runner import ProgressRunner
from env_manager import env_manager


class TestProgressRunner:
    """Test cases for the ProgressRunner class."""

    def setup_method(self):
        """Set up test fixtures for each test method."""
        self.mock_env_manager = MagicMock(spec=env_manager.EnvManager)
        self.mock_env_manager.logger = MagicMock()
        
        # Set up a return value for _prepare_command method
        self.mock_env_manager._prepare_command.return_value = (
            ["echo", "test"],  # shell_cmd
            {"capture_output": True}  # run_kwargs
        )
        
        self.runner = ProgressRunner().with_env(self.mock_env_manager)

    def test_initialization(self):
        """Test that the runner is properly initialized."""
        runner = ProgressRunner()
        assert runner.env_manager is None
        assert isinstance(runner.console, Console)

    def test_with_env(self):
        """Test that with_env properly configures the runner."""
        runner = ProgressRunner()
        result = runner.with_env(self.mock_env_manager)
        
        assert runner.env_manager == self.mock_env_manager
        assert result == runner  # Should return self

    def test_run_without_env_manager(self):
        """Test that run raises ValueError when no env_manager is configured."""
        runner = ProgressRunner()
        
        with pytest.raises(ValueError, match="Runner not configured with an environment manager"):
            runner.run("echo", "test")

    @patch("subprocess.run")
    @patch("rich.console.Console.status")
    @patch("time.time")
    def test_run_success(self, mock_time, mock_status, mock_subprocess_run):
        """Test successful command execution with progress spinner."""
        # Mock time.time() to consistently return increasing values for testing
        # First value is the start time, then each update needs a value
        time_values = [10.0]
        # Add 10 more increasing values to handle multiple status updates
        time_values.extend([10.0 + i * 0.5 for i in range(1, 10)])
        mock_time.side_effect = time_values
        
        # Mock the context manager for console.status
        mock_status_context = MagicMock()
        mock_status.return_value.__enter__.return_value = mock_status_context
        
        # Mock subprocess.run to return a successful CompletedProcess
        mock_completed_process = MagicMock(spec=subprocess.CompletedProcess)
        mock_subprocess_run.return_value = mock_completed_process
        
        # Execute the run method
        result = self.runner.run("test", "command")
        
        # Verify the environment manager's _prepare_command was called correctly
        self.mock_env_manager._prepare_command.assert_called_once_with(
            "test", "command", capture_output=True
        )
        
        # Verify subprocess.run was called with the prepared command
        mock_subprocess_run.assert_called_once_with(
            ["echo", "test"], env=mock_subprocess_run.call_args.kwargs['env'], capture_output=True
        )
        
        # Verify the spinner was updated with timing information
        mock_status_context.update.assert_called()
        
        # Verify the success was logged
        self.mock_env_manager.logger.info.assert_called_once()
        
        # Verify the result is the mocked CompletedProcess
        assert result == mock_completed_process

    @patch("subprocess.run")
    @patch("rich.console.Console.status")
    def test_run_subprocess_error(self, mock_status, mock_subprocess_run):
        """Test handling of subprocess.CalledProcessError."""
        # Mock the context manager for console.status
        mock_status_context = MagicMock()
        mock_status.return_value.__enter__.return_value = mock_status_context
        
        # Mock subprocess.run to raise CalledProcessError
        error = subprocess.CalledProcessError(1, ["echo", "test"])
        error.stdout = b"stdout content"
        error.stderr = b"stderr content"
        mock_subprocess_run.side_effect = error
        
        # Execute the run method and expect the error to propagate
        with pytest.raises(subprocess.CalledProcessError):
            self.runner.run("test", "command")
        
        # Verify error was logged
        self.mock_env_manager.logger.error.assert_called()

    @patch("subprocess.run")
    @patch("rich.console.Console.status")
    def test_run_general_exception(self, mock_status, mock_subprocess_run):
        """Test handling of general exceptions during execution."""
        # Mock the context manager for console.status
        mock_status_context = MagicMock()
        mock_status.return_value.__enter__.return_value = mock_status_context
        
        # Mock subprocess.run to raise a general exception
        mock_subprocess_run.side_effect = Exception("Test error")
        
        # Execute the run method and expect RuntimeError
        with pytest.raises(RuntimeError, match="Failed to execute command"):
            self.runner.run("test", "command")
        
        # Verify error was logged
        self.mock_env_manager.logger.error.assert_called_once_with(
            "Failed to execute command: Test error"
        )


@pytest.fixture
def mock_env_manager():
    """Create a mock environment manager for regression testing."""
    mock_env = MagicMock(spec=env_manager.EnvManager)
    mock_env.logger = MagicMock()
    
    # Setup _prepare_command to return command in format expected by subprocess.run
    def prepare_command(*args, **kwargs):
        cmd_args = list(args)
        run_kwargs = {k: v for k, v in kwargs.items()}
        if "capture_output" in run_kwargs:
            run_kwargs["capture_output"] = True
        return cmd_args, run_kwargs
    
    mock_env._prepare_command.side_effect = prepare_command
    return mock_env


@pytest.fixture
def mock_console_status():
    """Mock the rich console status to avoid actual console interactions."""
    with patch('env_manager.runners.progress_runner.Console.status') as mock_status:
        mock_status_context = MagicMock()
        mock_status.return_value.__enter__.return_value = mock_status_context
        yield mock_status, mock_status_context


@pytest.fixture
def progress_runner(mock_env_manager, mock_console_status):
    """Create a configured ProgressRunner instance with mocked dependencies."""
    return ProgressRunner().with_env(mock_env_manager)


class TestProgressRunnerRegression:
    """Regression tests for the ProgressRunner class."""

    def test_python_print_command(self, progress_runner, mock_env_manager, mock_console_status):
        """Test execution of a Python print command (more reliable than echo)."""
        # Unpack the mock_console_status fixture
        _, mock_status_context = mock_console_status
        
        # Run a Python print command instead of echo (more cross-platform compatible)
        test_message = "Progress Runner Test"
        result = progress_runner.run(
            "python", "-c", f"print('{test_message}')"
        )
        
        # Verify the command executed successfully
        assert result.returncode == 0
        assert test_message in result.stdout.decode().strip()
        
        # Verify that status updates were called (spinner and timer were updated)
        assert mock_status_context.update.called
        
        # Verify success was logged
        mock_env_manager.logger.info.assert_called_once()

    @pytest.mark.parametrize("sleep_time", [0.1])  # Short time for CI/CD
    def test_command_with_duration(self, progress_runner, mock_env_manager, mock_console_status, sleep_time):
        """Test command that runs for a specific duration."""
        # Unpack the mock_console_status fixture
        _, mock_status_context = mock_console_status
        
        # This test verifies the timer actually updates during execution
        start_time = time.time()
        
        # Use Python's sys.executable to run a Python sleep command
        # This is more reliable across platforms than using shell sleep commands
        result = progress_runner.run(
            "python", "-c", f"import time; time.sleep({sleep_time})"
        )
        
        end_time = time.time()
        
        # Verify the command ran for at least the sleep duration
        assert end_time - start_time >= sleep_time
        
        # Verify the command executed successfully
        assert result.returncode == 0
        
        # Verify that status updates were called (spinner and timer were updated)
        assert mock_status_context.update.called
        
        # Verify success was logged
        mock_env_manager.logger.info.assert_called_once()

    def test_failing_command(self, progress_runner, mock_env_manager, mock_console_status):
        """Test handling of a command that fails."""
        # Setup subprocess.run to raise a CalledProcessError
        with patch('subprocess.run') as mock_run:
            # Configure mock to raise CalledProcessError
            mock_called_proc_error = subprocess.CalledProcessError(1, ["python", "-c", "import sys; sys.exit(1)"])
            mock_called_proc_error.stdout = b""
            mock_called_proc_error.stderr = b"Simulated error"
            mock_run.side_effect = mock_called_proc_error
            
            # Run a command that should now fail due to our mocked exception
            # The ProgressRunner re-raises CalledProcessError directly
            with pytest.raises(subprocess.CalledProcessError):
                progress_runner.run("python", "-c", "import sys; sys.exit(1)")
        
        # Verify error was logged
        mock_env_manager.logger.error.assert_called()