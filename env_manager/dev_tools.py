import os
import logging
import shutil
import subprocess
import sys
import importlib
import atexit
from enum import Enum, auto
from pathlib import Path
from typing import Literal, Optional
from program_state import GlobalState
from env_manager import EnvManager, Environment
import questionary

DISTRIBUTION_PATH = "distribution"
VENV = ".venv"
APP_PATH = Path.cwd()
globalState= GlobalState(APP_PATH) 

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class _EnvManager(EnvManager):
    _instance = None    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(EnvManager, cls).__new__(cls)
        return cls._instance

class Setup:

    def __init__(self, application_path):
        self.application_path:Path = Path(application_path)
        self.dist_dir = self.application_path.joinpath(DISTRIBUTION_PATH)

    def get_env_manager(self)->EnvManager:

        if globalState.get("loaded"):
            return _EnvManager(globalState.get("env_path"))

        try:                        
            
            manager = None
            logger.info("\nSetting up environment...")            
            action = Setup._ask_for_env(globalState.get("env_path"))
            
            if action == 'keep':
                logger.info("Using existing virtual environment")
                manager = EnvManager(self.application_path)
            elif action in ('recreate', 'new'):
                logger.info("Creating fresh virtual environment")
                manager = EnvManager(self.application_path / VENV, clear=True)
            elif action == 'local':
                logger.info("Using local Python installation")
                manager = EnvManager(None)
            else:
                raise DevToolsError(f"Invalid action: {action}")
            
            if not manager:
                raise DevToolsError("Failed to initialize environment manager")
            
            logger.info("✅ Environment setup complete")            
            
            # store selected environment path to the state
            globalState["env_path"] = manager.env.root
            globalState["loaded"] = True
            globalState.save()

            return manager
        
        except ImportError as e:
            raise DevToolsError(f"Failed to import required package: {e}") from e
        except Exception as e:
            raise DevToolsError(f"Environment setup failed: {e}") from e

    @staticmethod
    def _ask_for_env(env_path: str) -> str:
        """
        Setup the Python environment with interactive prompts.
        
        This method guides the user through environment setup with clear options:
        - For existing environments: Options to reuse, recreate, or switch to local
        - For new setups: Options to create virtual env or use local Python
        
        The choices are presented via questionary after ensuring it's installed.
        """                                
        prompt = "Python environment setup"        
        if env_path and not Environment.is_local(env_path):
            logger.info(f"\nFound existing environment: {env_path}")
            
            # For existing environment
            action = questionary.select(
                prompt,
                choices=[
                    questionary.Choice(f"✓ Keep existing environment {os.path.basename(env_path)} (recommended)", "keep"),
                    questionary.Choice("♻ Recreate environment from scratch", "recreate"),
                    questionary.Choice("🌐 Switch to local Python installation", "local")
                ],
                default="keep"
            ).ask()
        else:
            # For new setup
            action = questionary.select(
                prompt,
                choices=[
                    questionary.Choice("🆕 Create new virtual environment (recommended)", "new"),
                    questionary.Choice("🌐 Use local Python installation", "local")
                ],
                default="new"
            ).ask()
    
        if action is None:
            raise DevToolsError("Environment setup cancelled by user")
        
        return action

class DevToolsError(Exception):
    """Base exception for DevTools errors."""
    pass

class PackageNotInstalledError(DevToolsError):
    """Raised when required package is not installed."""
    pass

class ReleaseError(DevToolsError):
    """Raised when there's an error creating or deploying a release."""
    pass

class ReleaseType(Enum):
    """Types of releases supported."""
    BETA = auto()
    PROD = auto()

class DeployTarget(Enum):
    """Deployment targets supported."""
    TEST = auto()
    PROD = auto()

