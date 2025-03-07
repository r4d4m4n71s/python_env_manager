"""
Progress Runner Module

This module provides a runner that displays a spinner and timer while executing commands.
"""

import os
import subprocess
import time
from typing import Any

from rich.console import Console

from env_manager.runners.irunner import IRunner
from env_manager import env_manager


class ProgressRunner(IRunner):
    """
    Runner that displays a spinner and timer while executing commands.
    
    This runner extends the standard runner functionality by showing a
    spinner and elapsed time during command execution. The spinner and timer
    are aligned to the left for better visibility.
    """
    
    def __init__(self, inline_output=None):
        """
        Initialize a ProgressRunner instance with a Rich console.
        
        Args:
            inline_output (int, optional): Number of output lines to show inline during execution.
                If None, no inline output is shown.
                If a positive integer, shows the last N lines of output during execution.
        """
        self.env_manager = None
        # Initialize Rich console for displaying spinner and status updates
        self.console = Console()
        # Store the inline output parameter
        self.inline_output = inline_output
        
    def with_env(self, env_manager: 'env_manager.EnvManager') -> 'ProgressRunner':
        """
        Configure the runner with an environment manager.
        
        Args:
            env_manager: The environment manager to use for command execution.
            
        Returns:
            ProgressRunner: The configured runner instance (self).
        """
        self.env_manager = env_manager
        return self
        
    def run(self, *cmd_args: str, capture_output: bool = True, **kwargs: Any) -> subprocess.CompletedProcess:
        """
        Execute a command with a progress spinner and timer.
        
        Displays a spinner and elapsed time counter while the command executes,
        both aligned to the left of the console. If inline_output is set, also
        displays the last N lines of command output in real-time.
        
        Args:
            *cmd_args: Command and arguments as separate strings.
            capture_output: Whether to capture command output (default: True).
            **kwargs: Additional arguments to pass to subprocess.run.
            
        Returns:
            subprocess.CompletedProcess: Result of the command execution.
            
        Raises:
            ValueError: If no command is provided or runner is not configured.
            RuntimeError: If command execution fails.
        """
        if not self.env_manager:
            raise ValueError("Runner not configured with an environment manager")
            
        # Format the command string for display
        command_str = ' '.join([str(arg) for arg in cmd_args])
        
        try:
            # Prepare the command using the environment manager
            shell_cmd, run_kwargs = self.env_manager._prepare_command(
                *cmd_args, capture_output=capture_output, **kwargs
            )
            
            # Start time tracking for the elapsed timer
            start_time = time.time()
            
            # Display spinner and execute command
            result = None
            # Use the spinner name as a string, not a Spinner object
            with self.console.status(f"Running: {command_str}", spinner="dots", refresh_per_second=10) as status:
                # Define timer update function
                def update_status():
                    elapsed = time.time() - start_time
                    minutes, seconds = divmod(int(elapsed), 60)
                    # Format "Running:" and timer in blue color
                    return f"[blue]Running:[/blue] {command_str} [[blue]{minutes:02d}:{seconds:02d}[/blue]] "
                
                try:
                    # Initial status update
                    status.update(update_status())
                    
                    # Execute command - pass check=False to handle return codes in our own way
                    if 'check' in run_kwargs:
                        # Store the check value but remove it from kwargs
                        check_enabled = run_kwargs.pop('check')
                    else:
                        check_enabled = False
                    
                    # For commands that run quickly, we might not see timer updates
                    # So we'll set up a separate thread to update the timer while the command runs
                    import threading
                    stop_event = threading.Event()
                    
                    def update_timer():
                        while not stop_event.is_set():
                            status.update(update_status())
                            time.sleep(0.1)  # Update the timer 10 times per second
                    
                    # Start timer update thread
                    timer_thread = threading.Thread(target=update_timer)
                    timer_thread.daemon = True
                    timer_thread.start()
                    
                    try:
                        # Handle inline output display if requested
                        if self.inline_output is not None and self.inline_output > 0:
                            # Keep track of recent output lines
                            output_lines = []
                            stdout_data = []
                            stderr_data = []
                            
                            # Filter run_kwargs to remove parameters not valid for Popen
                            popen_kwargs = {k: v for k, v in run_kwargs.items()
                                          if k not in ['stdout', 'stderr', 'text', 'encoding',
                                                      'capture_output', 'check']}
                            
                            # Create a process to capture output in real-time
                            process = subprocess.Popen(
                                shell_cmd,
                                env=os.environ,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                text=True,
                                **popen_kwargs
                            )
                            
                            # Function to read from a pipe and update display
                            def read_pipe(pipe, is_stderr=False):
                                for line in iter(pipe.readline, ''):
                                    if line:
                                        line = line.rstrip()
                                        # Store the line for result
                                        if is_stderr:
                                            stderr_data.append(line)
                                        else:
                                            stdout_data.append(line)
                                            
                                        # Update displayed lines
                                        output_lines.append(line)
                                        # Limit to last N lines
                                        while len(output_lines) > self.inline_output:
                                            output_lines.pop(0)
                                            
                                        # Update status with timer and output
                                        status_text = update_status()
                                        if output_lines:
                                            status_text += "\n" + "\n".join(output_lines)
                                        status.update(status_text)
                            
                            # Read stdout in main thread for real-time updates
                            read_pipe(process.stdout)
                            
                            # After stdout is done, read stderr
                            read_pipe(process.stderr, is_stderr=True)
                            
                            # Wait for process to complete
                            returncode = process.wait()
                            
                            # Create a CompletedProcess object with the captured output
                            stdout_output = "\n".join(stdout_data) if stdout_data else None
                            stderr_output = "\n".join(stderr_data) if stderr_data else None
                            
                            result = subprocess.CompletedProcess(
                                args=shell_cmd,
                                returncode=returncode,
                                stdout=stdout_output,
                                stderr=stderr_output
                            )
                        else:
                            # Run the command without inline output processing
                            result = subprocess.run(shell_cmd, env=os.environ, **run_kwargs)
                    finally:
                        # Stop the timer thread
                        stop_event.set()
                        timer_thread.join(timeout=1.0)  # Wait for thread to finish, but not indefinitely
                    
                    # If check_enabled and return code is non-zero, raise CalledProcessError
                    if check_enabled and result.returncode != 0:
                        raise subprocess.CalledProcessError(
                            result.returncode, shell_cmd,
                            output=result.stdout if hasattr(result, 'stdout') else None,
                            stderr=result.stderr if hasattr(result, 'stderr') else None
                        )
                    
                    # Final status update before completing
                    status.update(update_status())
                    
                except Exception as e:
                    # Update status with error information
                    status.update(f"Error: {str(e)}")
                    raise
            
            # Log success and return result
            self.env_manager.logger.info(f"Successfully executed command: {command_str}")
            return result
            
        except subprocess.CalledProcessError as e:
            # Log detailed error information from subprocess errors
            self.env_manager.logger.error(f"Command failed: {command_str}, return code: {e.returncode}")
            if e.stdout:
                self.env_manager.logger.error(f"Command stdout: {e.stdout}")
            if e.stderr:
                self.env_manager.logger.error(f"Command stderr: {e.stderr}")
            raise
            
        except Exception as e:
            # Log general execution errors
            self.env_manager.logger.error(f"Failed to execute command: {e}")
            raise RuntimeError(f"Failed to execute command: {e}") from e