"""
helpers.py - Shared test fixture helpers for cobots_tui tests.

Provides factory functions to create mock workspace directories with
sample task and report files.  Created early (Phase 1) so all test
files can reuse them (addresses review finding F6).
"""

import os
import textwrap
import types

from data import StatusSnapshot


def create_mock_workspace(tmp_dir: str) -> str:
    """Creates a ``.cobots/`` workspace with sample tasks and reports.

    Args:
        tmp_dir: Root temporary directory to create the workspace in.

    Returns:
        The path to the ``.cobots/`` directory.
    """
    cobots_dir = os.path.join(tmp_dir, ".cobots")
    tasks_dir = os.path.join(cobots_dir, "tasks")
    reports_dir = os.path.join(cobots_dir, "reports")
    os.makedirs(tasks_dir, exist_ok=True)
    os.makedirs(reports_dir, exist_ok=True)

    # Write a minimal cobots-config.yaml.
    config_path = os.path.join(cobots_dir, "cobots-config.yaml")
    with open(config_path, "w", encoding="utf-8") as f:
        f.write(textwrap.dedent("""\
            workspace_name: test-workspace
            task_status_values:
            - pending
            - underway
            - done
            - abandoned
            task_id_length: 16
            report_id_length: 16
            ntfy:
              url: https://ntfy.sh
              topic: test-topic
              token: ''
              mode: confidential
            status:
              refresh_rate: 5
              activity_count: 20
        """))

    return cobots_dir


def write_task_file(
    tasks_dir: str,
    task_id: str = "aaaa1111bbbb2222",
    title: str = "Test Task",
    status: str = "pending",
    author: str = "alice",
    owner: str = "bob",
    created_timestamp: str = "2026-04-22 10:00:00",
    linked_tasks: list[str] | None = None,
    body: str = "Task description here.",
) -> str:
    """Writes a sample ``.task.md`` file and returns its path."""
    linked = linked_tasks or []
    linked_yaml = ", ".join(f'"{t}"' for t in linked)

    path = os.path.join(tasks_dir, f"{task_id}.task.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(textwrap.dedent(f"""\
            ---
            id: "{task_id}"
            title: "{title}"
            status: "{status}"
            author: "{author}"
            owner: "{owner}"
            created_timestamp: "{created_timestamp}"
            linked_tasks: [{linked_yaml}]
            ---
            {body}
        """))
    return path


def write_report_file(
    reports_dir: str,
    report_id: str = "cccc3333dddd4444",
    title: str = "Test Report",
    author: str = "lorey",
    created_timestamp: str = "2026-04-22 11:00:00",
    body: str = "Report content here.",
) -> str:
    """Writes a sample ``.report.md`` file and returns its path."""
    path = os.path.join(reports_dir, f"{report_id}.report.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(textwrap.dedent(f"""\
            ---
            id: "{report_id}"
            title: "{title}"
            author: "{author}"
            created_timestamp: "{created_timestamp}"
            ---
            {body}
        """))
    return path


def write_knowledge_file(
    knowledge_dir: str,
    entry_id: str = "eeee5555ffff6666",
    title: str = "Test Knowledge Entry",
    author: str = "scribs",
    created_timestamp: str = "2026-04-22 11:30:00",
    updated_timestamp: str = "2026-04-22 11:30:00",
    tags: list[str] | None = None,
    body: str = "Knowledge content here.",
) -> str:
    """Writes a sample ``.knowledge.md`` file and returns its path.

    Creates the ``knowledge_dir`` if it does not already exist so that
    callers can rely on this helper without a separate ``makedirs`` step.
    """
    os.makedirs(knowledge_dir, exist_ok=True)
    tag_list = tags or []
    tags_yaml = ", ".join(f'"{t}"' for t in tag_list)

    path = os.path.join(knowledge_dir, f"{entry_id}.knowledge.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(textwrap.dedent(f"""\
            ---
            id: "{entry_id}"
            title: "{title}"
            author: "{author}"
            created_timestamp: "{created_timestamp}"
            updated_timestamp: "{updated_timestamp}"
            tags: [{tags_yaml}]
            ---
            {body}
        """))
    return path


def make_snapshot(**kwargs) -> StatusSnapshot:
    """Creates a :class:`StatusSnapshot` with sensible defaults.

    Any keyword argument overrides the corresponding default value.
    Useful for unit tests that only care about a subset of fields.
    """
    defaults = {
        "workspace_name": "test-ws",
        "workspace_root": "/tmp/test/.cobots",
        "tasks": (),
        "reports": (),
        "task_counts_by_status": types.MappingProxyType({}),
        "task_counts_by_owner": types.MappingProxyType({}),
        "report_count": 0,
        "activity_timeline": (),
        "snapshot_timestamp": "2026-04-22 12:00:00",
        "knowledge_count": 0,
    }
    defaults.update(kwargs)
    return StatusSnapshot(**defaults)


def _skip_if_no_textual():
    """Skip test if textual is not installed."""
    try:
        import textual
        return False
    except ImportError:
        return True
