"""
config.py - StatusConfig loader for the cobots_tui skill.

Provides a convenience function to load the status configuration section
from the CobotsConfig.  Avoids double-loading by returning both the
StatusConfig and the full CobotsConfig in a single call.
"""

from cobots_lib.workspace.working_dir import load_config


def load_status_config(workspace_path=None):
    """Loads and returns ``(StatusConfig, CobotsConfig)`` for the workspace.

    Returns a tuple of ``(status_config, cobots_config)`` so that callers
    can pass the already-loaded config downstream without re-reading disk.
    """
    config = load_config(workspace_path)
    return config.status, config
