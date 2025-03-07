# 🐍 Python Environment Manager

[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)]()
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A powerful, cross-platform tool for managing Python virtual environments with a clean, intuitive API.

## 🌟 Elevate Your Python Development Workflow

`env_manager` provides complete virtual environment lifecycle management.

---

## ✨ Features

- 🔄 **Seamless Environment Switching** - Easily activate and deactivate environments
- 📦 **Package Management** - Install, use, and remove packages with simple commands
- 🛠️ **Command Execution** - Run commands in the context of any environment
- 🧩 **Context Manager Support** - Use with Python's `with` statement for clean code
- 🔌 **Cross-Platform** - Works on Windows, macOS, and Linux
- 🚀 **Effortless Environment Management** - Create and run commands in virtual environments on the fly
- 📊 **Progress Visualization** - Real-time progress bars for long-running operations
- 🔍 **Smart Consistency Checking** - Validate environment configurations and ensure package integrity
- 🛡️ **Robust Error Handling** - Detailed logging and comprehensive error messages
- 🧰 **Extensible Runner System** - Customize command execution with specialized runners

## 📋 Installation

```bash
pip install python-env-manager
```

### Package Name vs Import Name

Note the difference between the package name and import name:

- **Package name** (for installation): `python-env-manager`
  ```bash
  pip install python-env-manager
  ```

- **Import name** (in Python code): `env_manager`
  ```python
  import env_manager
  from env_manager import EnvManager
  ```

This is standard Python behavior where hyphens in package names are converted to underscores when importing.

## 🚀 Quick Start

### Simple Command Execution

This example demonstrates the basic workflow for managing a virtual environment and running commands within it.

```python
# Import the package (note the underscore in the import name)
from env_manager import EnvManager

# Create a virtual environment (creates if it doesn't exist)
env = EnvManager("my_project_env")

# Install a package in the isolated environment
env.run("pip", "install", "requests")

# Run Python code using the installed package
env.run("python", "-c", "import requests; print('Requests version:', requests.__version__)")

# Run a script with arguments
env.run("python", "my_script.py", "--arg1", "value1")

# Remove the environment when done
env.remove()
```

### 🛠️ Creating a Custom Environment

Configure your virtual environment with specific options to meet your project requirements.

```python
from env_manager import EnvManager

# Create with default settings
env_manager = EnvManager("path/to/venv")

# For advanced use cases with custom options
from venv import EnvBuilder

# Configure with system packages access and pip
custom_builder = EnvBuilder(system_site_packages=True, with_pip=True)

# Create environment with custom configuration
env_manager = EnvManager("path/to/venv", env_builder=custom_builder)
```

### 📋 Running Commands

Execute various types of commands within your virtual environment with full control over inputs and outputs.

```python
env = EnvManager("path/to/venv")

# Install a package
env.run("pip", "install", "requests")

# List installed packages
env.run("pip", "list")

# Run a script with arguments
env.run("python", "my_script.py", "--arg1", "value1")

# Run inline Python code
env.run("python", "-c", "print('Hello from virtual environment!')")

# Capture command output
result = env.run("python", "--version", capture_output=True)
print(f"Python version: {result.stdout}")

# Run with progress bar visualization
env.run("pip", "install", "large-package", progressBar=True)
```

### 📊 Progress Bar Visualization

For long-running operations, you can enable progress bar visualization to track execution in real-time.

```python
from env_manager import EnvManager

env = EnvManager("path/to/venv")

# Install a package with progress bar
env.run("pip", "install", "tensorflow", progressBar=True)

# Run a long-running script with progress tracking
env.run("python", "train_model.py", "--epochs", "100", progressBar=True)
```

The progress bar automatically detects:
- Percentage indicators (e.g., "50%", "Progress: 75%")
- Count-based progress (e.g., "Downloaded 5 of 10 files", "Step 2/4 completed")
- For commands without identifiable progress indicators, it shows a pulsing progress bar

### 🖥️ Working with Local Python

For cases when you need to use the system Python installation instead of a virtual environment.

```python
# Use the system Python installation
local_env = EnvManager(path=None)

# Run commands with system Python
with local_env:
    local_env.run("python", "-c", "import sys; print(sys.executable)")
```

## 🔌 Environment Activation Guide

### Understanding Environment Activation

Environment activation is a critical concept in Python development that temporarily modifies your shell's environment variables to prioritize a specific Python installation and its packages. When you activate a virtual environment:

