# Progress Bar Functionality

The `EnvManagerWithProgress` class extends the standard `EnvManager` with the ability to display a progress bar when running commands. This feature provides visual feedback during long-running operations, making it easier to track the progress of command execution.

## Features

- Real-time progress bar display using the Rich library
- Automatic progress estimation based on command output
- Support for both percentage-based and count-based progress indicators
- Customizable terminal width usage (40% of available width)
- Compatible with all commands supported by the standard `EnvManager`

## Installation

The progress bar functionality requires the Rich library. It's included as a dependency in the package, but you can also install it manually:

```bash
pip install rich
```

## Usage

### Basic Usage

To use the progress bar functionality, simply use the `EnvManagerWithProgress` class instead of the standard `EnvManager` and set the `progressBar` parameter to `True` when calling the `run` method:

```python
from env_manager import EnvManagerWithProgress

# Create an environment manager with progress bar support
env_manager = EnvManagerWithProgress("/path/to/env")

# Run a command with progress bar
result = env_manager.run("pip", "install", "package_name", progressBar=True)
```

### Progress Estimation

The progress bar automatically tries to estimate progress based on the command output:

1. **Percentage-based progress**: Detects patterns like "50%" or "Progress: 75%"
2. **Count-based progress**: Detects patterns like "Downloaded 5 of 10 files" or "Step 2/4 completed"
3. **Indeterminate progress**: For commands without identifiable progress indicators, it shows a pulsing progress bar

### Example

```python
from env_manager import EnvManagerWithProgress

# Create an environment manager with progress bar support
env_manager = EnvManagerWithProgress("/path/to/env")

# Install a package with progress bar
env_manager.run("pip", "install", "requests", progressBar=True)

# Run a Python script with progress bar
env_manager.run("python", "my_script.py", progressBar=True)

# Execute a command without progress bar
env_manager.run("pip", "list", progressBar=False)  # Same as standard EnvManager
```

## Implementation Details

The progress bar functionality is implemented using two main components:

1. **ProgressRunner**: A utility class that handles the actual progress bar display and command execution
2. **EnvManagerWithProgress**: A subclass of `EnvManager` that delegates to `ProgressRunner` when the progress bar is enabled

The implementation uses lazy loading to avoid importing the Rich library until it's actually needed, minimizing the impact on performance when the progress bar is not used.