# Development Tools Documentation

This document describes the commands available in the development tools utility.

## Build Command

**Purpose**: Sets up the development environment and installs the package in development mode.

**Usage**: `dev_tools build`

**Details**:
- Creates or recreates a virtual environment (.venv)
- Prompts for recreation if virtual environment already exists
- Installs the package in development mode with all dev dependencies
- Essential first step before running other commands

**Options**:
- Interactive prompts for creating/recreating virtual environment

## Test Command

**Purpose**: Executes the project's test suite using pytest.

**Usage**: `dev_tools test`

**Details**:
- Runs all tests in the tests/ directory
- Verifies that the package is properly installed first
- Must run 'build' command before running tests

## Pre-commit Hooks Enable Command

**Purpose**: Enables Git pre-commit hooks for code quality checks.

**Usage**: `dev_tools prehook-on`

**Details**:
- Installs pre-commit hooks defined in .pre-commit-config.yaml
- Runs checks automatically before each commit
- Helps maintain code quality and consistency
- Must run 'build' command before enabling hooks

## Pre-commit Hooks Disable Command

**Purpose**: Disables Git pre-commit hooks.

**Usage**: `dev_tools prehook-off`

**Details**:
- Removes pre-commit hooks from Git
- Allows committing without running checks
- Useful for temporary disabling of pre-commit checks
- Must run 'build' command before disabling hooks

## Release Command

**Purpose**: Creates a new release version of the package.

**Usage**: `dev_tools release <type>`

**Arguments**:
- type: Either 'beta' or 'prod'
  * beta: Creates a beta release with .beta suffix
  * prod: Creates a production release with incremented patch version

**Details**:
- Automatically manages version numbers using bump2version
- Builds distribution packages (wheel and sdist)
- Stores artifacts in distribution/beta or distribution/release
- Must run 'build' command before creating a release

## Deploy Command

**Purpose**: Deploys the package to PyPI repositories.

**Usage**: `dev_tools deploy <target>`

**Arguments**:
- target: Either 'test' or 'prod'
  * test: Deploys to TestPyPI (for beta releases)
  * prod: Deploys to production PyPI

**Details**:
- Requires a release to be created first
- Uses twine for secure package uploading
- Validates the distribution before upload
- Must run 'build' command and create a release before deploying

## Error Handling and State Management

**Details**:
- Automatically manages program state during execution
- Cleans up state on error conditions
- Handles various error scenarios:
  * Command validation errors
  * Build and installation failures
  * Release and deployment issues
  * User interruptions (Ctrl+C)
- Uses logging for error reporting and status updates
- Provides clean error messages and recovery

**State Management**:
- Maintains state between command executions
- Automatically resets state on error conditions
- Preserves environment consistency
- Handles cleanup on abnormal termination