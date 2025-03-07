import os
import sys
import platform
import subprocess
from typing import Optional


class PythonLocal:
    """Class to find and interact with Python installations."""
    
    def __init__(self, python_path: Optional[str] = None):
        """Initialize with a specific Python path or use the current interpreter."""
        self.python_path = python_path or sys.executable
        self.is_current = self.python_path == sys.executable
        self._base_executable = None
        self._base_folder = None
    
    def find_base_executable(self) -> Optional[str]:
        """
        Find the base Python executable for a virtual environment with advanced detection.
        
        Returns:
            Optional[str]: Path to the base Python executable, or None if not a virtual env
                          or if the base executable cannot be found.
        """
        # For demonstration purposes, assume we've already checked this is a virtual environment
        
        if self._base_executable is not None:
            return self._base_executable
        
        if self.is_current and not (hasattr(sys, 'real_prefix') or hasattr(sys, 'base_prefix')):
            return None
        
        # Get info we'll need for the search
        prefix = sys.prefix if self.is_current else self._get_prefix()
        possible_executables = []
        
        # Extract version information for path construction
        version = platform.python_version() if self.is_current else self._get_version()
        
        version_parts = version.split('.')
        if len(version_parts) >= 2:
            major_version = version_parts[0]
            minor_version = version_parts[1]
            version_str = f"{major_version}.{minor_version}"
        else:
            major_version = "3"  # Default to Python 3
            minor_version = "0"
            version_str = "3"
        
        # METHOD 1: Extract from pyvenv.cfg (most reliable method)
        venv_cfg_path = os.path.join(prefix, "pyvenv.cfg")
        if os.path.exists(venv_cfg_path):
            try:
                with open(venv_cfg_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip().startswith("home ="):
                            home_path = line.split("=", 1)[1].strip()
                            # Handle both absolute paths and relative paths
                            if not os.path.isabs(home_path):
                                home_path = os.path.normpath(os.path.join(os.path.dirname(venv_cfg_path), home_path))
                                
                            # Construct executable path based on platform
                            if platform.system() == "Windows":
                                exe_names = ["python.exe", f"python{major_version}.exe"]
                            else:
                                exe_names = ["python", f"python{major_version}", f"python{version_str}"]
                                
                            # First check direct path (Windows often has python.exe in home dir)
                            for exe_name in exe_names:
                                base_exe = os.path.join(home_path, exe_name)
                                if os.path.isfile(base_exe) and os.access(base_exe, os.X_OK):
                                    possible_executables.append(base_exe)
                                    
                            # Then check bin/Scripts subdirectory
                            bin_dir = "Scripts" if platform.system() == "Windows" else "bin"
                            for exe_name in exe_names:
                                base_exe = os.path.join(home_path, bin_dir, exe_name)
                                if os.path.isfile(base_exe) and os.access(base_exe, os.X_OK):
                                    possible_executables.append(base_exe)
            except (IOError, UnicodeDecodeError):
                pass  # Silently handle file read errors
        
        # METHOD 2: Direct system attribute access for current interpreter
        if self.is_current:
            # Python 3.8+ has sys.base_executable
            if hasattr(sys, 'base_executable') and sys.base_executable:
                if os.path.isfile(sys.base_executable) and os.access(sys.base_executable, os.X_OK):
                    possible_executables.append(sys.base_executable)
            
            # Get base prefix from system
            base_prefix = getattr(sys, 'real_prefix', getattr(sys, 'base_prefix', None))
            if base_prefix:
                if platform.system() == "Windows":
                    base_exe = os.path.join(base_prefix, "python.exe")
                    if os.path.isfile(base_exe) and os.access(base_exe, os.X_OK):
                        possible_executables.append(base_exe)
                else:
                    for exe_name in [f"python{version_str}", f"python{major_version}", "python3", "python"]:
                        base_exe = os.path.join(base_prefix, "bin", exe_name)
                        if os.path.isfile(base_exe) and os.access(base_exe, os.X_OK):
                            possible_executables.append(base_exe)
        else:
            # Non-current interpreter: try to get base prefix by running the interpreter
            try:
                cmd = "import sys; print(getattr(sys, 'real_prefix', getattr(sys, 'base_prefix', sys.prefix)))"
                result = subprocess.run(
                    [self.python_path, "-c", cmd],
                    capture_output=True, text=True, check=True, timeout=2
                )
                
                base_prefix = result.stdout.strip()
                if base_prefix and base_prefix != prefix:
                    if platform.system() == "Windows":
                        base_exe = os.path.join(base_prefix, "python.exe")
                        if os.path.isfile(base_exe) and os.access(base_exe, os.X_OK):
                            possible_executables.append(base_exe)
                    else:
                        for exe_name in [f"python{version_str}", f"python{major_version}", "python3", "python"]:
                            base_exe = os.path.join(base_prefix, "bin", exe_name)
                            if os.path.isfile(base_exe) and os.access(base_exe, os.X_OK):
                                possible_executables.append(base_exe)
            except (subprocess.SubprocessError, subprocess.TimeoutExpired):
                pass  # Silently handle subprocess errors
        
        # METHOD 3: Common system locations based on platform and version
        if not possible_executables:
            is_64bit = platform.machine().endswith('64')
            
            if platform.system() == "Windows":
                program_files = os.environ.get("ProgramFiles", "C:\\Program Files")
                program_files_x86 = os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")
                local_app_data = os.environ.get("LocalAppData", "")
                
                candidates = [
                    # Direct version match
                    f"C:\\Python{major_version}{minor_version}\\python.exe",
                    # Program Files
                    os.path.join(program_files, f"Python{version_str}", "python.exe"),
                    # Program Files (x86) for 32-bit Python on 64-bit Windows
                    os.path.join(program_files_x86, f"Python{version_str}", "python.exe") if is_64bit else None,
                    # Local App Data
                    os.path.join(local_app_data, f"Programs\\Python\\Python{major_version}{minor_version}\\python.exe"),
                    # Windows Store Python
                    os.path.join(local_app_data, f"Microsoft\\WindowsApps\\python{major_version}.exe"),
                    # Other common locations
                    f"C:\\Python{major_version}\\python.exe",
                    "C:\\Python\\python.exe",
                ]
            else:  # Unix-like systems
                candidates = [
                    # Exact version match
                    f"/usr/bin/python{version_str}",
                    f"/usr/local/bin/python{version_str}",
                    # Major version match
                    f"/usr/bin/python{major_version}",
                    f"/usr/local/bin/python{major_version}",
                    # macOS specific locations
                    f"/opt/homebrew/bin/python{major_version}",
                    f"/Library/Frameworks/Python.framework/Versions/{version_str}/bin/python{major_version}",
                    # Common fallbacks
                    "/usr/bin/python3",
                    "/usr/local/bin/python",
                ]
            
            # Filter None values and check existence
            for candidate in filter(None, candidates):
                if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
                    possible_executables.append(candidate)
        
        # METHOD 4: Search PATH for suitable Python executables
        if not possible_executables:
            path_dirs = os.environ.get("PATH", "").split(os.pathsep)
            
            for path_dir in path_dirs:
                if not os.path.exists(path_dir) or prefix in path_dir:
                    continue  # Skip non-existent dirs and current venv dirs
                    
                # Check for interpreters matching our version first, then fallbacks
                for exe_name in [f"python{version_str}", f"python{major_version}", "python3", "python"]:
                    if platform.system() == "Windows":
                        exe_name += ".exe"
                    
                    candidate = os.path.join(path_dir, exe_name)
                    if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
                        # Make sure it's not the current interpreter or a symlink to it
                        if os.path.realpath(candidate) != os.path.realpath(self.python_path):
                            # Verify it's not another venv python by checking version
                            try:
                                result = subprocess.run(
                                    [candidate, "-c", "import sys; print('venv' if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix) else 'system')"],
                                    capture_output=True, text=True, check=True, timeout=2
                                )
                                
                                # Only add system Pythons, not other venvs
                                if result.stdout.strip() == 'system':
                                    possible_executables.append(candidate)
                            except (subprocess.SubprocessError, subprocess.TimeoutExpired):
                                # If we can't check, add it anyway as a fallback
                                possible_executables.append(candidate)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_executables = []
        
        for exe in possible_executables:
            real_path = os.path.realpath(exe)
            if real_path not in seen:
                # Verify the executable actually works
                try:
                    subprocess.run(
                        [exe, "--version"], 
                        capture_output=True, check=True, timeout=1
                    )
                    seen.add(real_path)
                    unique_executables.append(exe)
                except (subprocess.SubprocessError, subprocess.TimeoutExpired, PermissionError):
                    # Skip executables that don't actually work
                    pass
        
        # Cache and return the result
        self._base_executable = unique_executables[0] if unique_executables else None
        return self._base_executable
    
    def get_base_name(self) -> Optional[str]:
        """
        Find the base folder where the base Python executable is installed.
        
        Returns:
            Optional[str]: Path to the base Python installation folder, or None if not a virtual env
                          or if the base executable cannot be found.
        """
        if self._base_folder is not None:
            return self._base_folder
            
        base_exe = self.find_base_executable()
        if not base_exe:
            return None
            
        # Get the directory containing the executable
        exe_dir = os.path.dirname(os.path.realpath(base_exe))
        
        # For Unix-like systems, Python is typically in a bin directory
        if platform.system() != "Windows" and os.path.basename(exe_dir) == "bin":
            # Go up one level to get the base Python installation directory
            base_folder = os.path.dirname(exe_dir)
        else:
            # On Windows or if not in a bin directory, use the directory containing the executable
            base_folder = exe_dir
            
        self._base_folder = base_folder
        return base_folder
    
    def _get_prefix(self) -> str:
        """Get the prefix for a non-current Python interpreter."""
        try:
            result = subprocess.run(
                [self.python_path, "-c", "import sys; print(sys.prefix)"],
                capture_output=True, text=True, check=True, timeout=2
            )
            return result.stdout.strip()
        except (subprocess.SubprocessError, subprocess.TimeoutExpired):
            # Fallback: try to determine from path
            executable_path = os.path.realpath(self.python_path)
            if platform.system() == "Windows":
                if "\\Scripts\\" in executable_path:
                    return os.path.dirname(os.path.dirname(executable_path))
                return os.path.dirname(executable_path)
            else:
                if "/bin/" in executable_path:
                    return os.path.dirname(os.path.dirname(executable_path))
                return os.path.dirname(executable_path)
    
    def _get_version(self) -> str:
        """Get the version of a non-current Python interpreter."""
        try:
            result = subprocess.run(
                [self.python_path, "--version"],
                capture_output=True, text=True, check=True, timeout=2
            )
            match = result.stdout.strip() or result.stderr.strip()
            version = match.split()[-1] if match else "3.0"  # Default if can't determine
            return version
        except (subprocess.SubprocessError, subprocess.TimeoutExpired):
            return "3.0"  # Default if can't determine