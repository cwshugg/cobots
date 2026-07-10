"""
data.py - Shared data layer for the cobots_tui skill.

Provides frozen dataclasses for tasks, reports, activity events, and
workspace snapshots.  Both output modes (rich overview and TUI) consume
a single :class:`StatusSnapshot` produced by :func:`load_snapshot`.

Design principles:
- Never crash on bad data — return ``None`` or skip with a warning.
- All collection fields use ``tuple`` for immutability on frozen dataclasses.
- ``dict`` fields (task_counts_by_status, task_counts_by_owner) are
  accepted as a pragmatic compromise: ``MappingProxyType`` is not easily
  JSON-serializable.  Consumers should treat them as read-only.
"""

import glob
import os
import types
import warnings
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone

from cobots_lib.workspace.working_dir import resolve_working_dir, load_config
from cobots_lib.workspace.constants import (
    TASKS_DIR_NAME,
    REPORTS_DIR_NAME,
    TASK_FILE_SUFFIX,
    REPORT_FILE_SUFFIX,
)
from cobots_lib.parsing import parse_frontmatter, parse_discussion_headers
from cobots_lib.workspace.knowledge import list_knowledge_files

from security import validate_path_within_workspace

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MAX_FILE_SIZE: int = 1_048_576  # 1 MB — skip files larger than this


# ---------------------------------------------------------------------------
# Dataclasses (all frozen, collections as tuples)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TaskData:
    """A single parsed task."""

    id: str
    title: str
    status: str
    author: str
    owner: str
    created_timestamp: str
    linked_tasks: tuple[str, ...]
    path: str           # Absolute file path (internal use)
    relative_path: str  # Workspace-relative path (display/JSON)


@dataclass(frozen=True)
class ReportData:
    """A single parsed report."""

    id: str
    title: str
    author: str
    created_timestamp: str
    path: str
    relative_path: str


@dataclass(frozen=True)
class ActivityEvent:
    """A single entry in the activity timeline."""

    timestamp: str
    event_type: str   # "task_created" | "task_updated" | "report_created"
    summary: str
    entity_id: str


@dataclass(frozen=True)
class StatusSnapshot:
    """Immutable snapshot of the entire workspace state."""

    workspace_name: str
    workspace_root: str
    tasks: tuple[TaskData, ...]
    reports: tuple[ReportData, ...]
    task_counts_by_status: types.MappingProxyType
    task_counts_by_owner: types.MappingProxyType
    report_count: int
    activity_timeline: tuple[ActivityEvent, ...]
    snapshot_timestamp: str
    knowledge_count: int = 0

    def status_counts_dict(self) -> dict[str, int]:
        """Returns ``task_counts_by_status`` as a plain ``dict``.

        Consumers should call this instead of inlining the
        ``MappingProxyType`` → ``dict`` conversion.
        """
        if isinstance(self.task_counts_by_status, types.MappingProxyType):
            return dict(self.task_counts_by_status)
        return self.task_counts_by_status

    def owner_counts_dict(self) -> dict[str, int]:
        """Returns ``task_counts_by_owner`` as a plain ``dict``.

        Consumers should call this instead of inlining the
        ``MappingProxyType`` → ``dict`` conversion.
        """
        if isinstance(self.task_counts_by_owner, types.MappingProxyType):
            return dict(self.task_counts_by_owner)
        return self.task_counts_by_owner


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------


def _relative_path(abs_path: str, workspace_root: str) -> str:
    """Returns a workspace-relative path (e.g. ``tasks/abc.task.md``)."""
    # workspace_root points to the .cobots directory.
    parent = os.path.dirname(workspace_root)
    try:
        return os.path.relpath(abs_path, parent)
    except ValueError:
        # On Windows, relpath can fail across drives.
        return abs_path