- The `PATH` environment variable is modified to prioritize the environment's binaries
- Python-related environment variables are updated to point to the environment
- The Python import system is configured to look for packages in the environment first

This isolation ensures that your project uses exactly the dependencies it needs, regardless of what's installed elsewhere on your system.

### 🔌 Activation Methods

Three different ways to activate and use your virtual environments based on your specific needs.

```python
from env_manager import EnvManager

# Method 1: Explicit activation/deactivation
env = EnvManager(".some_env")

# Activate the environment
env.activate()

# Run commands in the active environment
result = env.run("python", "-c", "import sys; print(sys.executable)")
print(result.stdout)

# Deactivate when finished
env.deactivate()

# Method 2: Context manager (recommended) ✨
with EnvManager(".venv") as venv:
    # Environment automatically activated
    venv.run("pip", "install", "requests")
    venv.run("python", "my_script.py")
    
    if venv.is_active():
        print("Environment is active!")
# Automatically deactivated when exiting

# Method 3: Implicit activation for single commands
EnvManager(".some_env").run("python", "script.py")
```

### 🌟 Best Practices for Environment Activation

1. **Use context managers whenever possible** - They ensure proper cleanup even if exceptions occur
2. **Keep activation scopes as narrow as possible** - Activate only when needed and deactivate promptly
3. **Check environment status before critical operations** - Use `is_active()` to verify the environment state
4. **Consider using the implicit activation for simple operations** - It's cleaner for one-off commands
5. **Be mindful of nested environments** - Activating an environment while another is active can lead to unexpected behavior

### 📋 Activation Cheat Sheet

| Scenario | Recommended Approach |
|----------|---------------------|
| Running multiple commands in sequence | Context manager (`with EnvManager() as env:`) |
| One-off script execution | Implicit activation (`EnvManager().run("python", "script.py")`) |
| Complex workflows with error handling | Context manager with try/except blocks |
| Fine-grained control over activation timing | Explicit activation/deactivation |
| CI/CD pipelines | Context manager for predictable cleanup |

## 🧰 Runner Architecture

The Python Environment Manager uses a flexible runner architecture to execute commands in different contexts. This architecture follows SOLID principles, providing clear separation of concerns and extensibility.

### Available Runners

- **Standard Runner**: Default runner for executing commands in virtual environments
- **Progress Runner**: Executes commands with real-time progress visualization
- **Local Runner**: Executes commands using the local Python installation

### Using Different Runners

The runner system provides a flexible way to execute commands in different contexts. Here's how to use different runners:

```python
from env_manager import EnvManager, RunnerFactory

# Create environment manager
env_manager = EnvManager("path/to/venv")

# Method 1: Using EnvManager's get_runner method (recommended)
standard_runner = env_manager.get_runner("standard")
standard_runner.run("pip", "list")

# Method 2: Using RunnerFactory directly
# Create a runner and configure it with the environment manager
standard_runner = RunnerFactory.create("standard").with_env(env_manager)
standard_runner.run("pip", "list")

# Using a progress runner for long-running operations
progress_runner = RunnerFactory.create("progress").with_env(env_manager)
progress_runner.run("pip", "install", "large-package")

# Using a local runner for system Python operations
local_runner = RunnerFactory.create("local").with_env(env_manager)
local_runner.run("python", "--version")

# Shorthand method using EnvManager's run with progressBar parameter
env_manager.run("pip", "install", "tensorflow", progressBar=True)
```

### Advanced Package Management

The PackageManager class provides a dedicated interface for package operations:

```python
from env_manager import EnvManager, PackageManager, RunnerFactory

# Create environment manager
env_manager = EnvManager("path/to/venv")

# Method 1: Using EnvManager's install_pkg method (recommended)
with env_manager.install_pkg("pytest"):
    env_manager.run("pytest", "--version")

# Method 2: Using PackageManager directly
# Get a standard runner
standard_runner = RunnerFactory.create("standard").with_env(env_manager)

# Create a package manager with the runner
pkg_manager = PackageManager(standard_runner)

# Install a package permanently
pkg_manager.install("requests")

# Check if a package is installed
if pkg_manager.is_installed("numpy"):
    print("NumPy is installed")

# List all installed packages
installed_packages = pkg_manager.list_packages()
print(f"Installed packages: {installed_packages}")

# Install a package temporarily using context manager
with pkg_manager.install_pkg("pytest"):
    # Package is available only within this block
    standard_runner.run("pytest", "--version")
# Package is automatically uninstalled here

# Uninstall a package
pkg_manager.uninstall("requests")
```

