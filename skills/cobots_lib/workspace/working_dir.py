"""
working_dir.py - Shared logic for resolving the cobots working directory.

Provides functions to locate the cobots working directory and config file.
The working directory is a `.cobots/` folder that contains the config file,
tasks, and reports.

Resolution strategy:
1. If an explicit path is provided, use it directly.
2. Walk up from the current directory looking for an existing `.cobots/`.
3. Fall back to `.cobots/` in the current working directory.
"""

import os

from cobots_lib.workspace.constants import CONFIG_FILE_NAME, WORKING_DIR_NAME


def find_working_dir(start_dir: str) -> str | None:
    """Walks up from `start_dir` looking for an existing `WORKING_DIR_NAME`
    directory.

    Returns the absolute path to the first `WORKING_DIR_NAME` directory
    found, or ``None`` if the file system root is reached without finding
    one.
    """
    current = os.path.abspath(start_dir)
    while True:
        candidate = os.path.join(current, WORKING_DIR_NAME)
        if os.path.isdir(candidate):
            return candidate

        parent = os.path.dirname(current)
        if parent == current:
            return None
        current = parent


def resolve_working_dir(workspace_path: str | None = None) -> str:
    """Resolves the cobots working directory path.

    If `workspace_path` is provided, it is used as-is (as an absolute path).
    Otherwise, walks up from cwd looking for an existing `.cobots/`
    directory. Falls back to `.cobots/` in the current working directory.

    Returns the absolute path to the working directory. The directory may
    or may not exist yet.
    """
    if workspace_path is not None:
        return os.path.abspath(workspace_path)

    existing = find_working_dir(os.getcwd())
    if existing is not None:
        return existing

    return os.path.join(os.getcwd(), WORKING_DIR_NAME)


def resolve_config_path(workspace_path: str | None = None) -> str:
    """Resolves the absolute path to the cobots config file.

    The config file lives inside the working directory. Returns the path
    to `CONFIG_FILE_NAME` inside `resolve_working_dir()`. The file may or
    may not exist yet.
    """
    return os.path.join(resolve_working_dir(workspace_path), CONFIG_FILE_NAME)


def load_config(workspace_path: str | None = None) -> "CobotsConfig":
    """Loads the cobots configuration from disk, or returns defaults.

    Resolves the working directory, then loads the config file if it
    exists. Otherwise returns a `CobotsConfig` with default values.
    """
    from cobots_lib.workspace.config import CobotsConfig

    config_path = resolve_config_path(workspace_path)
    if os.path.isfile(config_path):
        return CobotsConfig.from_file(config_path)
    return CobotsConfig()
