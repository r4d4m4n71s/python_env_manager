"""
Test module for RunnerFactory class.
"""

from unittest.mock import MagicMock

import pytest

from env_manager.runners.irunner import IRunner
from env_manager.runners.runner_factory import RunnerFactory


# Create mock runner classes for testing
class MockRunner1(IRunner):
    def __init__(self, **kwargs):
        self.kwargs = kwargs
    
    def with_env(self, env_manager):
        return self
    
    def run(self, *cmd_args, **kwargs):
        return None


class MockRunner2(IRunner):
    def __init__(self, **kwargs):
        self.kwargs = kwargs
    
    def with_env(self, env_manager):
        return self
    
    def run(self, *cmd_args, **kwargs):
        return None


class TestRunnerFactory:
    """Test cases for the RunnerFactory class."""

    def setup_method(self):
        """Reset the RunnerFactory registry before each test."""
        # Clear the existing registry to avoid test interference
        RunnerFactory._runners = {}
    
    def test_register_runner(self):
        """Test registering a runner class."""
        # Register a runner
        RunnerFactory.register("mock1", MockRunner1)
        
        # Verify it was registered
        assert "mock1" in RunnerFactory._runners
        assert RunnerFactory._runners["mock1"] == MockRunner1

    def test_create_runner(self):
        """Test creating a runner instance by name."""
        # Register a runner
        RunnerFactory.register("mock1", MockRunner1)
        
        # Create an instance
        runner = RunnerFactory.create("mock1")
        
        # Verify it's the right type
        assert isinstance(runner, MockRunner1)

    def test_create_runner_with_kwargs(self):
        """Test creating a runner with constructor arguments."""
        # Register a runner
        RunnerFactory.register("mock1", MockRunner1)
        
        # Create an instance with kwargs
        runner = RunnerFactory.create("mock1", test_arg="value", another_arg=123)
        
        # Verify kwargs were passed to constructor
        assert runner.kwargs == {"test_arg": "value", "another_arg": 123}

    def test_create_unknown_runner(self):
        """Test handling of unknown runner names."""
        # Attempt to create an unregistered runner
        with pytest.raises(ValueError, match="Unknown runner type"):
            RunnerFactory.create("unknown")

    def test_available_runners(self):
        """Test listing available runners."""
        # Empty registry
        assert RunnerFactory.available_runners() == []
        
        # Register runners
        RunnerFactory.register("mock1", MockRunner1)
        RunnerFactory.register("mock2", MockRunner2)
        
        # Verify list of available runners
        available = RunnerFactory.available_runners()
        assert len(available) == 2
        assert "mock1" in available
        assert "mock2" in available

    def test_register_multiple_runners(self):
        """Test registering multiple runner classes."""
        # Register multiple runners
        RunnerFactory.register("mock1", MockRunner1)
        RunnerFactory.register("mock2", MockRunner2)
        
        # Verify both were registered correctly
        assert len(RunnerFactory._runners) == 2
        assert RunnerFactory._runners["mock1"] == MockRunner1
        assert RunnerFactory._runners["mock2"] == MockRunner2
        
        # Create instances of each
        runner1 = RunnerFactory.create("mock1")
        runner2 = RunnerFactory.create("mock2")
        
        # Verify types
        assert isinstance(runner1, MockRunner1)
        assert isinstance(runner2, MockRunner2)

    def test_register_override(self):
        """Test overriding an existing runner registration."""
        # Register a runner
        RunnerFactory.register("mock", MockRunner1)
        assert RunnerFactory._runners["mock"] == MockRunner1
        
        # Override with a different runner
        RunnerFactory.register("mock", MockRunner2)
        assert RunnerFactory._runners["mock"] == MockRunner2
        
        # Verify the new runner is used when creating
        runner = RunnerFactory.create("mock")
        assert isinstance(runner, MockRunner2)