class DevTools:
    """Development tools for managing the project lifecycle."""
    
    def __init__(self, project_root: str):
        
        """Initialize DevTools with project root path."""
        self.setup = Setup(project_root)

    # Public Methods
    def install(self):
        """
        Intall the application in development mode.
        
        Args:
            recreate: Optional flag to force recreation of virtual environment
        """
        env_manager = self.setup.get_env_manager()      
        logger.info("Installing project dependencies...")
        env_manager.run("python", "-m", "pip", "install", "-e", ".[dev]",capture_output=False) 
        return self

    def test(self):
        """Run the project test suite."""
        env_manager = self.setup.get_env_manager()
        logger.info("Running tests...")
                        
        action = questionary.select(
            "\nRun select:",
            choices=[
                questionary.Choice('All tests', '--ff'),
                questionary.Choice('Only failed', '--lf'),
                questionary.Choice('Test just single', '-k test_version')
            ],
            default='-k test_version'
        ).ask()
        
        if action is None:
            raise DevToolsError("Test execution cancelled")
        
        env_manager.run("pytest", action, "--tb=short", "-v", capture_output=False)
        return self

    def hooks(self, action: Literal["on", "off"]):
        """
        Enable or disable pre-commit hooks.
        
        Args:
            action: "on" to enable hooks, "off" to disable
        """
        env_manager = self.setup.get_env_manager()
        
        if action == "on":
            logger.info("Enabling pre-commit hooks...")
            env_manager.run("pre-commit install")
        else:
            logger.info("Disabling pre-commit hooks...")
            env_manager.run("pre-commit uninstall")
        return self

    def release(self, release_type: Literal["beta", "prod"]):
        """
        Create a new release.
        
        Args:
            release_type: Type of release to create ("beta" or "prod")
        """
        env_manager = self.setup.get_env_manager()
        release_enum = ReleaseType[release_type.upper()]
        
        logger.info(f"Creating {release_type} release...")
        
        # Install required packages using the new method
        self._install_if_needed("build")
        self._install_if_needed("bump2version")
        
        # Configure git
        self._configure_git_for_release()
        
        # Version management
        if release_enum == ReleaseType.PROD:
            env_manager.run(
                "bump2version", "patch", "--config-file", ".bumpversion.cfg"
            )
        else:
            current_version = self._get_current_version()
            env_manager.run([
                "bump2version",
                "patch",
                "--config-file",
                ".bumpversion.cfg",
                "--new-version",
                f"{current_version}.beta",
            ])
        
        # Build package
        env_manager.run("python", "-m", "build")
        
        # Move artifacts
        release_dir = self._prepare_release_directory(release_enum)
        for artifact in (self.setup.application_path / "dist").glob("*"):
            shutil.move(str(artifact), str(release_dir / artifact.name))
        
        logger.info(
            f"✅ {'Production' if release_enum == ReleaseType.PROD else 'Beta'} "
            f"release created in {release_dir}/"
        )
        return self

    def deploy(self, target: Literal["test", "prod"]):
        """
        Deploy the package to PyPI.
        
        Args:
            target: Deployment target ("test" or "prod")
        """
        env_manager = Setup.get_env_manager()
        deploy_target = DeployTarget[target.upper()]
        
        logger.info(f"Deploying to {target} PyPI...")
        self._install_if_needed("twine")
        
        if deploy_target == DeployTarget.PROD:
            release_dir = self.config.dist_dir / "release"
            if not release_dir.exists():
                raise ReleaseError(
                    "No production release found. Create one first with 'release prod'"
                )
            logger.info("📦 Deploying production release to PyPI...")
            self.env_manager.run("twine", "upload", str(release_dir / "*"))
            logger.info("✅ Deployed to PyPI - https://pypi.org/project/venv-py/")
        else:
            beta_dir = self.setup.dist_dir / "beta"
            if not beta_dir.exists():
                raise ReleaseError(
                    "No beta release found. Create one first with 'release beta'"
                )
            logger.info("📦 Deploying beta release to TestPyPI...")
            env_manager.run([
                "twine", "upload", "--repository", "testpypi", str(beta_dir / "*")
            ])
            logger.info("✅ Deployed to TestPyPI - https://test.pypi.org/project/venv-py/")

    # Private Methods
    def _install_if_needed(self, package_name: str, version: Optional[str] = None) -> bool:
        """
        Install a Python package if it's not already installed.
        
        Args:
            package_name (str): Name of the package to install
            version (Optional[str]): Specific version to install (e.g., '1.0.0')
            
        Returns:
            bool: True if package was installed, False if it was already installed
            
        Raises:
            DevToolsError: If environment manager is not initialized
        """
        env_manager = Setup.get_env_manager()

        try:
            # Try to import the package
            
            importlib.import_module(package_name)
            logger.debug(f"Package {package_name} is already installed")
            return False
        except ImportError:
            # Package not found, install it
            install_spec = f"{package_name}=={version}" if version else package_name
            logger.info(f"Installing {install_spec}")
            env_manager.install_pkg(install_spec)
            return True
                    
    def _configure_git_for_release(self) -> None:
        """Configure git settings for release."""
        env_manager = Setup.get_env_manager()
        env_manager.run("git", "config", "--local", "user.email", "local-release@noreply.local")
        env_manager.run("git", "config", "--local", "user.name", "Local Release Script")

    def _get_current_version(self) -> str:
        """Get current package version."""
        env_manager = Setup.get_env_manager()
        version_result = env_manager.run("bump2version", "--dry-run", "patch", "--list")
        
        for line in version_result.stdout.splitlines():
            if "current_version" in line:
                return line.split("=")[1].strip()
        
        raise ReleaseError("Could not determine current version")

    def _prepare_release_directory(self, release_type: ReleaseType) -> Path:
        """Prepare release directory and return its path."""
        release_dir = self.setup.dist_dir / (
            "release" if release_type == ReleaseType.PROD else "beta"
        )
        release_dir.mkdir(parents=True, exist_ok=True)
        return release_dir

