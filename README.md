# 🐍 Virtual Environment Manager

[![Python Versions](https://img.shields.io/badge/python-3.8%20%7C%203.9%20%7C%203.10%20%7C%203.11%20%7C%203.12-blue.svg)](https://pypi.org/project/virtual-env-manager/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)]()
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## 🌟 Elevate Your Python Development Workflow

`venv_py` virtual environment lifecycle manager.

---

### ✨ Key Features

- 🚀 **Effortless Environment Management**
  - Create and run commands in virtual environments on the fly
  - Cross-platform support (Windows and Unix-like systems)

- 🔍 **Smart Consistency Checking**
  - Validate environment configurations
  - Ensure package and file integrity

- 🛡️ **Robust Error Handling**
  - Detailed logging
  - Comprehensive error messages

- 🔧 **Flexible Command Execution**
  - Run commands directly within virtual environments
  - Retrieve and inspect command results

---
### Usage

```python
from venv_py import EnvManager

# Installing libraries
EnvManager(".some_env").run("pip", "install", "requests", "pandas").result()

# Reset the state, flushing libraries
EnvManager(".some_env").flush().run("python script.py").result()

```

### Context Manager Usage

```python
with EnvManager(".venv") as venv:
    # Automatic environment lifecycle management
    venv.run("python", "my_script.py").result()
```

## 🔌 Environment Activation Guide

### Understanding Environment Activation

Environment activation is a critical concept in Python development that temporarily modifies your shell's environment variables to prioritize a specific Python installation and its packages. When you activate a virtual environment:

- The `PATH` environment variable is modified to prioritize the environment's binaries
- Python-related environment variables are updated to point to the environment
- The Python import system is configured to look for packages in the environment first

This isolation ensures that your project uses exactly the dependencies it needs, regardless of what's installed elsewhere on your system.

### 🛠️ Activation Methods

#### Method 1: Explicit Activation/Deactivation

```python
from venv_py import EnvManager

# Create or connect to an existing environment
env = EnvManager(".some_env")

# ✅ ACTIVATE: Set up environment variables and Python paths
env.activate()

# 🔍 What happens during activation:
# - PATH environment variable is updated to prioritize the environment's bin directory
# - VIRTUAL_ENV environment variable is set to point to the environment root
# - Python's sys.path is modified to include the environment's site-packages
# - The environment becomes the active Python context for all operations

# 💻 Now you can work within the isolated environment:
env.run("pip", "install", "requests")  # Install packages isolated to this environment
env.run("python", "-c", "import requests; print(requests.__version__)")  # Use the installed package
env.run("pytest", "tests/")  # Run tools installed in the environment

# ⚠️ Without activation, these commands would use the system Python!

# ❌ DEACTIVATE: Restore original environment state when finished
env.deactivate()

# 🔍 What happens during deactivation:
# - All environment variables are restored to their original state
# - Python's sys.path is restored to its original configuration
# - The system returns to using the default Python installation
```

#### Method 2: Context Manager (Recommended Approach)

```python
from venv_py import EnvManager

# 🔄 Automatic activation/deactivation with context manager
with EnvManager(".venv") as venv:
    # ✅ Environment is automatically activated when entering this block
    
    # 🛠️ All operations inside this block use the virtual environment
    venv.run("pip", "install", "requests")
    venv.run("python", "my_script.py")
    
    # 🔍 Verify environment status
    if venv.is_active():
        print("Environment is active and ready to use!")
        
    # 📊 You can even run multiple commands in sequence
    venv.run("pip", "install", "pandas")
    venv.run("python", "-c", "import pandas as pd; print(pd.__version__)")
    
    # 🧪 Or execute test suites in isolation
    venv.run("pytest", "--cov=your_package")
    
    # ⚡ Any exceptions are properly handled, and cleanup still occurs
    
# ❌ Environment is automatically deactivated when exiting the context
# Even if exceptions occur, deactivation is guaranteed
```

#### Method 3: Implicit Single-Command Activation

```python
from venv_py import EnvManager

# 🚀 Run a single command in the environment without explicit activation
# Perfect for one-off script execution or quick package operations
EnvManager(".some_env").run("python", "script.py")

# 📦 Install a package with a single line
EnvManager(".some_env").run("pip", "install", "requests")

# 🔍 Check installed packages
result = EnvManager(".some_env").run("pip", "list", capture_output=True)
print(result.stdout)

# ⚙️ The environment is automatically used just for these commands
# No explicit activation/deactivation needed
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

## 📦 Requirements

- **Python**: 3.8+
- **Platforms**: Windows, macOS, Linux

---

## 🤝 Contributing

1. 🍴 Fork the repository
2. 🌿 Create a feature branch
3. 🔨 Make your changes
4. ✅ Run tests
5. 📤 Submit a pull request

---

## 📄 License

[MIT License](LICENSE) - Free to use, modify, and distribute

---

## 🌈 Powered By

- Pure Python
- Standard Library
- Community Love ❤️
