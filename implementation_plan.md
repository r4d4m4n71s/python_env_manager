# Implementation Plan: Add Progress Bar to Environment Manager

## 1. Update Dependencies

Add Rich library to the dependencies in pyproject.toml:

```toml
[project]
dependencies = [
    "rich>=10.0.0"
]
```

## 2. Create New ProgressRunner Class

Create a new file `env_manager/progress_runner.py` with a class to handle progress bar functionality:

```python
"""
Progress Runner Module

This module provides a class to run commands with a Rich progress bar display,
extending the functionality of the EnvManager class.
"""

import os
import sys
import re
import io
import time
import subprocess
from typing import Optional, Any, Dict, List, Tuple, Union, Callable

# Only import Rich when this module is used
try:
    from rich.progress import Progress, TextColumn, BarColumn, TimeElapsedColumn
    from rich.console import Console
except ImportError:
    # Provide placeholder for type hints when Rich is not installed
    class Progress:
        pass
    class Console:
        pass

class ProgressRunner:
    """
    A utility class to run commands with a Rich progress bar.
    
    This class extends the command execution capabilities of EnvManager
    by adding a real-time progress bar that tracks command execution.
    """
    
    def __init__(self, logger, env):
        """
        Initialize a ProgressRunner instance.
        
        Args:
            logger: The logger instance to use for logging.
            env: The Environment instance containing environment information.
        """
        self.logger = logger
        self.env = env
    
    def prepare_command(self, cmd_args: Tuple[str, ...], kwargs: Dict[str, Any]) -> Tuple[Union[str, List[str]], Dict[str, Any]]:
        """
        Prepare the command for execution, similar to EnvManager.run.
        
        Args:
            cmd_args: Command and arguments as separate strings.
            kwargs: Additional arguments to pass to subprocess.run.
            
        Returns:
            Tuple containing the prepared shell command and updated kwargs.
        """
        is_windows = os.name == "nt"
        cmd_list = [str(arg) for arg in cmd_args]
        
        # Determine command execution strategy
        activate_script = os.path.join(
            self.env.bin,
            "activate.bat" if is_windows else "activate"
        )
        
        # Prepare the command similarly to the run method
        if os.path.exists(activate_script):
            # Virtual environment with activation script
            # Set common shell command properties
            kwargs['shell'] = True
            
            # Extract Python code for -c commands
            is_python_c_command = len(cmd_list) >= 2 and cmd_list[0] == "python" and cmd_list[1] == "-c"
            
            if is_python_c_command:
                # Properly handle Python -c command with quoted code
                python_code = " ".join(cmd_list[2:])
                cmd_part = f'python -c "{python_code}"'
            else:
                # Standard command
                cmd_part = " ".join(cmd_list)
            
            # Platform-specific activation and shell setup
            if is_windows:
                shell_cmd = f'"{activate_script}" && {cmd_part}'
            else:
                shell_cmd = f'source "{activate_script}" && {cmd_part}'
                kwargs['executable'] = '/bin/bash'
        else:
            # Local Python or no activation script
            kwargs['shell'] = False
            
            if cmd_list and cmd_list[0].lower() == 'python':
                # Use environment's Python executable
                python_exe = self.env.python if os.path.exists(self.env.python) else sys.executable
                shell_cmd = [python_exe] + cmd_list[1:]
            else:
                # Look for command in environment's bin directory
                cmd_path = os.path.join(
                    self.env.bin,
                    cmd_list[0] + (".exe" if is_windows else "")
                )
                if not os.path.exists(cmd_path):
                    cmd_path = cmd_list[0]
                shell_cmd = [cmd_path] + cmd_list[1:]
        
        return shell_cmd, kwargs
    
    def create_progress_bar(self, cmd_list: List[str]) -> Tuple[Progress, int]:
        """
        Create and configure a Rich progress bar.
        
        Args:
            cmd_list: The command being executed, for display purposes.
            
        Returns:
            Tuple containing the configured Progress instance and the task ID.
        """
        # Import here to avoid dependency for users not using progress features
        console = Console()
        terminal_width = console.width
        bar_width = int(terminal_width * 0.4)  # Use 40% of terminal width
        
        progress = Progress(
            TextColumn("[bold blue]{task.description}"),
            BarColumn(bar_width=bar_width),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            TextColumn("[cyan]{task.fields[output]}"),
            console=console,
            expand=True
        )
        
        # Create the task
        task_id = progress.add_task(
            f"Running: {' '.join(cmd_list)}", 
            total=100,
            output=""
        )
        
        return progress, task_id
    
    def estimate_progress(self, line: str) -> Optional[float]:
        """
        Estimate progress percentage from command output.
        
        Args:
            line: A line of command output to analyze.
            
        Returns:
            A float between 0 and 1 representing progress, or None if progress
            cannot be estimated from the line.
        """
        # Patterns for progress detection
        percent_pattern = re.compile(r'(?:^|\D)(\d{1,3})%(?:\D|$)')
        count_pattern = re.compile(r'(?:^|\D)(\d+)\s*(?:of|\/)\s*(\d+)(?:\D|$)')
        
        # Try to find percentage indicators
        percent_match = percent_pattern.search(line)
        if percent_match:
            try:
                percent = int(percent_match.group(1))
                return min(percent, 100) / 100.0
            except (ValueError, IndexError):
                pass
        
        # Try to find count indicators
        count_match = count_pattern.search(line)
        if count_match:
            try:
                current = int(count_match.group(1))
                total = int(count_match.group(2))
                if total > 0:
                    return min(current / total, 1.0)
            except (ValueError, IndexError):
                pass
        
        # No progress indicator found
        return None
    
    def run_with_capture(self, process, progress, task_id, cmd_list):
        """
        Run a process with output capture and progress tracking.
        
        Args:
            process: The subprocess.Popen instance.
            progress: The Rich Progress instance.
            task_id: The task ID in the progress bar.
            cmd_list: The original command list for error reporting.
            
        Returns:
            A subprocess.CompletedProcess instance with the execution results.
        """
        # Create buffers for stdout and stderr
        stdout_buffer = io.StringIO()
        stderr_buffer = io.StringIO()
        
        # Variables for tracking process output
        return_code = None
        last_progress = 0
        last_output = ""
        
        # Read output in real-time
        while True:
            # Check if process has exited
            return_code = process.poll()
            if return_code is not None and not (process.stdout or process.stderr):
                break
            
            # Read stdout
            if process.stdout:
                line = process.stdout.readline()
                if line:
                    stdout_buffer.write(line)
                    # Update last output for display
                    last_output = line.strip()[:50] + "..." if len(line) > 50 else line.strip()
                    # Try to estimate progress
                    progress_value = self.estimate_progress(line)
                    if progress_value is not None:
                        last_progress = progress_value * 100
            
            # Read stderr
            if process.stderr:
                line = process.stderr.readline()
                if line:
                    stderr_buffer.write(line)
                    # Update last output for display if it looks important
                    if "error" in line.lower() or "warning" in line.lower():
                        last_output = "ERROR: " + (line.strip()[:45] + "..." if len(line) > 45 else line.strip())
            
            # Update progress
            progress.update(task_id, completed=last_progress, output=last_output)
            
            # Small sleep to prevent CPU overload
            time.sleep(0.05)
            
            # If both streams are empty and process has exited, we're done
            if return_code is not None and process.stdout.readable() and process.stderr.readable():
                if not process.stdout.readable() and not process.stderr.readable():
                    break
        
        # Complete the progress bar
        progress.update(task_id, completed=100, output="Completed" if return_code == 0 else f"Failed (code {return_code})")
        
        # Get stdout and stderr content
        stdout = stdout_buffer.getvalue()
        stderr = stderr_buffer.getvalue()
        
        # Create a CompletedProcess object
        return subprocess.CompletedProcess(
            args=cmd_list,
            returncode=return_code,
            stdout=stdout,
            stderr=stderr
        )
    
    def run_without_capture(self, process, progress, task_id, cmd_list):
        """
        Run a process without output capture but with progress tracking.
        
        Args:
            process: The subprocess.Popen instance.
            progress: The Rich Progress instance.
            task_id: The task ID in the progress bar.
            cmd_list: The original command list for error reporting.
            
        Returns:
            A subprocess.CompletedProcess instance with the execution results.
        """
        return_code = None
        last_progress = 0
        
        # For non-capture mode, just wait for process to complete
        # and periodically update the progress bar (as indeterminate)
        while True:
            return_code = process.poll()
            if return_code is not None:
                break
            
            # Update progress as pulsing/indeterminate
            last_progress = (last_progress + 5) % 100
            progress.update(task_id, completed=last_progress, output="Running...")
            time.sleep(0.2)
        
        # Complete the progress bar
        progress.update(task_id, completed=100, output="Completed" if return_code == 0 else f"Failed (code {return_code})")
        
        # Create a CompletedProcess object
        return subprocess.CompletedProcess(
            args=cmd_list,
            returncode=return_code,
            stdout=None,
            stderr=None
        )
    
    def run(self, cmd_args: Tuple[str, ...], capture_output: bool = True, **kwargs: Any) -> subprocess.CompletedProcess:
        """
        Execute a command with a progress bar.
        
        Args:
            cmd_args: Command and arguments as separate strings.
            capture_output: Whether to capture command output (default: True).
            **kwargs: Additional arguments to pass to subprocess.run.
            
        Returns:
            subprocess.CompletedProcess: Result of the command execution.
            
        Raises:
            ValueError: If no command is provided.
            RuntimeError: If command execution fails.
        """
        if not cmd_args:
            raise ValueError("No command provided")
            
        # Set default kwargs
        kwargs.setdefault('text', True)
        kwargs.setdefault('check', True)
        
        # We need to handle capturing output manually for the progress bar
        kwargs.pop('capture_output', None)
        
        try:
            cmd_list = [str(arg) for arg in cmd_args]
            
            # Prepare the command
            shell_cmd, kwargs = self.prepare_command(cmd_args, kwargs)
            
            # Get startupinfo for Windows
            startupinfo = None
            if os.name == "nt":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            # Create the progress bar
            with self.create_progress_bar(cmd_list)[0] as progress:
                task_id = progress.task_ids[0]
                
                # Setup process with pipes
                process = subprocess.Popen(
                    shell_cmd,
                    stdout=subprocess.PIPE if capture_output else None,
                    stderr=subprocess.PIPE if capture_output else None,
                    universal_newlines=True,
                    env=os.environ,
                    startupinfo=startupinfo,
                    **{k: v for k, v in kwargs.items() if k not in ['text', 'check', 'capture_output']}
                )
                
                # Run the process with or without output capture
                if capture_output:
                    result = self.run_with_capture(process, progress, task_id, cmd_list)
                else:
                    result = self.run_without_capture(process, progress, task_id, cmd_list)
                
                # Check the return code if requested
                if kwargs.get('check', False) and result.returncode != 0:
                    raise subprocess.CalledProcessError(
                        result.returncode, cmd_list, output=getattr(result, 'stdout', None),
                        stderr=getattr(result, 'stderr', None)
                    )
                
                # Log result
                self.logger.info(f"Successfully executed command with progress bar: {' '.join(cmd_list)}")
                return result
                
        except subprocess.CalledProcessError as e:
            # Let CalledProcessError propagate for proper error handling
            self.logger.error(f"Command failed: {' '.join(cmd_list)}, return code: {e.returncode}")
            if hasattr(e, 'stdout') and e.stdout:
                self.logger.error(f"Command stdout: {e.stdout}")
            if hasattr(e, 'stderr') and e.stderr:
                self.logger.error(f"Command stderr: {e.stderr}")
            raise
        except Exception as e:
            self.logger.error(f"Failed to execute command: {e}")
            raise RuntimeError(f"Failed to execute command: {e}") from e
```

