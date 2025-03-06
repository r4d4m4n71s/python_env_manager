"""
Simple test script for the progress bar functionality.
"""

import os
import sys
import time
from pathlib import Path

# Add the parent directory to the Python path so we can import the env_manager package
sys.path.append(str(Path(__file__).parent.parent))

from env_manager import EnvManagerWithProgress

def main():
    """Run a simple command with progress bar."""
    print("Simple Progress Bar Test")
    print("=======================")
    
    # Create a temporary environment for the example
    env_path = os.path.join(os.path.dirname(__file__), "temp_env")
    
    # Create an EnvManagerWithProgress instance
    env_manager = EnvManagerWithProgress(env_path, clear=True)
    print(f"Created environment at: {env_path}")
    
    # Run a simple Python command with progress bar
    print("\nRunning a simple Python command with progress bar:")
    result = env_manager.run(
        "python", 
        "-c", 
        "import time; print('Starting...'); time.sleep(1); print('25%'); time.sleep(1); print('50%'); time.sleep(1); print('75%'); time.sleep(1); print('100%'); print('Done!')",
        progressBar=True
    )
    
    print("\nCommand output:")
    if result.stdout:
        print(result.stdout)
    
    # Clean up the temporary environment
    env_manager.remove()
    print(f"\nRemoved environment at: {env_path}")

if __name__ == "__main__":
    main()