"""
security.py - Path validation and text sanitization utilities.

Centralizes all security-sensitive operations for the cobots_tui skill.
All modules that handle file paths or render file-derived text must import
from this module.

Security constraints enforced:
- NEVER use ``Text.from_ansi(content)`` on file-derived content.
- NEVER use ``Text.from_markup(content)`` on file-derived content.
- NEVER use ``console.out()`` for file-derived content.
- NEVER use ``os.system()`` — only ``subprocess.run()`` with argument lists.
"""

import os
import shutil


def validate_path_within_workspace(candidate: str, workspace_root: str) -> str:
    """Validates that *candidate* resolves to within *workspace_root*.

    Resolves symlinks via :func:`os.path.realpath` before checking
    containment.  Returns the resolved absolute path.

    Raises:
        ValueError: If the resolved path is outside the workspace boundary.
    """
    real_candidate = os.path.realpath(candidate)
    real_workspace = os.path.realpath(workspace_root)
    if not (
        real_candidate == real_workspace
        or real_candidate.startswith(real_workspace + os.sep)
    ):
        raise ValueError(f"Path escapes workspace boundary: {candidate}")
    return real_candidate


def sanitize_display_text(text: str) -> str:
    """Escapes Rich markup in file-derived text.

    MUST be called on every string from task/report files before rendering
    in Rich or Textual widgets.  Prevents markup injection.
    """
    from rich.markup import escape as rich_escape

    return rich_escape(text)


def validate_editor(editor_env: str) -> list[str] | None:
    """Validates an ``$EDITOR`` or ``$PAGER`` environment variable value.

    Splits *editor_env* with :func:`shlex.split`, checks the first token
    exists via :func:`shutil.which`.

    Returns the argument list on success, or ``None`` if the executable
    cannot be found or the value is empty.
    """
    import shlex

    editor_env = editor_env.strip()
    if not editor_env:
        return None
    try:
        parts = shlex.split(editor_env)
    except ValueError:
        return None
    if not parts or not shutil.which(parts[0]):
        return None
    return parts