## 3. Create EnvManagerWithProgress Class

Create a new class that extends EnvManager in `env_manager/env_manager.py`:

```python
class EnvManagerWithProgress(EnvManager):
    """
    Environment Manager with Progress Bar support.
    
    This class extends EnvManager to add progress bar functionality for command execution.
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize EnvManagerWithProgress with same parameters as EnvManager."""
        super().__init__(*args, **kwargs)
        self._progress_runner = None
    
    @property
    def progress_runner(self):
        """Lazy-initialize the progress runner to avoid importing Rich until needed."""
        if self._progress_runner is None:
            from env_manager.progress_runner import ProgressRunner
            self._progress_runner = ProgressRunner(self.logger, self.env)
        return self._progress_runner
    
    def run(self, *cmd_args: str, capture_output: bool = True, progressBar: bool = False, **kwargs: Any) -> subprocess.CompletedProcess:
        """
        Execute a command in the environment context with optional progress bar.
        
        This method extends the original run method by adding a progress bar
        option that displays command execution progress in real-time.
        
        Args:
            *cmd_args: Command and arguments as separate strings.
            capture_output: Whether to capture command output (default: True).
            progressBar: Whether to display a progress bar (default: False).
            **kwargs: Additional arguments to pass to subprocess.run.
            
        Returns:
            subprocess.CompletedProcess: Result of the command execution.
            
        Raises:
            ValueError: If no command is provided.
            RuntimeError: If command execution fails.
        """
        if progressBar:
            return self.progress_runner.run(cmd_args, capture_output=capture_output, **kwargs)
        else:
            return super().run(*cmd_args, capture_output=capture_output, **kwargs)
```