def _get_command_help(command: Optional[str] = None) -> str:
    """
    Get help text for a command from the markdown documentation.
    
    Args:
        command: Optional command name to get help for
        
    Returns:
        str: Help text for the command or general help if no command specified
    """
    try:
        with open("dev_tools.md", "r") as f:
            content = f.read()
            
        if command is None:
            # Return the basic usage and commands list
            return (
                "Usage: python -m dev_tools <command> [args]\n\n"
                "Commands:\n"
                "  install         - Install the application in dev mode\n"
                "  test            - Run the test suite\n"
                "  prehook-on      - Enable pre-commit hooks\n"
                "  prehook-off     - Disable pre-commit hooks\n"
                "  release <type>  - Create a release (beta|prod)\n"
                "  deploy <target> - Deploy to PyPI (test|prod)\n"
                "  help [command]  - Show this help message or detailed help for a specific command\n\n"
            )
            
        # Map command names to their section titles in the markdown
        command_sections = {
            "install": "Install Command",
            "test": "Test Command",
            "prehook-on": "Pre-commit Hooks Enable Command",
            "prehook-off": "Pre-commit Hooks Disable Command",
            "release": "Release Command",
            "deploy": "Deploy Command"
        }
        
        if command not in command_sections:
            return f"Error: Unknown command '{command}'"
            
        # Find the section for this command
        section_title = command_sections[command]
        start = content.find(f"## {section_title}")
        if start == -1:
            return f"Error: Documentation not found for command '{command}'"
            
        # Find the next section or end of file
        next_section = content.find("\n## ", start + 1)
        if next_section == -1:
            section_content = content[start:]
        else:
            section_content = content[start:next_section]
            
        return section_content.strip()
        
    except FileNotFoundError:
        return "Error: Documentation file not found"
    except Exception as e:
        return f"Error reading documentation: {str(e)}"

def show_help(command: Optional[str] = None) -> None:
    """
    Show detailed help for commands.
    
    Args:
        command: Optional specific command to show help for
    """
    print(_get_command_help(command))

