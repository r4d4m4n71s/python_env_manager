"""Test version information."""

from env_manager import __version__


def test_version():
    """Test version is a string."""
    assert isinstance(__version__, str)
