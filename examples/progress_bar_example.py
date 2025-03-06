"""
Example script demonstrating the progress bar functionality in EnvManagerWithProgress.

This script shows how to use the EnvManagerWithProgress class to run commands
with a progress bar that displays real-time progress information.
"""

import os
import sys
import time
from pathlib import Path

# Add the parent directory to the Python path so we can import the env_manager package
sys.path.append(str(Path(__file__).parent.parent))

from env_manager import EnvManagerWithProgress

def main():
    """Run example commands with progress bar."""
    print("EnvManagerWithProgress Example")
    print("==============================")
    
    # Create a temporary environment for the example
    env_path = os.path.join(os.path.dirname(__file__), "temp_env")
    
    # Create an EnvManagerWithProgress instance
    env_manager = EnvManagerWithProgress(env_path, clear=True)
    print(f"Created environment at: {env_path}")
    
    # Example 1: Run a simple Python command with progress bar
    print("\nExample 1: Running a simple Python command with progress bar")
    result = env_manager.run(
        "python", 
        "-c", 
        """
import time
for i in range(10):
    print(f'Processing step {i+1}/10...')
    time.sleep(0.5)
print('Command completed successfully!')
        """,
        progressBar=True
    )
    
    # Example 2: Run pip list with progress bar
    print("\nExample 2: Running pip list with progress bar")
    result = env_manager.run("pip", "list", progressBar=True)
    
    # Example 3: Run pip install with progress bar
    print("\nExample 3: Installing a package with progress bar")
    result = env_manager.run("pip", "install", "requests", progressBar=True)
    
    # Clean up the temporary environment
    env_manager.remove()
    print(f"\nRemoved environment at: {env_path}")

if __name__ == "__main__":
    main()