def handle_command(tools: Optional[DevTools], command: str, args: list[str]) -> None:
    """
    Handle the execution of a specific command.
    
    Args:
        tools: DevTools instance (None only allowed for help command)
        command: Command to execute
        args: Additional command arguments
    
    Raises:
        DevToolsError: If command validation fails
    """
    command_handlers = {
        "install": lambda: tools.install(),
        "test": lambda: tools.test(),
        "prehook-on": lambda: tools.hooks("on"),
        "prehook-off": lambda: tools.hooks("off"),
        "release": lambda: _handle_release(tools, args),
        "deploy": lambda: _handle_deploy(tools, args),
        "help": lambda: show_help(args[0] if args else None)
    }
    
    handler = command_handlers.get(command)
    if not handler:
        raise DevToolsError(f"Unknown command: {command}")
    
    handler()

def _handle_release(tools: DevTools, args: list[str]) -> None:
    """Handle release command validation and execution."""
    if not args or args[0] not in ("beta", "prod"):
        raise DevToolsError("Please specify release type (beta or prod)")
    tools.release(args[0])

def _handle_deploy(tools: DevTools, args: list[str]) -> None:
    """Handle deploy command validation and execution."""
    if not args or args[0] not in ("test", "prod"):
        raise DevToolsError("Please specify deployment target (test or prod)")
    tools.deploy(args[0])

class ExitStatus:
    """Keep track of program exit status and error information."""
    def __init__(self):
        self.exit_code: int = 0
        self.error_message: Optional[str] = None
        self.exception: Optional[Exception] = None

# Create a global exit status tracker
exit_status = ExitStatus()

def exit_handler(state: GlobalState) -> None:
    """
    Handle program exit and cleanup state if error occurred.
    
    This handler is called on program exit and will:
    1. Check for any unhandled exceptions
    2. Reset program state if an error occurred
    3. Log appropriate exit message
    
    Args:
        state: Global state instance to manage
    """
    # Check if we're exiting due to an error
    error = exit_status.exit_code if exit_status.exit_code != 0 else None

    print(f"exit error code {error}")    
    if error == 2:
        logger.info("Cleaning up due to error condition...")
        try:
            state.reset()
            logger.info("State reset successfully")
        except Exception as e:
            logger.error(f"Failed to reset state: {e}")
    elif error == 0:
        logger.info("Exiting successfully")

def choose_virtual_env():
    while True:
        response = input("Do you want to perform the installation in a virtual .venv environment? (yes/no): ").strip().lower()
        if response in ("yes", "y"):
            return True
        elif response in ("no", "n"):
            return False
        else:
            print("Please choose 'yes' or 'no'.")

def main() -> None:
    """CLI entry point."""
    try:
        if len(sys.argv) < 2:
            show_help()
            sys.exit(1)

        command = sys.argv[1]
        args = sys.argv[2:]

        if command == "help":
            handle_command(None, command, args)
            sys.exit(0)
        
        tools = DevTools(APP_PATH)
        atexit.register(exit_handler, globalState)
        handle_command(tools, command, args)

    except DevToolsError as e:
        exit_status.exit_code = 1
        exit_status.error_message = str(e)
        exit_status.exception = e
        logger.error(str(e))
        sys.exit(2)
    except KeyboardInterrupt as e:
        exit_status.exit_code = 1
        exit_status.error_message = f"Operation cancelled by user: {e}"
        exit_status.exception = e
        logger.info("\nOperation cancelled by user")
        sys.exit(2)
    except subprocess.CalledProcessError as e:
        exit_status.exit_code = e.returncode
        exit_status.error_message = f"Command execution failed: {e}"
        exit_status.exception = e
        logger.error(f"Command execution failed: {e}")
        sys.exit(1)
    except Exception as e:
        exit_status.exit_code = 1
        exit_status.error_message = f"Unexpected error: {e}"
        exit_status.exception = e
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
    