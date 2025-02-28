# 🐍 Python Environment Manager

[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A powerful, cross-platform tool for managing Python virtual environments with a clean, intuitive API.

## ✨ Features

- 🔄 **Seamless Environment Switching** - Easily activate and deactivate environments
- 📦 **Package Management** - Install, use, and remove packages with simple commands
- 🛠️ **Command Execution** - Run commands in the context of any environment
- 🧩 **Context Manager Support** - Use with Python's `with` statement for clean code
- 🔌 **Cross-Platform** - Works on Windows, macOS, and Linux

## 📋 Installation

```bash
pip install python-env-manager
```

### 🚀 Simple Command Execution

This example demonstrates the basic workflow for managing a virtual environment and running commands within it.

```python
from env_manager import EnvManager

# Create a reference to a virtual environment
# If the environment doesn't exist, it will be created automatically
env = EnvManager("my_project_env")

# Run commands in the environment - each command runs in the context of the virtual environment
# Install a package without explicitly activating the environment
env.run("pip", "install", "requests")  # Isolated from your system Python packages

# Execute Python code with access to installed packages
# The -c flag allows running Python code directly from the command line
env.run("python", "-c", "import requests; print('Requests version:', requests.__version__)")

# Run a Python script with command-line arguments
# All imports in my_script.py will use packages from this environment
env.run("python", "my_script.py", "--arg1", "value1")

# Clean up by removing the environment when no longer needed
# This deletes the entire virtual environment directory
env.remove()  # Optional - only use when you want to delete the environment
```

### 🛠️ Creating a Custom Environment

Configure your virtual environment with specific options to meet your project requirements.

```python
from env_manager import EnvManager

# Create a new virtual environment at the specified path
# If the path doesn't exist, directories will be created automatically
env_manager = EnvManager("path/to/venv")  # Uses default settings

# For advanced use cases, create with custom options using Python's built-in EnvBuilder
from venv import EnvBuilder

# Configure a custom environment builder with specific options:
# - system_site_packages=True: Gives access to system-installed packages
# - with_pip=True: Ensures pip is installed in the new environment
custom_builder = EnvBuilder(system_site_packages=True, with_pip=True)

# Create environment with the custom configuration
# This provides more control over the environment creation process
env_manager = EnvManager("path/to/venv", env_builder=custom_builder)
```

### 📋 Running Commands

Execute various types of commands within your virtual environment with full control over inputs and outputs.

```python
env = EnvManager("path/to/venv")

# Package management commands - isolated from your system Python
# Install a specific package in the virtual environment
env.run("pip", "install", "requests")

# List all installed packages in the environment
env.run("pip", "list")  # Shows only packages in this environment

# Execute Python scripts with arguments
# The script runs with access to all packages installed in this environment
env.run("python", "my_script.py", "--arg1", "value1")

# Run inline Python code for quick tests or operations
# Useful for debugging or simple operations without creating a separate file
env.run("python", "-c", "print('Hello from virtual environment!')")

# Capture command output for programmatic use
# capture_output=True returns a CompletedProcess object with stdout and stderr
result = env.run("python", "--version", capture_output=True)
print(f"Python version: {result.stdout}")  # Access the captured standard output
```

### 🖥️ Working with Local Python

For cases when you need to use the system Python installation instead of a virtual environment.

```python
# Create an environment manager that uses the system Python
# Setting path=None tells EnvManager to use the current Python interpreter
local_env = EnvManager(path=None)  # No isolation - uses system packages

# Use a context manager for clean activation/deactivation
with local_env:
    # Run commands with the system Python installation
    # This prints the path to the system Python executable
    local_env.run("python", "-c", "import sys; print(sys.executable)")
```

### 🔌 Activation Methods

Three different ways to activate and use your virtual environments based on your specific needs.

```python
from env_manager import EnvManager

# Method 1: Explicit activation/deactivation
# Use this approach when you need fine-grained control over when the environment is active
env = EnvManager(".some_env")

# Explicitly activate the environment
# This sets up environment variables and Python paths
env.activate()

# Now the environment is active and you can:
# - Run Python scripts with packages from this environment
# - Install packages that will be isolated to this environment
# - Use command-line tools installed in this environment
result = env.run("python", "-c", "import sys; print(sys.executable)")
print(result.stdout)  # Shows Python executable from the virtual environment

# When finished, explicitly deactivate the environment
# This restores the original environment state
env.deactivate()

# Method 2: Context manager (recommended) ✨
# Use this approach for automatic activation/deactivation
# The environment is automatically activated when entering the context
# and deactivated when exiting, even if exceptions occur
with EnvManager(".venv") as venv:
    # Environment is now active
    # All operations here use the virtual environment
    venv.run("pip", "install", "requests")
    venv.run("python", "my_script.py")
    
    # Check if environment is active
    if venv.is_active():
        print("Environment is active!")
# Environment is automatically deactivated when exiting the context

# Method 3: Implicit activation for single commands
# The run() method automatically uses the environment for that specific command
# without requiring explicit activation
EnvManager(".some_env").run("python", "script.py")  # Environment used just for this command
```


### 📦 Package Management

Efficiently manage packages in your virtual environments with permanent or temporary installations.

```python
with EnvManager("path/to/venv") as env:
    # Install a package permanently in the environment
    # This package will remain available until explicitly uninstalled
    env.run("pip", "install", "requests")
    
    # Install a package temporarily using the specialized context manager
    # Perfect for testing or one-time use of a package
    with env.install_pkg("beautifulsoup4"):
        # The package is available only within this context block
        # Use the temporarily installed package
        env.run("python", "-c", "import bs4; print(bs4.__version__)")
    # beautifulsoup4 is automatically uninstalled when exiting the context
    # This keeps your environment clean and prevents dependency conflicts
```

### 🗑️ Environment Removal

Clean up resources by removing environments when they're no longer needed.

```python
# Create a reference to an existing environment
env_manager = EnvManager("path/to/venv")

# Use the environment for various tasks
# ...

# When the environment is no longer needed, remove it completely
# This deletes the entire directory and all installed packages
env_manager.remove()

# You can also use this pattern for temporary environments:
temp_env = EnvManager("temp_env")
try:
    # Use the temporary environment
    temp_env.run("pip", "install", "requests")
    temp_env.run("python", "script.py")
finally:
    # Always clean up, even if an exception occurs
    temp_env.remove()
```

## 📚 API Reference

Comprehensive documentation of the classes and methods available in the Python Environment Manager.

### 🔧 EnvManager Class

The main class for creating and managing Python virtual environments.

```python
EnvManager(
    path: Optional[str] = None,  # Path to the virtual environment
    clear: bool = False,         # Whether to clear existing environment
    env_builder: Optional[EnvBuilder] = None,  # Custom environment builder
    logger: Optional[logging.Logger] = None    # Custom logger
)
```

**Parameters:**
- `path`: Path to the virtual environment. If `None`, uses the current Python environment.
- `clear`: Whether to clear the environment directory if it already exists.
- `env_builder`: Custom EnvBuilder instance for environment creation with specific options.
- `logger`: Custom logger for the environment manager to control logging behavior.

**Methods:**
- `activate()`: Activate the environment by setting up environment variables and paths.
- `deactivate()`: Deactivate the environment and restore original environment state.
- `run(*cmd_args, **kwargs)`: Run a command in the environment with specified arguments.
- `install_pkg(package)`: Install a package temporarily (returns a context manager).
- `remove()`: Remove the virtual environment completely from the filesystem.
- `is_active()`: Check if the environment is currently active.

### 🏗️ Environment Class

Represents a Python environment with information about its structure and properties.

```python
Environment(
    path: Optional[str] = None,  # Path to the environment
    **kwargs                     # Additional configuration options
)
```

**Attributes:**
- `root`: Root directory of the environment (absolute path).
- `bin`: Directory containing executables (`bin` on Unix, `Scripts` on Windows).
- `lib`: Directory containing libraries and installed packages.
- `python`: Path to the Python executable within this environment.
- `name`: Environment name derived from the directory name.
- `is_virtual`: Boolean indicating whether the environment is a virtual environment.

**Methods:**
- `get_site_packages()`: Returns the path to the site-packages directory.
- `get_python_version()`: Returns the Python version used in this environment.

## 🌟 Real-World Examples

Practical examples demonstrating how to use Python Environment Manager in various scenarios.

### 📊 Example 1: Data Science Workflow

Create isolated environments for data analysis projects with specific package requirements.

```python
from env_manager import EnvManager

# Create a dedicated data science environment with all necessary tools
with EnvManager("path/to/data_science_env") as env:
    # Install the data science stack with a single command
    # Each package is isolated to this environment only
    env.run("pip", "install", "numpy", "pandas", "matplotlib", "scikit-learn")
    
    # Run a data analysis script with command-line arguments
    # All imports in the script will use the packages from this environment
    env.run("python", "analyze_data.py", "--input", "data.csv", "--output", "results.csv")
    
    # Execute multi-line Python code directly for quick visualization
    # This is useful for one-off analysis without creating separate files
    env.run("python", "-c", """
import matplotlib.pyplot as plt
import pandas as pd

# Load the processed data
data = pd.read_csv('results.csv')

# Create a visualization
plt.figure(figsize=(10, 6))
plt.plot(data['x'], data['y'])
plt.title('Analysis Results')
plt.savefig('plot.png')
print('Plot saved to plot.png')
    """)
```

### 🧪 Example 2: Testing with Different Package Versions

Easily test your code against multiple versions of dependencies without conflicts.

```python
from env_manager import EnvManager
import shutil
import os

# Define the versions you want to test against
versions = ["1.0.0", "1.1.0", "2.0.0"]

# Iterate through each version and run tests in isolated environments
for version in versions:
    # Create a unique environment name for each version
    env_path = f"test_env_{version.replace('.', '_')}"
    
    # Ensure a clean environment for each test run
    if os.path.exists(env_path):
        shutil.rmtree(env_path)
    
    # Create and use a fresh environment for this version
    with EnvManager(env_path) as env:
        # Install the specific version of the package
        env.run("pip", "install", f"package=={version}")
        
        # Run the test suite and capture results
        result = env.run("pytest", "tests/", capture_output=True)
        
        # Report test results for this version
        print(f"Test results for version {version}:")
        print(result.stdout)
        
        # The environment will be automatically deactivated when exiting the context
        # You could also add env.remove() here if you want to clean up immediately
```

### 🌐 Example 3: Web Development Project

Set up and manage a complete web development environment with database migrations.

```python
from env_manager import EnvManager

# Create a dedicated environment for your web project
with EnvManager("web_project_env") as env:
    # Install the web framework and all required dependencies
    # These packages are isolated from your system Python
    env.run("pip", "install", "flask", "flask-sqlalchemy", "flask-migrate")
    
    # Set up the database with Flask-Migrate
    # Initialize the migration repository
    env.run("flask", "db", "init")
    
    # Create the initial migration
    env.run("flask", "db", "migrate", "-m", "Initial migration")
    
    # Apply the migration to the database
    env.run("flask", "db", "upgrade")
    
    # Run the development server with debug mode enabled
    # The server will automatically reload when code changes
    env.run("flask", "run", "--debug")
    
    # When the context exits, the environment is deactivated
    # but remains available for future use
```

## 🤝 Contributing

We welcome contributions from the community to make Python Environment Manager even better!

### How to Contribute

1. **Fork the repository** on GitHub
2. **Clone your fork** to your local machine
3. **Create a new branch** for your feature or bugfix
4. **Make your changes** and add tests if applicable
5. **Run the tests** to ensure everything works
6. **Commit your changes** with clear, descriptive messages
7. **Push to your fork** and submit a pull request

### Development Guidelines

- Follow PEP 8 style guidelines
- Write tests for new features
- Update documentation for any changes
- Keep pull requests focused on a single topic

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2025 Python Environment Manager Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files.
```

---

<div align="center">
  <p>Made with ❤️ by the Python Environment Manager team</p>
  <p>
    <a href="https://github.com/yourusername/python-env-manager">GitHub</a> •
    <a href="https://pypi.org/project/python-env-manager/">PyPI</a> •
    <a href="https://python-env-manager.readthedocs.io/">Documentation</a>
  </p>
</div>