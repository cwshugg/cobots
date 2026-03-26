"""
working_dir.py - Shared logic for resolving the cobots working directory.

Provides functions to locate the cobots working directory and config file by
walking up the directory tree, detect the git repository root, and resolve
the final paths. The config file lives inside the working directory
(e.g. `.cobots/cobots-config.yaml`).
"""

import os
import subprocess

from workspace.base.constants import CONFIG_FILE_NAME, WORKING_DIR_NAME


def find_working_dir(start_dir: str) -> str | None:
    """Walks up from `start_dir` looking for an existing `WORKING_DIR_NAME`
    directory.

    The search is bounded by the git repository root (if inside one) so that
    a `.cobots/` in a parent directory outside the repo is not matched.
    Returns the absolute path to the first `WORKING_DIR_NAME` directory
    found, or ``None`` if none is found within the boundary.
    """
    git_root = get_git_root()
    boundary = os.path.abspath(git_root) if git_root is not None else None

    current = os.path.abspath(start_dir)
    while True:
        candidate = os.path.join(current, WORKING_DIR_NAME)
        if os.path.isdir(candidate):
            return candidate

        # Stop if we've reached the boundary (git root) or file system root.
        if boundary is not None and current == boundary:
            return None
        parent = os.path.dirname(current)
        if parent == current:
            return None
        current = parent


def get_git_root() -> str | None:
    """Returns the root directory of the current git repository, or ``None``
    if the current directory is not inside a git repository.
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def resolve_working_dir() -> str:
    """Resolves the cobots working directory path.

    Applies the following strategy in order:
    1. Walk up looking for an existing `WORKING_DIR_NAME` containing
       `CONFIG_FILE_NAME`.
    2. Fall back to `WORKING_DIR_NAME` at the git repository root.
    3. Fall back to `WORKING_DIR_NAME` in the current working directory.

    Returns the absolute path to the working directory. The directory may
    or may not exist yet.
    """
    cwd = os.getcwd()

    existing = find_working_dir(cwd)
    if existing is not None:
        return existing

    git_root = get_git_root()
    if git_root is not None:
        return os.path.join(git_root, WORKING_DIR_NAME)

    return os.path.join(cwd, WORKING_DIR_NAME)


def resolve_config_path() -> str:
    """Resolves the absolute path to the cobots config file.

    The config file lives inside the working directory. Returns the path
    to `CONFIG_FILE_NAME` inside `resolve_working_dir()`. The file may or
    may not exist yet.
    """
    return os.path.join(resolve_working_dir(), CONFIG_FILE_NAME)


def load_config() -> "CobotsConfig":
    """Loads the cobots configuration from disk, or returns defaults.

    Walks up the directory tree looking for a working directory. If one is
    found and contains a config file, loads it. Otherwise returns a
    `CobotsConfig` with default values.
    """
    from workspace.base.config import CobotsConfig

    config_path = resolve_config_path()
    if os.path.isfile(config_path):
        return CobotsConfig.from_file(config_path)
    return CobotsConfig()
