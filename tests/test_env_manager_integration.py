"""
Integration tests for the EnvManager class.
Tests complete workflows and component interactions with the actual system.
"""

import os
import sys
import shutil
import subprocess
import logging
import pytest
import time
from pathlib import Path
from env_manager import EnvManager, Environment, InstallPkgContextManager, PythonLocal

class TestEnvManagerIntegration:
    """Integration tests for EnvManager testing complete workflows."""
    
    @pytest.fixture
    def test_logger(self):
        """Create a logger for testing."""
        logger = logging.getLogger("test_env_manager")
        logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler()
        handler.setLevel(logging.DEBUG)
        logger.addHandler(handler)
        return logger
    
    @pytest.fixture
    def temp_env_path(self, tmp_path, test_logger):
        """Create a temporary directory for virtual environment."""
        env_path = tmp_path / ".test_venv"
        env_path.mkdir(exist_ok=True)
        return env_path
    
    @pytest.fixture
    def env_manager(self, temp_env_path, test_logger):
        """Create EnvManager instance with temporary path."""
        return EnvManager(path=str(temp_env_path), logger=test_logger)
    
    def test_basic_environment_lifecycle(self, env_manager):
        """Test basic environment lifecycle: create, activate, deactivate, remove."""
        # Verify environment was created
        assert env_manager.env.is_virtual
        assert os.path.exists(env_manager.env.root)
        
        # Test activation
        env_manager.activate()
        assert env_manager.is_active()
        assert "VIRTUAL_ENV" in os.environ
        assert os.path.abspath(os.environ["VIRTUAL_ENV"]) == os.path.abspath(env_manager.env.root)
        
        # Test deactivation
        env_manager.deactivate()
        assert not env_manager.is_active()
        assert "VIRTUAL_ENV" not in os.environ
        
        # Test removal
        env_manager.remove()
        assert not os.path.exists(env_manager.env.root)
    
    def test_context_manager(self, env_manager):
        """Test basic context manager behavior."""
        # Store original environment state
        original_environ = dict(os.environ)
        
        # Use context manager
        with env_manager as env:
            # Verify activation
            assert env.is_active()
            assert "VIRTUAL_ENV" in os.environ
            assert os.path.abspath(os.environ["VIRTUAL_ENV"]) == os.path.abspath(env_manager.env.root)
        
        # Verify deactivation after context exit
        assert not env_manager.is_active()
        assert "VIRTUAL_ENV" not in os.environ
    
    def test_package_installation(self, env_manager):
        """Test basic package installation."""
        with env_manager:
            # Install a package
            env_manager.run("pip", "install", "setuptools", capture_output=True)
            
            # Verify installation via pip list
            result = env_manager.run("pip", "list", capture_output=True)
            assert "setuptools" in result.stdout
    
    def test_install_pkg_context_manager(self, env_manager):
        """Test the install_pkg context manager."""
        with env_manager:
            # Use the context manager to install a package
            with env_manager.install_pkg("wheel"):
                # Verify package is installed
                result = env_manager.run("pip", "list", capture_output=True)
                assert "wheel" in result.stdout
            
            # After context exit, package should be uninstalled
            result = env_manager.run("pip", "list", capture_output=True)
            assert "wheel" not in result.stdout
    
    def test_script_execution(self, env_manager, tmp_path):
        """Test executing Python scripts in the environment."""
        # Create a test script
        script_path = tmp_path / "test_script.py"
        script_content = '''
import sys
import os
print("Python path:", sys.executable)
print("Virtual env:", os.environ.get('VIRTUAL_ENV', 'None'))
'''
        script_path.write_text(script_content)
        
        with env_manager:
            # Execute the script
            result = env_manager.run("python", str(script_path), capture_output=True)
            
            # Verify environment is correctly used
            env_root = os.path.abspath(env_manager.env.root)
            # Normalize path separators for cross-platform comparison
            normalized_stdout = result.stdout.replace('\\', '/')
            normalized_env_root = env_root.replace('\\', '/')
            assert normalized_env_root in normalized_stdout
            
            # Test different run options
            result = env_manager.run("python", "--version", capture_output=True)
            assert "Python" in result.stdout
            
            # Test with check=False
            result = env_manager.run(
                "python", "-c", "import sys; sys.exit(1)",
                capture_output=True, check=False
            )
            assert result.returncode == 1
            
            # Test with text=False
            result = env_manager.run(
                "python", "-c", "print('hello')",
                capture_output=True, text=False
            )
            assert isinstance(result.stdout, bytes)        
    
    def test_error_handling(self, env_manager):
        """Test error handling in various scenarios."""
        with env_manager:
            # Test invalid package installation
            with pytest.raises(subprocess.CalledProcessError):
                env_manager.run("pip", "install", "nonexistent_package_name_12345")
            
            # Test command execution failure
            with pytest.raises(subprocess.CalledProcessError):
                env_manager.run("python", "-c", "raise Exception('test error')")
    
    def test_multiple_environments(self, tmp_path, test_logger):
        """Test managing multiple environments simultaneously."""
        # Create two separate environments
        env1_path = tmp_path / "env1"
        env2_path = tmp_path / "env2"
        env1_path.mkdir(exist_ok=True)
        env2_path.mkdir(exist_ok=True)
                
        env1 = EnvManager(path=str(env1_path), logger=test_logger)
        env2 = EnvManager(path=str(env2_path), logger=test_logger)
        
        # Install different packages in each environment
        with env1:
            env1.run("pip", "install", "setuptools", capture_output=True)
        
        with env2:
            env2.run("pip", "install", "wheel", capture_output=True)
        
        # Verify environments remain separate
        with env1:
            result = env1.run("pip", "list", capture_output=True)
            assert "setuptools" in result.stdout
            assert "wheel" not in result.stdout
        
        with env2:
            result = env2.run("pip", "list", capture_output=True)
            assert "wheel" in result.stdout
            assert "setuptools" not in result.stdout   
    
    def test_environment_variables(self, env_manager):
        """Test environment variables preservation and restoration."""
        # Set a custom environment variable
        os.environ["TEST_VAR"] = "test_value"
        original_environ = dict(os.environ)
        
        try:
            with env_manager:
                # Variable should be preserved in virtual environment
                assert os.environ["TEST_VAR"] == "test_value"
                
                # Add a new variable
                os.environ["VENV_VAR"] = "venv_value"
            
            # Original environment should be restored
            assert os.environ == original_environ
            assert "VENV_VAR" not in os.environ
            assert os.environ["TEST_VAR"] == "test_value"
        finally:
            # Cleanup
            if "TEST_VAR" in os.environ:
                del os.environ["TEST_VAR"]
    
    def test_venv_to_venv_creation(self, test_logger):
    
        """Test working with venv to venv."""
        #use base pibot env
        EnvManager(".test_env").activate()
                
        local_env = EnvManager(path=None, clear=True, logger=test_logger)  # Uses system Python
        original_environ = dict(os.environ)
        
        with local_env:
            # Should work with local Python
            result = local_env.run(
                "python",
                "-c",
                "import sys; print('test')",
                capture_output=True
            )
            assert "test" in result.stdout.strip()
        
            # Verify environment restored
            assert os.environ == original_environ
    
    def test_environment_class(self, tmp_path):
        """Test Environment class integration with EnvManager."""
        # Create environment directly
        env = Environment(path=str(tmp_path))
        
        # Verify properties
        assert env.root == os.path.abspath(str(tmp_path))
        assert env.name == os.path.basename(str(tmp_path))
        assert env.bin == os.path.join(os.path.abspath(str(tmp_path)),
                                      "Scripts" if os.name == "nt" else "bin")
        assert env.lib == os.path.join(os.path.abspath(str(tmp_path)),
                                      "Lib" if os.name == "nt" else "lib")
        
        # Use with EnvManager
        manager = EnvManager(path=str(tmp_path))
        assert manager.env.root == env.root
        assert manager.env.name == env.name
        assert manager.env.bin == env.bin
        assert manager.env.lib == env.lib