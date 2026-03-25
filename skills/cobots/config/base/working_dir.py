"""
working_dir.py - Shared logic for resolving the cobots working directory.

Provides functions to locate the cobots config file by walking up the
directory tree, detect the git repository root, and resolve the final
working directory path. Used by skills that need to know where agents
should read/write files.
"""

import os
import subprocess

from config.base.constants import CONFIG_FILE_NAME, WORKING_DIR_NAME


def find_config_dir(start_dir: str) -> str | None:
    """Walks up from `start_dir` looking for `CONFIG_FILE_NAME`.

    Returns the directory containing the config file, or ``None`` if the
    file system root is reached without finding one.
    """
    current = os.path.abspath(start_dir)
    while True:
        candidate = os.path.join(current, CONFIG_FILE_NAME)
        if os.path.isfile(candidate):
            return current

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


def resolve_base_dir() -> str:
    """Resolves the base directory where cobots files should live.

    Applies the following strategy in order:
    1. Look for `CONFIG_FILE_NAME` by walking up the directory tree.
    2. Fall back to the git repository root.
    3. Fall back to the current working directory.

    Returns the absolute path to the directory that should contain both
    `CONFIG_FILE_NAME` and `WORKING_DIR_NAME`.
    """
    cwd = os.getcwd()

    config_dir = find_config_dir(cwd)
    if config_dir is not None:
        return config_dir

    git_root = get_git_root()
    if git_root is not None:
        return git_root

    return cwd


def resolve_working_dir() -> str:
    """Resolves the cobots working directory path.

    Returns the absolute path to the `WORKING_DIR_NAME` directory inside
    the base directory determined by `resolve_base_dir`.
    """
    return os.path.join(resolve_base_dir(), WORKING_DIR_NAME)


def resolve_config_path() -> str:
    """Resolves the absolute path to the cobots config file.

    Returns the path to `CONFIG_FILE_NAME` inside the base directory
    determined by `resolve_base_dir`. The file may or may not exist.
    """
    existing = find_config_dir(os.getcwd())
    if existing is not None:
        return os.path.join(existing, CONFIG_FILE_NAME)
    return os.path.join(resolve_base_dir(), CONFIG_FILE_NAME)


def load_config() -> "CobotsConfig":
    """Loads the cobots configuration from disk, or returns defaults.

    Attempts to find and load `CONFIG_FILE_NAME` by walking up the directory
    tree. If no config file is found, returns a `CobotsConfig` with default
    values.
    """
    from config.base.config import CobotsConfig

    config_dir = find_config_dir(os.getcwd())
    if config_dir is not None:
        return CobotsConfig.from_file(os.path.join(config_dir, CONFIG_FILE_NAME))
    return CobotsConfig()