def _validate_and_parse(
    path: str, workspace_root: str
) -> tuple[dict, str, str] | None:
    """Validates path, checks size, parses frontmatter.

    Returns (frontmatter_dict, validated_path, relative_path) or None.
    """
    try:
        validated = validate_path_within_workspace(path, workspace_root)
    except ValueError:
        warnings.warn(f"Skipping file outside workspace: {os.path.basename(path)}")
        return None
    try:
        size = os.path.getsize(validated)
    except OSError:
        warnings.warn(f"Cannot stat file: {os.path.basename(path)}")
        return None
    if size > MAX_FILE_SIZE:
        warnings.warn(f"Skipping oversized file ({size} bytes): {os.path.basename(path)}")
        return None
    try:
        fm, _ = parse_frontmatter(validated)
    except OSError as exc:
        warnings.warn(f"Cannot read file {os.path.basename(path)}: {exc}")
        return None
    if not fm:
        warnings.warn(f"No frontmatter in file: {os.path.basename(path)}")
        return None
    rel = _relative_path(validated, workspace_root)
    return (fm, validated, rel)


def load_task(path: str, workspace_root: str) -> TaskData | None:
    """Parses a single ``.task.md`` file into a :class:`TaskData`.

    Returns ``None`` on any error (never crashes).
    """
    result = _validate_and_parse(path, workspace_root)
    if result is None:
        return None
    frontmatter, validated, rel = result
    return TaskData(
        id=str(frontmatter.get("id", "")),
        title=str(frontmatter.get("title", "")),
        status=str(frontmatter.get("status", "")),
        author=str(frontmatter.get("author", "")),
        owner=str(frontmatter.get("owner", "")),
        created_timestamp=str(frontmatter.get("created_timestamp", "")),
        linked_tasks=tuple(
            str(t) for t in frontmatter.get("linked_tasks", []) or []
        ),
        path=validated,
        relative_path=rel,
    )


def load_report(path: str, workspace_root: str) -> ReportData | None:
    """Parses a single ``.report.md`` file into a :class:`ReportData`.

    Returns ``None`` on any error (never crashes).
    """
    result = _validate_and_parse(path, workspace_root)
    if result is None:
        return None
    frontmatter, validated, rel = result
    return ReportData(
        id=str(frontmatter.get("id", "")),
        title=str(frontmatter.get("title", "")),
        author=str(frontmatter.get("author", "")),
        created_timestamp=str(frontmatter.get("created_timestamp", "")),
        path=validated,
        relative_path=rel,
    )


def list_task_files(workspace_root: str) -> list[str]:
    """Globs all ``.task.md`` files under the workspace tasks directory."""
    tasks_dir = os.path.join(workspace_root, TASKS_DIR_NAME)
    pattern = os.path.join(tasks_dir, f"*{TASK_FILE_SUFFIX}")
    return sorted(glob.glob(pattern))


def list_report_files(workspace_root: str) -> list[str]:
    """Globs all ``.report.md`` files under the workspace reports directory."""
    reports_dir = os.path.join(workspace_root, REPORTS_DIR_NAME)
    pattern = os.path.join(reports_dir, f"*{REPORT_FILE_SUFFIX}")
    return sorted(glob.glob(pattern))


def _read_body_safe(path: str, workspace_root: str) -> str:
    """Reads the body of a markdown file, returning empty string on error.

    Enforces ``MAX_FILE_SIZE`` before reading to guard against files that
    grew between the initial ``load_task()`` size check and this call
    (defense-in-depth against TOCTOU window).

    Also validates that *path* resolves within *workspace_root*
    (defense-in-depth against path traversal).
    """
    try:
        validated = validate_path_within_workspace(path, workspace_root)
    except ValueError:
        return ""
    try:
        if os.path.getsize(validated) > MAX_FILE_SIZE:
            return ""
        _, body = parse_frontmatter(validated)
        return body
    except OSError:
        return ""


