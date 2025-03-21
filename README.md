# 🐍 Python Environment Manager

[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)]()
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A comprehensive tool that streamlines the creation and management of Python virtual environments while offering:

- Complete environment lifecycle handling from initialization through decommissioning
- Simplified dependency management via the intuitive install_pkg method
- Secure command execution within isolated environments through the user-friendly run function
- Seamless integration with modern Python development workflows

## ✨ Key Features

- 🔄 **Virtual Environment Management** - Create, activate, and remove environments
- 📦 **Package Management** - Manage dependencies in isolated environments
- 🛠️ **Command Execution** - Run commands with different runner types
- 📊 **Progress Visualization** - Real-time progress bars for long operations
- 🧰 **Extensible Runner System** - Standard, Progress, and Local runners
- 🔌 **Cross-Platform** - Works on Windows, macOS, and Linux

## 🚀 Quick Start

## 📋 Installation

```bash
pip install python-env-manager
```

Note: package name is `python-env-manager` while import name is `env_manager`.

```python
from env_manager import EnvManager

# Create a virtual environment
env = EnvManager("my_project_env")

# Get a standard runner
runner = env.get_runner("standard")

# Install a package
runner.run("pip", "install", "requests")

# Run code with the installed package
runner.run("python", "-c", "import requests; print(requests.__version__)")

# Get a progress runner for visual feedback
progress_runner = env.get_runner("progress")
progress_runner.run("pip", "install", "tensorflow")

# Use context manager for automatic activation/deactivation
with EnvManager("another_env") as env:
    runner = env.get_runner("standard")
    runner.run("python", "my_script.py")
```

## 🧰 Runner Architecture

The core of the Python Environment Manager is its runner architecture, which provides different ways to execute commands.

### Available Runners

- **Standard Runner**: Base runner for command execution
- **Progress Runner**: Shows real-time progress visualization
- **Local Runner**: Uses system Python installation

```python
# Get different types of runners
env = EnvManager("path/to/venv")

standard_runner = env.get_runner("standard")
progress_runner = env.get_runner("progress")
local_runner = env.get_runner("local")

# Customize progress runner with inline output
custom_progress = env.get_runner("progress", inline_output=5)
```

## 📦 Package Management

Manage packages permanently or temporarily:

```python
from env_manager import PackageManager

# Create environment and get runner
env = EnvManager("my_env")
runner = env.get_runner("standard")

# Create package manager
pkg_manager = PackageManager(runner)

# Install permanently
pkg_manager.install("requests")

# Install temporarily with context manager
with pkg_manager.install_pkg("pytest"):
    runner.run("pytest", "tests/")
# Package automatically uninstalled here
```

## 🔌 Environment Activation

Three ways to work with environments:

```python
# 1. Explicit activation/deactivation
env = EnvManager("my_env")
env.activate()
runner = env.get_runner("standard")
runner.run("python", "script.py")
env.deactivate()

# 2. Context manager (recommended)
with EnvManager("my_env") as env:
    runner = env.get_runner("standard")
    runner.run("python", "script.py")

# 3. Automatic activation for each command
env = EnvManager("my_env")
runner = env.get_runner("standard")
runner.run("python", "script.py")  # Auto-activates for this command
```

## 🌟 Example: Data Science Workflow

```python
from env_manager import EnvManager

# Create environment for data science
with EnvManager("data_science_env") as env:
    # Get runners
    std = env.get_runner("standard")
    prog = env.get_runner("progress")
    
    # Install packages with progress
    prog.run("pip", "install", "numpy", "pandas", "matplotlib", "scikit-learn")
    
    # Run analysis
    std.run("python", "analyze_data.py", "--input", "data.csv", "--output", "results.csv")
```

## 📚 API Reference

### 🔧 EnvManager

Primary class for managing environments.

```python
EnvManager(
    path: Optional[str] = None,  # Environment path (None uses system Python)
    clear: bool = False,         # Clear existing environment
    env_builder: Optional[EnvBuilder] = None,  # Custom venv builder
    logger: Optional[logging.Logger] = None    # Custom logger
)
```

**Key Methods:**
- `activate()`: Activate the environment
- `deactivate()`: Deactivate the environment
- `get_runner(runner_type, **kwargs)`: Get a runner of specified type
- `remove()`: Remove the environment
- `is_active()`: Check if environment is active

### 🏃 Runners

- `RunnerFactory`: Creates runner instances
  - `create(name, **kwargs)`: Create a runner
  - `register(name, runner_class)`: Register a custom runner
  
- `IRunner`: Base interface implemented by all runners
  - `with_env(env_manager)`: Configure with an environment manager
  - `run(*cmd_args, **kwargs)`: Execute a command

### 📦 PackageManager

Manages packages in virtual environments.

- `install(package, **options)`: Install a package
- `uninstall(package, **options)`: Uninstall a package
- `is_installed(package)`: Check if a package is installed
- `list_packages()`: List all installed packages
- `install_pkg(package)`: Context manager for temporary installation

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

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<div align="center">
  <p>Made with ❤️ by the Python Environment Manager team</p>
  <p>
    <a href="https://github.com/r4d4m4n71s/Python-env_manager">GitHub</a> •
    <a href="https://pypi.org/project/python-env-manager/">PyPI</a>
  </p>
</div>
