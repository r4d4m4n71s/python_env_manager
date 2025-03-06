"""
Very simple test script for the progress bar functionality.
"""

from env_manager import EnvManagerWithProgress

# Create an EnvManagerWithProgress instance
env = EnvManagerWithProgress(".")

# Run a simple command with progress bar
print("Running command with progress bar...")
result = env.run("python", "-c", "print('Hello, world!')", progressBar=True)

# Print the result
print("\nCommand output:")
print(result.stdout)