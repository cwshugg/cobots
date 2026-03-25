"""
constants.py - Shared constants for cobots config skills.

Defines canonical file and directory names used across config-related skills.
"""

# The config file name to search for when walking up the file tree.
CONFIG_FILE_NAME = "cobots-config.yaml"

# The name of the working directory created alongside the config file (or at
# the git root / current directory as a fallback).
WORKING_DIR_NAME = ".cobots"

# The subdirectory under the working directory where task files are stored.
TASKS_DIR_NAME = "tasks"
