"""
Test module for PythonLocal class.
"""

import os
import sys
import platform
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from env_manager.env_local import PythonLocal


class TestPythonLocal:
    """Test cases for the PythonLocal class."""

    def test_initialization(self):
        """Test that PythonLocal initializes correctly."""
        pl = PythonLocal()
        assert pl.python_path == sys.executable
        assert pl.is_current is True
        assert pl._base_executable is None
        assert pl._base_folder is None

    def test_initialization_with_custom_path(self):
        """Test initialization with a custom Python path."""
        custom_path = "/custom/python/path"
        pl = PythonLocal(python_path=custom_path)
        assert pl.python_path == custom_path
        assert pl.is_current is False

    @patch('os.path.isfile')
    @patch('os.access')
    @patch('os.path.realpath')
    @patch('subprocess.run')
    def test_find_base_executable_windows(self, mock_run, mock_realpath, mock_access, mock_isfile):
        """Test finding base executable on Windows."""
        # Setup for Windows test
        with patch('platform.system', return_value="Windows"), \
             patch('sys.executable', 'C:\\venv\\Scripts\\python.exe'), \
             patch('os.environ.get', return_value="C:\\Python39"):
            
            # Mock file checks
            mock_isfile.return_value = True
            mock_access.return_value = True
            mock_realpath.return_value = "C:\\Python39\\python.exe"
            
            # Mock subprocess.run for version check
            mock_completed_process = MagicMock()
            mock_completed_process.stdout = "Python 3.9.0"
            mock_run.return_value = mock_completed_process
            
            pl = PythonLocal()
            result = pl.find_base_executable()
            
            # Should find the base Python executable
            assert result is not None
            # Check that a Windows path was used in the search
            windows_path_found = False
            for call in mock_isfile.call_args_list:
                if "python.exe" in str(call) and "\\Python" in str(call):
                    windows_path_found = True
                    break
            assert windows_path_found

    @patch('os.path.isfile')
    @patch('os.access')
    @patch('os.path.realpath')
    @patch('subprocess.run')
    @patch('platform.python_version')
    def test_find_base_executable_unix(self, mock_version, mock_run, mock_realpath, mock_access, mock_isfile):
        """Test finding base executable on Unix-like systems."""
        # Define expected Unix paths
        unix_paths = [
            "/usr/bin/python3",
            "/usr/bin/python3.9",
            "/usr/local/bin/python3",
            "/usr/local/bin/python3.9"
        ]
        
        # Setup for Unix test
        with patch('platform.system', return_value="Linux"), \
             patch('sys.executable', '/home/user/venv/bin/python'), \
             patch('os.environ.get', return_value="/usr/bin"), \
             patch('sys.prefix', '/home/user/venv'), \
             patch('sys.base_prefix', '/usr'):

            # Mock Python version
            mock_version.return_value = "3.9.0"
            
            # Setup isfile mock to only return True for expected paths
            checked_paths = []
            def isfile_side_effect(path):
                checked_paths.append(path)
                # Return True for expected Unix paths
                return path in unix_paths
                
            mock_isfile.side_effect = isfile_side_effect
            
            mock_access.return_value = True
            mock_realpath.return_value = "/usr/bin/python3"
            
            # Mock subprocess.run for version checks
            mock_completed_process = MagicMock()
            mock_completed_process.stdout = "Python 3.9.0"
            mock_run.return_value = mock_completed_process
            
            pl = PythonLocal()
            result = pl.find_base_executable()
            
            # Should find the base Python executable
            assert result is not None
            
            # Check that at least one Unix-style Python path was checked
            unix_path_checked = False
            for path in checked_paths:
                for unix_path in unix_paths:
                    if unix_path == path:
                        unix_path_checked = True
                        break
                if unix_path_checked:
                    break
                    
            assert unix_path_checked, "No Unix-style Python path was checked"

    @patch('os.path.isfile')
    @patch('os.access')
    def test_find_base_executable_not_found(self, mock_access, mock_isfile):
        """Test behavior when base executable is not found."""
        # Mock file checks to always return False
        mock_isfile.return_value = False
        mock_access.return_value = False
        
        with patch('subprocess.run', side_effect=subprocess.SubprocessError):
            pl = PythonLocal()
            result = pl.find_base_executable()
            
            # Should return None when no executable is found
            assert result is None

    @patch('os.path.exists')
    @patch('os.path.isfile')
    @patch('os.access')
    @patch('os.path.realpath')
    @patch('subprocess.run')
    def test_find_base_executable_from_venv_cfg(self, mock_run, mock_realpath, mock_access, mock_isfile, mock_exists):
        """Test finding base executable from pyvenv.cfg."""
        # Setup mock file content
        mock_file_content = """
        home = /usr/bin
        include-system-site-packages = false
        version = 3.9.0
        """
        mock_open = MagicMock()
        mock_open.return_value.__enter__.return_value.readlines.return_value = mock_file_content.splitlines()
        
        with patch('builtins.open', mock_open), \
             patch('platform.system', return_value="Linux"), \
             patch('sys.executable', '/home/user/venv/bin/python'), \
             patch('os.environ.get', return_value="/usr/bin"):
            
            # Mock file checks
            mock_exists.return_value = True
            mock_isfile.return_value = True
            mock_access.return_value = True
            mock_realpath.return_value = "/usr/bin/python3"
            
            # Mock subprocess.run for version check
            mock_completed_process = MagicMock()
            mock_completed_process.stdout = "Python 3.9.0"
            mock_run.return_value = mock_completed_process
            
            pl = PythonLocal()
            result = pl.find_base_executable()
            
            # Should find the base Python executable
            assert result is not None

    @patch('platform.system', return_value="Linux")
    @patch('subprocess.run')
    def test_get_version(self, mock_run, _):
        """Test getting Python version."""
        # Mock subprocess.run to return a version
        mock_completed_process = MagicMock()
        mock_completed_process.stdout = "Python 3.9.0"
        mock_run.return_value = mock_completed_process
        
        pl = PythonLocal(python_path="/usr/bin/python3")
        result = pl._get_version()
        
        assert result == "3.9.0"

    @patch('platform.system', return_value="Linux")
    @patch('subprocess.run')
    def test_get_prefix(self, mock_run, _):
        """Test getting Python prefix."""
        # Mock subprocess.run to return a prefix
        mock_completed_process = MagicMock()
        mock_completed_process.stdout = "/usr/bin"
        mock_run.return_value = mock_completed_process
        
        pl = PythonLocal(python_path="/usr/bin/python3")
        result = pl._get_prefix()
        
        assert result == "/usr/bin"

    @patch('os.path.isfile')
    @patch('os.access')
    @patch('os.path.realpath')
    @patch('subprocess.run')
    def test_get_base_name(self, mock_run, mock_realpath, mock_access, mock_isfile):
        """Test getting base folder name."""
        # Setup for test
        with patch('platform.system', return_value="Linux"):
            # Mock file checks
            mock_isfile.return_value = True
            mock_access.return_value = True
            mock_realpath.return_value = "/usr/bin/python3"
            
            # Mock subprocess.run for version check
            mock_completed_process = MagicMock()
            mock_completed_process.stdout = "Python 3.9.0"
            mock_run.return_value = mock_completed_process
            
            pl = PythonLocal()
            # Mock find_base_executable to return a known path
            pl._base_executable = "/usr/bin/python3"
            
            result = pl.get_base_name()
            
            # Should return the base folder
            assert result is not None
            assert "usr" in result