def build_activity_timeline(
    tasks: tuple[TaskData, ...],
    reports: tuple[ReportData, ...],
    workspace_root: str,
    count: int = 20,
) -> tuple[ActivityEvent, ...]:
    """Merges task and report events into a newest-first timeline.

    Event sources:
    - Task creation timestamps
    - Task discussion headers (parsed from task file bodies)
    - Report creation timestamps
    """
    events: list[ActivityEvent] = []

    for task in tasks:
        if task.created_timestamp:
            events.append(ActivityEvent(
                timestamp=task.created_timestamp,
                event_type="task_created",
                summary=task.title,
                entity_id=task.id,
            ))
        # Parse discussion headers from the task body for update events.
        body = _read_body_safe(task.path, workspace_root)
        if body:
            for ts, author in parse_discussion_headers(body):
                events.append(ActivityEvent(
                    timestamp=ts,
                    event_type="task_updated",
                    summary=f"Discussion by {author} on: {task.title}",
                    entity_id=task.id,
                ))

    for report in reports:
        if report.created_timestamp:
            events.append(ActivityEvent(
                timestamp=report.created_timestamp,
                event_type="report_created",
                summary=report.title,
                entity_id=report.id,
            ))

    # Sort newest-first, then slice.
    events.sort(key=lambda e: e.timestamp, reverse=True)
    return tuple(events[:count])


def load_snapshot(
    workspace_path: str | None = None,
    activity_count: int = 20,
    cobots_config=None,
) -> StatusSnapshot:
    """Loads the full workspace state into an immutable snapshot.

    This is the single function both output modes call.

    Args:
        workspace_path: Explicit path to the ``.cobots/`` directory.
            If ``None``, auto-resolved by walking up from cwd.
        activity_count: Maximum number of activity events to include.
        cobots_config: Pre-loaded :class:`CobotsConfig` instance.
            When provided, the internal ``load_config()`` disk read is
            skipped — avoids redundant I/O when the caller already has
            the config (e.g. from ``load_status_config()``).

    Returns:
        A frozen :class:`StatusSnapshot` with all workspace data.
    """
    workspace_root = resolve_working_dir(workspace_path)
    if cobots_config is None:
        cobots_config = load_config(workspace_path)
    workspace_name = cobots_config.workspace_name or os.path.basename(
        os.path.dirname(workspace_root)
    )

    # --- Parse tasks (sorted newest-first by created_timestamp) ---
    task_files = list_task_files(workspace_root)
    tasks_list: list[TaskData] = []
    for path in task_files:
        task = load_task(path, workspace_root)
        if task is not None:
            tasks_list.append(task)
    tasks_list.sort(key=lambda t: t.created_timestamp, reverse=True)
    tasks = tuple(tasks_list)

    # --- Parse reports (sorted newest-first by created_timestamp) ---
    report_files = list_report_files(workspace_root)
    reports_list: list[ReportData] = []
    for path in report_files:
        report = load_report(path, workspace_root)
        if report is not None:
            reports_list.append(report)
    reports_list.sort(key=lambda r: r.created_timestamp, reverse=True)
    reports = tuple(reports_list)

    # --- Count knowledge entries (reuses the cobots_lib helper) ---
    knowledge_count = len(list_knowledge_files(workspace_path))

    # --- Aggregations ---
    status_counter: Counter[str] = Counter(t.status for t in tasks)
    owner_counter: Counter[str] = Counter(
        (t.owner or "(unassigned)").lower() for t in tasks
    )

    # --- Activity timeline ---
    timeline = build_activity_timeline(
        tasks, reports, workspace_root, count=activity_count
    )
    # --- Timestamp ---
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    return StatusSnapshot(
        workspace_name=workspace_name,
        workspace_root=workspace_root,
        tasks=tasks,
        reports=reports,
        task_counts_by_status=types.MappingProxyType(dict(status_counter)),
        task_counts_by_owner=types.MappingProxyType(dict(owner_counter)),
        report_count=len(reports),
        activity_timeline=timeline,
        snapshot_timestamp=now,
        knowledge_count=knowledge_count,
    )
