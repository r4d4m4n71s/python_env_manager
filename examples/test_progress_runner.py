"""
Simple test script for the progress runner functionality.
"""
import os
import sys
import subprocess
import time
from pathlib import Path

# Add the parent directory to the Python path so we can import the env_manager package
sys.path.append(str(Path(__file__).parent.parent))

from env_manager import EnvManager 
from env_manager.runners import ProgressRunner

def main():
    """Run a simple command with progress spinner visualization."""
    print("Simple Progress Runner Test")
    print("=========================")
    
    # Create a temporary environment for the example
    env_path = os.path.join(os.getcwd(), ".test_env")
    
    # Create an EnvManager instance
    env_manager = EnvManager(env_path)
    print(f"Created environment at: {env_path}")
    
    # Define test commands with properly formatted Python code for -c option
    # When using -c, make sure all code is on a single line with no indentation
    short_cmd = ["python", "-c", "import time; print('Starting...'); time.sleep(2); print('Done!')"]
    
    # Use list comprehensions instead of traditional for loops to avoid syntax issues
    progress_cmd = [
        "python", "-c",
        "import time, sys; print('Starting...'); [print(f'Processing item {i+1}/10', flush=True) or time.sleep(2) for i in range(10)]; print('Done!')"
    ]
    
    error_cmd = [
        "python", "-c",
        "import time, sys; print('Starting...'); time.sleep(1); print('ERROR: Something went wrong!', file=sys.stderr); sys.exit(1)"
    ]

    # Example 1: Default ProgressRunner with capture_output=True
    print("\nExample 1: ProgressRunner with capture_output=True")
    runner = ProgressRunner().with_env(env_manager)
    
    try:
        result = runner.run(*progress_cmd)
        print("\nCommand completed successfully")
        print("Output:")
        print(result.stdout)
    except Exception as e:
        print(f"Error: {e}")

    # Example 2: ProgressRunner with capture_output=False
    print("\nExample 2: ProgressRunner with capture_output=False")
    runner = ProgressRunner().with_env(env_manager)
    
    try:
        result = runner.run(*progress_cmd, capture_output=False)
        print("\nCommand completed successfully")
        print("Output:")
        print(result.stdout)
    except Exception as e:
        print(f"Error: {e}")
    
    # Example 2.1: ProgressRunner with inline_output=1 (show last line)
    print("\nExample 2.1: ProgressRunner with inline_output=1 (showing last line)")
    runner = ProgressRunner(inline_output=1).with_env(env_manager)
    
    try:
        result = runner.run(*progress_cmd)
        print("\nCommand completed successfully")
        print("Output:")
        print(result.stdout)
    except Exception as e:
        print(f"Error: {e}")
    
    # Example 2.2: ProgressRunner with inline_output=3 (show last 3 lines)
    print("\nExample 2.2: ProgressRunner with inline_output=3 (showing last 3 lines)")
    runner = ProgressRunner(inline_output=3).with_env(env_manager)
    
    try:
        result = runner.run(*progress_cmd)
        print("\nCommand completed successfully")
        print("Output:")
        print(result.stdout)
    except Exception as e:
        print(f"Error: {e}")
        
    # Example 3: Error handling with check=True
    print("\nExample 3: Error handling with check=True:")
    
    try:
        result = runner.run(*error_cmd, check=True)
        print("This should not be printed as an exception should be raised")
    except subprocess.CalledProcessError as e:
        print(f"Expected error caught: {e}")
        print(f"Command stderr: {e.stderr}")
    
    # Example 4: Error handling with check=False (default)
    print("\nExample 4: Error handling with check=False (default):")
    
    try:
        result = runner.run(*error_cmd)
        print(f"Command failed with return code: {result.returncode}")
        print(f"Command stderr: {result.stderr}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    # Example 5: Running a command with a lot of output
    print("\nExample 5: Running a command with a lot of output (real-time display):")
    
    many_lines_cmd = [
        "python", "-c",
        "import time; [print(f'Line {i+1} of output') for i in range(100)]; [time.sleep(0.2) for _ in range(5)]"
    ]
    
    try:
        # Create a new runner with inline_output=3 for this test
        runner = ProgressRunner(inline_output=3).with_env(env_manager)
        # Use capture_output=False to see output in real-time
        result = runner.run(*many_lines_cmd, capture_output=False)
        print("\nCommand completed successfully")
    except Exception as e:
        print(f"Error: {e}")
    
    # Clean up the temporary environment
    # Uncomment to actually remove the test environment
    # env_manager.remove()
    # print(f"\nRemoved environment at: {env_path}")

if __name__ == "__main__":
    main()