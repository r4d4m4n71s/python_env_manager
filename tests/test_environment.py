"""
Test module for Environment class.
"""

import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from env_manager.environment import Environment


class TestEnvironment:
    """Test cases for the Environment class."""

    def test_initialization_default(self):
        """Test default initialization using current Python environment."""
        fake_path = os.path.normpath('/fake/path')
        with patch('os.path.abspath', return_value=fake_path), \
             patch('sys.prefix', fake_path):
            env = Environment()
            assert env.root == fake_path
            assert env.name == 'path'
            
            # Check platform-specific paths
            if os.name == 'nt':  # Windows
                assert env.bin == os.path.join(fake_path, 'Scripts')
                assert env.lib == os.path.join(fake_path, 'Lib')
                assert env.python == os.path.join(fake_path, 'Scripts', 'python.exe')
            else:  # Unix-like
                assert env.bin == '/fake/path/bin'
                assert env.lib == '/fake/path/lib'
                assert env.python == '/fake/path/bin/python'

    def test_initialization_with_path(self):
        """Test initialization with a specific path."""
        test_path = '/test/venv'
        with patch('os.path.abspath', return_value=test_path):
            env = Environment(path=test_path)
            assert env.root == test_path
            assert env.name == 'venv'

    def test_initialization_with_virtual_env(self):
        """Test initialization using VIRTUAL_ENV environment variable."""
        virtual_env_path = '/test/virtual/env'
        with patch('os.environ.get', return_value=virtual_env_path), \
             patch('os.path.abspath', return_value=virtual_env_path):
            env = Environment()
            assert env.root == virtual_env_path
            assert env.name == 'env'

    def test_initialization_with_kwargs(self):
        """Test initialization with direct attribute kwargs."""
        env = Environment(
            root='/custom/path',
            name='custom_env',
            bin='/custom/path/bin',
            lib='/custom/path/lib',
            python='/custom/path/bin/python',
            is_virtual=True
        )
        assert env.root == '/custom/path'
        assert env.name == 'custom_env'
        assert env.bin == '/custom/path/bin'
        assert env.lib == '/custom/path/lib'
        assert env.python == '/custom/path/bin/python'
        assert env.is_virtual is True

    @pytest.mark.parametrize('path,expected', [
        # Windows patterns
        ('C:\\Python39', True),
        ('C:\\Users\\user\\AppData\\Local\\Programs\\Python\\Python39', True),
        ('C:\\Users\\user\\Anaconda3', True),
        ('C:\\Users\\user\\Miniconda3', True),
        ('C:\\venv', False),
        # Unix patterns
        ('/usr', True),
        ('/usr/local', True),
        ('/usr/bin', True),
        ('/opt/homebrew/bin', True),
        ('/Library/Frameworks/Python.framework', True),
        ('/home/user/anaconda3/bin', True),
        ('/home/user/miniconda3/bin', True),
        ('/home/user/venv', False),
    ])
    def test_is_local(self, path, expected):
        """Test is_local correctly identifies local Python installations."""
        with patch('os.name', 'nt' if '\\' in path else 'posix'):
            result = Environment.is_local(path)
            assert result == expected

    def test_from_dict(self):
        """Test creating an Environment instance from a dictionary."""
        env_dict = {
            'root': '/test/env',
            'name': 'test_env',
            'bin': '/test/env/bin',
            'lib': '/test/env/lib',
            'python': '/test/env/bin/python',
            'is_virtual': True
        }
        
        env = Environment.from_dict(env_dict)
        
        assert env.root == '/test/env'
        assert env.name == 'test_env'
        assert env.bin == '/test/env/bin'
        assert env.lib == '/test/env/lib'
        assert env.python == '/test/env/bin/python'
        assert env.is_virtual is True

    def test_virtual_environment_detection(self):
        """Test detection of virtual environments vs local installations."""
        # Test with path that looks like a virtual environment
        with patch('env_manager.environment.Environment.is_local', return_value=False), \
             patch('os.path.abspath', return_value='/path/to/venv'):
            env = Environment(path='/path/to/venv')
            assert env.is_virtual is True
        
        # Test with path that looks like a system Python
        with patch('env_manager.environment.Environment.is_local', return_value=True), \
             patch('os.path.abspath', return_value='/usr/bin/python'), \
             patch('sys.executable', '/usr/bin/python'):
            env = Environment(path='/usr/bin/python')
            assert env.is_virtual is False
            assert env.python == '/usr/bin/python'  # Should use sys.executable