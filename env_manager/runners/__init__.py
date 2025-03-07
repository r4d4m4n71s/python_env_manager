"""
Runners Package

This package provides various command runners for executing commands in different contexts.
"""

from env_manager.runners.irunner import IRunner
from env_manager.runners.runner import Runner
from env_manager.runners.progress_runner import ProgressRunner
from env_manager.runners.local_runner import LocalRunner
from env_manager.runners.runner_factory import RunnerFactory

# Register default runners
RunnerFactory.register("standard", Runner)
RunnerFactory.register("progress", ProgressRunner)
RunnerFactory.register("local", LocalRunner)

__all__ = [
    'IRunner',
    'Runner',
    'ProgressRunner',
    'LocalRunner',
    'RunnerFactory',
]