"""
Unit tests for the progress_runner module.

These tests focus on the ProgressRunner class and its integration with EnvManagerWithProgress.
"""

import os
import sys
import subprocess
import logging
from unittest import mock
import pytest

from env_manager import Environment, EnvManager, EnvManagerWithProgress
from env_manager.progress_runner import ProgressRunner


class TestProgressRunner:
    """Tests for the ProgressRunner class."""
    
    @pytest.fixture
    def mock_environment(self):
        """Fixture to mock Environment class."""
        mock_env = mock.MagicMock()
        mock_env.root = "/test/venv/path"
        mock_env.bin = "/test/venv/path/bin"
        mock_env.lib = "/test/venv/path/lib"
        mock_env.python = "/test/venv/path/bin/python"
        mock_env.name = "path"
        mock_env.is_virtual = True
        return mock_env
    
    @pytest.fixture
    def mock_logger(self):
        """Fixture to mock logger."""
        return mock.MagicMock(spec=logging.Logger)
    
    @pytest.fixture
    def progress_runner(self, mock_environment, mock_logger):
        """Fixture to create a ProgressRunner instance."""
        return ProgressRunner(mock_logger, mock_environment)
    
    def test_init(self, progress_runner, mock_environment, mock_logger):
        """Test initializing ProgressRunner."""
        assert progress_runner.logger is mock_logger
        assert progress_runner.env is mock_environment
    
    def test_prepare_command_with_activation_script(self, progress_runner):
        """Test preparing a command with an activation script."""
        with mock.patch("os.path.exists", return_value=True), \
             mock.patch("os.name", "nt"):
            cmd_args = ("pip", "install", "package")
            kwargs = {}
            
            shell_cmd, updated_kwargs = progress_runner.prepare_command(cmd_args, kwargs)
            
            assert isinstance(shell_cmd, str)
            assert "activate.bat" in shell_cmd
            assert "pip install package" in shell_cmd
            assert updated_kwargs.get("shell") is True
    
    def test_prepare_command_without_activation_script(self, progress_runner):
        """Test preparing a command without an activation script."""
        with mock.patch("os.path.exists", return_value=False), \
             mock.patch("os.name", "nt"), \
             mock.patch("sys.executable", progress_runner.env.python):
            cmd_args = ("python", "-c", "print('hello')")
            kwargs = {}
            
            shell_cmd, updated_kwargs = progress_runner.prepare_command(cmd_args, kwargs)
            
            assert isinstance(shell_cmd, list)
            assert shell_cmd[0] == progress_runner.env.python
            assert "-c" in shell_cmd
            assert "print('hello')" in shell_cmd
            assert updated_kwargs.get("shell") is False
    
    def test_estimate_progress_percentage(self, progress_runner):
        """Test estimating progress from percentage indicators."""
        assert progress_runner.estimate_progress("Progress: 50%") == 0.5
        assert progress_runner.estimate_progress("50% complete") == 0.5
        assert progress_runner.estimate_progress("Downloaded 50%") == 0.5
        assert progress_runner.estimate_progress("No percentage here") is None
    
    def test_estimate_progress_count(self, progress_runner):
        """Test estimating progress from count indicators."""
        assert progress_runner.estimate_progress("Processing 5 of 10 files") == 0.5
        assert progress_runner.estimate_progress("Step 2/4 completed") == 0.5
        assert progress_runner.estimate_progress("No count here") is None
    
    def test_create_progress_bar(self, progress_runner):
        """Test creating a progress bar."""
        # Create a real Progress instance for testing
        try:
            from rich.progress import Progress
            from rich.console import Console
            
            # Call the method
            progress, task_id = progress_runner.create_progress_bar(["pip", "install", "package"])
            
            # Verify results
            assert isinstance(progress, Progress)
            assert isinstance(task_id, int)
            assert task_id >= 0
        except ImportError:
            # Skip test if Rich is not installed
            pytest.skip("Rich library not installed")
    
    @mock.patch("subprocess.Popen")
    def test_run_with_capture(self, mock_popen, progress_runner):
        """Test running a process with output capture."""
        # Setup mock process
        mock_process = mock_popen.return_value
        mock_process.poll.side_effect = [None, 0]
        mock_process.stdout.readline.return_value = "Progress: 50%"
        mock_process.stderr.readline.return_value = ""
        mock_process.stdout.readable.return_value = False
        mock_process.stderr.readable.return_value = False
        
        # Setup mock progress
        mock_progress = mock.MagicMock()
        
        result = progress_runner.run_with_capture(
            mock_process, mock_progress, 1, ["pip", "install", "package"]
        )
        
        assert isinstance(result, subprocess.CompletedProcess)
        assert result.returncode == 0
        assert mock_progress.update.called
    
    @mock.patch("subprocess.Popen")
    def test_run_without_capture(self, mock_popen, progress_runner):
        """Test running a process without output capture."""
        # Setup mock process
        mock_process = mock_popen.return_value
        mock_process.poll.side_effect = [None, 0]
        
        # Setup mock progress
        mock_progress = mock.MagicMock()
        
        result = progress_runner.run_without_capture(
            mock_process, mock_progress, 1, ["pip", "install", "package"]
        )
        
        assert isinstance(result, subprocess.CompletedProcess)
        assert result.returncode == 0
        assert mock_progress.update.called
    
    @mock.patch("subprocess.Popen")
    @mock.patch("rich.progress.Progress")
    @mock.patch("rich.console.Console")
    def test_run(self, mock_console_class, mock_progress_class, mock_popen, progress_runner):
        """Test the main run method."""
        # Setup mocks
        mock_console = mock_console_class.return_value
        mock_console.width = 100
        
        mock_progress = mock_progress_class.return_value
        mock_progress.add_task.return_value = 1
        mock_progress.task_ids = [1]
        mock_progress.__enter__.return_value = mock_progress
        
        mock_process = mock_popen.return_value
        mock_process.poll.side_effect = [None, 0]
        mock_process.stdout.readline.return_value = "Progress: 50%"
        mock_process.stderr.readline.return_value = ""
        mock_process.stdout.readable.return_value = False
        mock_process.stderr.readable.return_value = False
        
        with mock.patch.object(progress_runner, "prepare_command") as mock_prepare, \
             mock.patch.object(progress_runner, "create_progress_bar") as mock_create_bar, \
             mock.patch.object(progress_runner, "run_with_capture") as mock_run_with_capture:
            
            mock_prepare.return_value = (["python", "-c", "print('hello')"], {})
            mock_create_bar.return_value = (mock_progress, 1)
            mock_run_with_capture.return_value = subprocess.CompletedProcess(
                args=["python", "-c", "print('hello')"],
                returncode=0,
                stdout="hello",
                stderr=""
            )
            
            result = progress_runner.run(("python", "-c", "print('hello')"))
            
            assert isinstance(result, subprocess.CompletedProcess)
            assert result.returncode == 0
            assert mock_prepare.called
            assert mock_create_bar.called
            assert mock_run_with_capture.called
    
    def test_run_error(self, progress_runner):
        """Test error handling in the run method."""
        with mock.patch.object(progress_runner, "prepare_command") as mock_prepare:
            mock_prepare.side_effect = Exception("Test error")
            
            with pytest.raises(RuntimeError, match="Failed to execute command"):
                progress_runner.run(("python", "-c", "print('hello')"))


