# 🐍 Python Environment Manager

A powerful, cross-platform tool for managing Python environments with ease. Seamlessly handle both virtual and local Python environments with a clean, intuitive API.

## ✨ Features

- 🔄 **Cross-Platform Compatibility**: Works on Windows, macOS, and Linux
- 🎯 **Smart Environment Detection**: Automatically handles both virtual and local Python environments
- 🛠️ **Flexible Command Execution**: Run any Python command, script, or package management operation
- 🔒 **Context Manager Support**: Safe environment handling with `with` statements
- 📦 **Package Management**: Easy package installation with temporary or permanent options
- 🔍 **Environment Variable Control**: Proper handling of Python paths and environment variables

## 🚀 Quick Start

### Installation

```python
import EnvManager
```

### Basic Usage

```python
# Create and manage a virtual environment
env = EnvManager("path/to/venv")
# The environment is created automatically if it doesn't exist
```

### Using Context Manager (Recommended)

```python
# Automatically handles activation and deactivation
with EnvManager("path/to/venv") as env:
    env.run("pip", "install", "requests")
    env.run("python", "your_script.py")
```

## 📚 API Reference

### `EnvManager`

#### Constructor

```python
env = EnvManager(
    path=None,           # Optional: Path to Python environment
    clear=False,         # Optional: Clear environment if it exists
    env_builder=None,    # Optional: Custom EnvBuilder configuration
    logger=None          # Optional: Custom logger
)
```

#### Core Methods

| Method | Description | Example |
|--------|-------------|---------|
| `activate()` | Activate the environment | `env.activate()` |
| `deactivate()` | Deactivate the environment | `env.deactivate()` |
| `run()` | Execute commands in the environment | `env.run("pip", "install", "requests")` |
| `install_pkg()` | Install Python package | `env.install_pkg("requests")` |
| `remove()` | Remove the virtual environment | `env.remove()` |
| `is_active()` | Check if environment is active | `if env.is_active(): ...` |

### Command Execution Examples

```python
# Package Management
with EnvManager() as env:
    # Install packages
    env.run("pip", "install", "requests")
    
    # Run tests
    env.run("pytest", "tests/")
    
    # Execute Python scripts
    env.run("python", "script.py", "--arg1", "value1")
    
    # Install a package temporarily (will be uninstalled when exiting the context)
    with env.install_pkg("requests") as pkg_ctx:
        # Use the package within this block
        env.run("python", "-c", "import requests; print(requests.__version__)")
```

## 🎯 Use Cases

### 1. Package Development

```python
with EnvManager("dev_env") as env:
    # Install development dependencies
    env.run("pip", "install", "-r", "requirements-dev.txt")
    
    # Run tests
    env.run("pytest", "--cov=your_package")
    
    # Build package
    env.run("python", "setup.py", "build")
```

### 2. Script Execution

```python
with EnvManager() as env:
    # Install required packages
    env.run("pip", "install", "pandas", "matplotlib")
    
    # Run data processing script
    env.run("python", "process_data.py")
```

### 3. Environment Management

```python
# Create a new environment (happens automatically in constructor)
env = EnvManager("new_env")

# Use the environment
with env:
    env.run("pip", "list")  # List installed packages
```

## 🔧 Advanced Usage

### Custom Environment Builder

```python
from venv import EnvBuilder

builder = EnvBuilder(
    system_site_packages=True,
    clear=True,
    with_pip=True,
    upgrade_deps=True
)

env = EnvManager("custom_env", env_builder=builder)
```

### Custom Logging

```python
import logging

logger = logging.getLogger("custom_logger")
logger.setLevel(logging.DEBUG)

env = EnvManager("env_path", logger=logger)
```

## 🚨 Best Practices

1. **Always Use Context Managers**
   ```python
   # Good
   with EnvManager() as env:
       env.run("pip", "install", "requests")
   
   # Avoid
   env = EnvManager()
   env.activate()
   try:
       env.run("pip", "install", "requests")
   finally:
       env.deactivate()
   ```

2. **Handle Paths Properly**
   ```python
   from pathlib import Path
   
   env_path = Path("environments/project_env")
   env = EnvManager(env_path)
   ```

3. **Use Explicit Commands**
   ```python
   # Good
   env.run("python", "-m", "pip", "install", "requests")
   
   # Avoid
   env.run("pip install requests")  # String splitting is less reliable
   ```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Python's `venv` module for providing the foundation
- The Python community for inspiration and best practices

---

Made with ❤️ by the Python Utils Team