### Creating Custom Runners

You can extend the runner system by implementing the `IRunner` interface and registering your custom runner.

```python
from env_manager.runners.irunner import IRunner
from env_manager import RunnerFactory
import subprocess

class MyCustomRunner(IRunner):
    def __init__(self):
        self.env_manager = None
    
    def with_env(self, env_manager):
        self.env_manager = env_manager
        return self
    
    def run(self, *cmd_args, **kwargs):
        # Custom implementation
        print(f"Running command: {' '.join(cmd_args)}")
        # ... custom logic ...
        return subprocess.run(*cmd_args, **kwargs)

# Register your custom runner
RunnerFactory.register("custom", MyCustomRunner)

# Use your custom runner
custom_runner = env_manager.get_runner("custom")
custom_runner.run("python", "script.py")
```

### 📦 Package Management

Efficiently manage packages in your virtual environments with permanent or temporary installations.

```python
with EnvManager("path/to/venv") as env:
    # Install a permanent package
    env.run("pip", "install", "requests")
    
    # Install a temporary package
    with env.install_pkg("beautifulsoup4"):
        # Use the package
        env.run("python", "-c", "import bs4; print(bs4.__version__)")
    # Package is automatically uninstalled here
```

### 🗑️ Environment Removal

Clean up resources by removing environments when they're no longer needed.

```python
# Reference an existing environment
env_manager = EnvManager("path/to/venv")

# Remove the environment
env_manager.remove()

# Pattern for temporary environments
temp_env = EnvManager("temp_env")
try:
    temp_env.run("pip", "install", "requests")
    temp_env.run("python", "script.py")
finally:
    temp_env.remove()  # Always cleaned up
```

## 📚 API Reference

Comprehensive documentation of the classes and methods available in the Python Environment Manager.

### 🔧 EnvManager Class

The main class for creating and managing Python virtual environments.

```python
EnvManager(
    path: Optional[str] = None,  # Environment path
    clear: bool = False,         # Clear if exists
    env_builder: Optional[EnvBuilder] = None,  # Custom builder
    logger: Optional[logging.Logger] = None    # Custom logger
)
```

**Parameters:**
- `path`: Path to the virtual environment. If `None`, uses the current Python environment.
- `clear`: Whether to clear the environment directory if it already exists.
- `env_builder`: Custom EnvBuilder instance for environment creation.
- `logger`: Custom logger for the environment manager.

**Methods:**

| Method | Description | Example |
|--------|-------------|---------|
| `activate()` | Activate the environment | `env.activate()` |
| `deactivate()` | Deactivate the environment | `env.deactivate()` |
| `run(*cmd_args, **kwargs)` | Execute commands in the environment | `env.run("pip", "install", "requests")` |
| `install_pkg(package)` | Install Python package | `env.install_pkg("requests")` |
| `remove()` | Remove the virtual environment | `env.remove()` |
| `is_active()` | Check if environment is active | `if env.is_active(): ...` |
- `run_local(*cmd_args, **kwargs)` | (static): Run a command using the local Python. | `env.run_local("pip", "install", "requests")` |

### 🏗️ Environment Class

Represents a Python environment with information about its structure and properties.

```python
Environment(
    path: Optional[str] = None,  # Environment path
    **kwargs                     # Additional options
)
```

**Attributes:**
- `root`: Root directory of the environment.
- `bin`: Directory containing executables.
- `lib`: Directory containing libraries.
- `python`: Path to the Python executable.
- `name`: Environment name.
- `is_virtual`: Whether the environment is a virtual environment.

### 🏃 Runner Classes

Classes for executing commands in different contexts.

#### IRunner Interface

```python
class IRunner:
    def with_env(self, env_manager): ...
    def run(self, *cmd_args, **kwargs): ...
```

#### RunnerFactory

```python
class RunnerFactory:
    @staticmethod
    def register(name, runner_class): ...
    @staticmethod
    def create(name): ...
    @staticmethod
    def available_runners(): ...
```

### 📦 PackageManager Class

Manages packages in Python environments.

```python
PackageManager(runner: Optional[IRunner] = None)
```