class TestEnvManagerWithProgress:
    """Tests for the EnvManagerWithProgress class."""
    
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
    def mock_env_builder(self):
        """Fixture to mock EnvBuilder."""
        with mock.patch("env_manager.env_manager.EnvBuilder") as mock_builder:
            mock_instance = mock_builder.return_value
            mock_instance.create.return_value = None
            yield mock_builder
    
    @pytest.fixture
    def mock_progress_runner(self):
        """Fixture to mock ProgressRunner."""
        with mock.patch("env_manager.progress_runner.ProgressRunner") as mock_runner:
            mock_instance = mock_runner.return_value
            mock_instance.run.return_value = mock.MagicMock()
            yield mock_instance
    
    def test_init(self, mock_environment, mock_env_builder):
        """Test initializing EnvManagerWithProgress."""
        manager = EnvManagerWithProgress("/test/venv/path")
        assert isinstance(manager, EnvManager)
        assert manager._progress_runner is None
    
    def test_progress_runner_property(self, mock_environment, mock_env_builder):
        """Test the progress_runner property."""
        with mock.patch("env_manager.progress_runner.ProgressRunner") as mock_runner:
            manager = EnvManagerWithProgress("/test/venv/path")
            runner = manager.progress_runner
            assert runner is not None
            assert manager._progress_runner is not None
            # Verify property returns same instance on second call
            assert manager.progress_runner is runner
    
    def test_run_with_progress(self, mock_environment, mock_env_builder, mock_progress_runner):
        """Test running a command with a progress bar."""
        with mock.patch.object(EnvManagerWithProgress, "progress_runner", 
                              new_callable=mock.PropertyMock) as mock_property:
            mock_property.return_value = mock_progress_runner
            
            manager = EnvManagerWithProgress("/test/venv/path")
            
            # Test running a command with progress bar
            result = manager.run("pip", "install", "package", progressBar=True)
            
            # Verify progress_runner.run was called with unpacked arguments
            mock_progress_runner.run.assert_called_once_with("pip", "install", "package",
                                                           capture_output=True)
            assert result is mock_progress_runner.run.return_value
    
    def test_run_without_progress(self, mock_environment, mock_env_builder):
        """Test running a command without a progress bar."""
        with mock.patch.object(EnvManager, "run") as mock_run:
            mock_run.return_value = mock.MagicMock()
            
            manager = EnvManagerWithProgress("/test/venv/path")
            
            # Test running a command without progress bar
            result = manager.run("pip", "install", "package", progressBar=False)
            
            # Verify parent run method was called
            mock_run.assert_called_once_with("pip", "install", "package", 
                                            capture_output=True)
            assert result is mock_run.return_value