## 4. Update Import in __init__.py

Update `env_manager/__init__.py` to expose the new class:

```python
# Add this line to the existing imports
from env_manager.env_manager import EnvManagerWithProgress
```

## 5. Testing Strategy

Add tests for the new functionality in `tests/test_env_manager.py`:

```python
class TestEnvManagerWithProgress:
    """Tests for the EnvManagerWithProgress class."""
    
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
        with mock.patch("env_manager.env_manager.ProgressRunner") as mock_runner:
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
            
            # Verify progress_runner.run was called
            mock_progress_runner.run.assert_called_once()
            assert result is mock_progress_runner.run.return_value
    
    def test_run_without_progress(self, mock_environment, mock_env_builder, mock_subprocess):
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
```

## 6. Implementation Steps

1. Update pyproject.toml to add Rich dependency
2. Create new progress_runner.py module with ProgressRunner class
3. Add EnvManagerWithProgress class to env_manager.py
4. Update __init__.py to expose the new class
5. Add tests for the new functionality
6. Test the implementation with various commands

## 7. Considerations

- This design separates concerns by keeping progress functionality in its own class
- The implementation allows lazy loading of the Rich dependency
- Progress estimation works with percentage-based and count-based outputs
- For commands without progress indicators, it shows a pulsing progress bar
- Error handling is consistent with the existing run method
- Live output is displayed in the progress bar's status column