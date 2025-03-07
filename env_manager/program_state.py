"""
Program State Management Module

This module provides functionality for persistent state management in Python applications.
The GlobalState class offers a dictionary-like interface for storing and retrieving
application state, with automatic persistence to the filesystem.

Key Features:
- Dictionary-like interface (inherits from dict)
- Automatic state persistence to config files
- Cross-platform config directory handling
- JSON serialization for complex data types
- Multiple update methods (dict, key-value, kwargs)
- Configurable storage location

Default Storage Location:
- Windows: %USERPROFILE%\\config\\[app_name]\\
- Unix: ~/.config/[app_name]/

The state is stored in INI format with JSON serialization for values,
allowing for storage of complex Python data types.
"""

import configparser
import json
import os
import tomllib
from pathlib import Path

def read_toml(filepath = None):
    """Loads data from a TOML file with error handling."""
    try:
        if not filepath:
            filepath = os.path.join(os.getcwd(), "pyproject.toml")

        with open(filepath, 'rb') as f:
            data = tomllib.load(f)
            return data
    except FileNotFoundError:
        print(f"TOML file not found: {filepath}")
        return None
    except tomllib.TOMLDecodeError as e:
        print(f"Error decoding TOML file: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

class GlobalState(dict):  # Inherit from dict
    
    def __init__(self, app_name, config_dir=None):
        """
        Initialize GlobalState with configuration for state persistence.
        
        Args:
            app_name (str): Name of the application for config directory
            filename (str): Name of the config file
            config_dir (str, optional): Custom config directory path. If None, uses ~/.config/[app_name]
        """
        super().__init__()  # Initialize the parent dict class
        self.app_name = app_name
        self.filename = f"{app_name}.ini"

        if config_dir is None:
            # Use ~/.config/[app_name] as default config directory
            self.config_dir = str(Path.home() / '.config')
        else:
            self.config_dir = config_dir

        self.full_path = str(Path(self.config_dir) / self.filename)
        
        # Create config directory if it doesn't exist
        #if not os.path.exists(self.config_dir):
            #os.makedirs(self.config_dir, exist_ok=True)
            
        self.load()  # Load state after initializing the dictionary

    def save(self):
        """Save the current state to the config file."""
        config = configparser.ConfigParser()
        if not config.has_section('state'):
            config.add_section('state')

        for key, value in self.items():
            config.set('state', key, json.dumps(value))

        # Ensure directory exists before saving
        #os.makedirs(os.path.dirname(self.full_path), exist_ok=True)
        
        with open(self.full_path, 'w') as configfile:
            config.write(configfile)

    def load(self):
        """Load state from the config file if it exists."""
        config = configparser.ConfigParser()
        try:
            if not os.path.exists(self.full_path):
                return  # No state file exists yet
                
            config.read(self.full_path)
            self.clear()  # Clear existing data before loading
            
            if not config.has_section('state'):
                return  # No state section exists
                
            for key, value in config.items('state'):
                try:
                    self[key] = json.loads(value)  # Set values directly
                except json.JSONDecodeError:
                    self[key] = value  # Keep as string if not valid JSON
        except Exception as e:
            print(f"Error loading state: {e}")
            # Don't raise - maintain empty state on error

    def update(self, *args, **kwargs):
        """
        Update the state with new values.
        
        Supports:
        - Dictionary update: update({'key': 'value'})
        - Key-value update: update('key', 'value')
        - Keyword update: update(key='value')
        """
        if len(args) == 1 and isinstance(args[0], dict):
            # Handle dictionary update
            super().update(args[0])
        elif len(args) == 2:
            # Handle key-value pair update
            self[args[0]] = args[1]
        else:
            # Handle keyword arguments
            super().update(kwargs)

    def reset(self):
        """Reset the state and remove the config file if it exists."""
        self.clear()  # Clear the in-memory state
        
        try:
            if os.path.exists(self.full_path):
                os.remove(self.full_path)
                print(f"State file removed: {self.full_path}")
            
            # Also try to remove empty config directory
            if os.path.exists(self.config_dir) and not os.listdir(self.config_dir):
                os.rmdir(self.config_dir)
                print(f"Empty config directory removed: {self.config_dir}")
        except Exception as e:
            print(f"Error during reset: {e}")

"""Example usage:

# Default config directory (~/.config/MyApp1/config.ini)
state = GlobalState(app_name="MyApp1")

# Custom config directory and filename
state = GlobalState(
    app_name="MyApp2",
    filename="settings.ini",
    config_dir="/custom/path"
)

# Basic operations
state.update('counter', 1)
state.update('name', "My Program")
state.update('data', [1, 2, 3])
state.save()

# Dictionary-style operations
state['new_key'] = 'new_value'
print(state['new_key'])
state.update({'key1': 'value1', 'key2': 'value2'})

# Load existing state in new instance
state2 = GlobalState(app_name="MyApp1")  # Loads from ~/.config/MyApp1/config.ini
print("Loaded state:", state2)

# Reset and cleanup
state.reset()  # Clears state and removes config file/empty directory
"""