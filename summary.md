<div align="center">

# 🐍 Python Environment Manager

[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)]()
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

</div>

## 🌟 Overview

A comprehensive tool that streamlines the creation and management of Python virtual environments while offering:

- Complete environment lifecycle handling from initialization through decommissioning
- Simplified dependency management via the intuitive install_pkg method
- Secure command execution within isolated environments through the user-friendly run function
- Seamless integration with modern Python development workflows

---

## ✨ Key Features

- 🔄 **Seamless Environment Switching** - Activate/deactivate environments with ease
- 📦 **Package Management** - Install, use, and remove packages effortlessly
- 🛠️ **Command Execution** - Run commands in any environment context
- 📊 **Progress Visualization** - Real-time progress bars for long operations
- 🧰 **Extensible Runner System** - Customize command execution with specialized runners
- 🔌 **Cross-Platform** - Works on Windows, macOS, and Linux

## 📋 Quick Installation

```bash
pip install python-env-manager
```

## 🚀 Quick Start

```python
from env_manager import EnvManager

# Create a virtual environment
env = EnvManager("my_project_env")

# Install a package with progress bar
env.run("pip", "install", "requests", progressBar=True)

# Run Python code using the installed package
env.run("python", "-c", "import requests; print(requests.__version__)")

# Use context manager for automatic activation/deactivation
with EnvManager("another_env") as env:
    env.run("python", "my_script.py")
    
    # Install a temporary package
    with env.install_pkg("pytest"):
        env.run("pytest", "tests/")
```

## 🧰 Advanced Usage: Runner Architecture

```python
from env_manager import EnvManager, RunnerFactory, PackageManager

# Create environment manager
env_manager = EnvManager("path/to/venv")

# Get specialized runners
standard_runner = RunnerFactory.create("standard").with_env(env_manager)
progress_runner = RunnerFactory.create("progress").with_env(env_manager)
local_runner = RunnerFactory.create("local").with_env(env_manager)

# Use package manager for advanced operations
pkg_manager = PackageManager(standard_runner)
pkg_manager.install("requests")

# Temporary package installation
with pkg_manager.install_pkg("pytest"):
    standard_runner.run("pytest", "--version")
```

## 📚 Learn More

For comprehensive documentation, examples, and API reference, see the [full README](README.md).

---

<div align="center">
  <p>Made with ❤️ by the Python Environment Manager team</p>
  <p>
    <a href="https://github.com/r4d4m4n71s/Python-env_manager">GitHub</a> •
    <a href="https://pypi.org/project/python-env-manager/">PyPI</a> •
    <a href="https://github.com/r4d4m4n71s/Python-env_manager/blob/main/README.md">Documentation</a>
  </p>
</div>