**Methods:**
- `with_runner(runner)`: Configure with a runner.
- `install(package, **options)`: Install a package.
- `uninstall(package, **options)`: Uninstall a package.
- `is_installed(package)`: Check if a package is installed.
- `list_packages()`: List installed packages.
- `install_pkg(package)`: Context manager for temporary installation.

## 🌟 Examples

Practical examples demonstrating how to use Python Environment Manager in various scenarios.

### 📊 Example 1: Data Science Workflow

Create isolated environments for data analysis projects with specific package requirements.

```python
from env_manager import EnvManager

# Create a data science environment
with EnvManager("path/to/data_science_env") as env:
    # Install data science packages with progress bar
    env.run("pip", "install", "numpy", "pandas", "matplotlib", "scikit-learn", progressBar=True)
    
    # Run analysis script
    env.run("python", "analyze_data.py", "--input", "data.csv", "--output", "results.csv")
    
    # Generate visualization
    env.run("python", "-c", """
import matplotlib.pyplot as plt
import pandas as pd

data = pd.read_csv('results.csv')
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

# Define versions to test
versions = ["1.0.0", "1.1.0", "2.0.0"]

for version in versions:
    # Create unique environment name
    env_path = f"test_env_{version.replace('.', '_')}"
    
    # Clean previous environment if exists
    if os.path.exists(env_path):
        shutil.rmtree(env_path)
    
    # Create fresh environment
    with EnvManager(env_path) as env:
        # Install specific version
        env.run("pip", "install", f"package=={version}")
        
        # Run tests
        result = env.run("pytest", "tests/", capture_output=True)
        
        # Show results
        print(f"Test results for version {version}:")
        print(result.stdout)
```

### 🌐 Example 3: Web Development Project

Set up and manage a complete web development environment with database migrations.

```python
from env_manager import EnvManager

# Create web project environment
with EnvManager("web_project_env") as env:
    # Install web framework and dependencies with progress bar
    env.run("pip", "install", "flask", "flask-sqlalchemy", "flask-migrate", progressBar=True)
    
    # Initialize database
    env.run("flask", "db", "init")
    
    # Create migration
    env.run("flask", "db", "migrate", "-m", "Initial migration")
    
    # Apply migration
    env.run("flask", "db", "upgrade")
    
    # Run development server
    env.run("flask", "run", "--debug")
```

### 📊 Example 4: Using Progress Bars for Long Operations

Visualize progress for long-running operations.

```python
from env_manager import EnvManager

# Create environment
env = EnvManager("ml_project_env")

# Install a large machine learning library with progress visualization
env.run("pip", "install", "tensorflow", progressBar=True)

# Train a model with progress visualization
env.run("python", "train_model.py", "--epochs", "100", "--batch-size", "32", progressBar=True)

# Run a data processing pipeline with progress visualization
env.run("python", "process_data.py", "--input", "large_dataset.csv", progressBar=True)
```

### 🧰 Example 5: Advanced Runner Usage

Demonstrate the flexibility of the runner architecture.

```python
from env_manager import EnvManager, RunnerFactory, PackageManager

# Create environment manager
env_manager = EnvManager("path/to/venv")

# Get and use a standard runner
standard_runner = RunnerFactory.create("standard").with_env(env_manager)
standard_runner.run("pip", "list")

# Get and use a progress runner for long operations
progress_runner = RunnerFactory.create("progress").with_env(env_manager)
progress_runner.run("pip", "install", "large-package")

# Get and use a local runner for system Python operations
local_runner = RunnerFactory.create("local").with_env(env_manager)
local_runner.run("python", "--version")

# Use package manager for advanced package operations
pkg_manager = PackageManager(standard_runner)
pkg_manager.install("requests")

# Temporary package installation with context manager
with PackageManager(standard_runner).install_pkg("pytest"):
    standard_runner.run("pytest", "--version")
```

## 📦 Requirements

- **Python**: 3.7+
- **Dependencies**: Rich (for progress bar visualization)
- **Platforms**: Windows, macOS, Linux

---

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
    <a href="https://github.com/r4d4m4n71s/Python-env_manager">GitHub</a> •
    <a href="https://pypi.org/project/python-env-manager/">PyPI</a> •
    <a href="https://github.com/r4d4m4n71s/Python-env_manager/blob/main/README.md">Documentation</a>
  </p>
</div>
