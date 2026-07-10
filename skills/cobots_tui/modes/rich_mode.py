"""
rich_mode.py - Rich-formatted static snapshot output.

Renders a formatted terminal view using the Rich library.  All
file-derived strings are passed through :func:`sanitize_display_text`
before rendering to prevent markup injection.
"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box

from constants import (
    CERULEAN,
    get_status_color,
)
from data import load_snapshot, StatusSnapshot
from security import sanitize_display_text


def _build_summary_text(snapshot: StatusSnapshot) -> str:
    """Builds a one-line summary string for the summary panel."""
    counts_status = snapshot.status_counts_dict()
    parts: list[str] = []
    for status, count in sorted(counts_status.items()):
        color = get_status_color(status)
        parts.append(
            f"[{color}]{sanitize_display_text(status)}: "
            f"{count}[/{color}]"
        )
    task_summary = ", ".join(parts) if parts else "No tasks"
    return (
        f"Tasks: {task_summary}  |  Reports: {snapshot.report_count}"
        f"  |  Knowledge: {snapshot.knowledge_count}"
    )


def _build_task_table(snapshot: StatusSnapshot) -> Table:
    """Builds a Rich Table of tasks."""
    table = Table(
        title="Tasks",
        box=box.SIMPLE_HEAVY,
        row_styles=["dim", ""],
    )
    table.add_column("ID", style="dim", width=10, no_wrap=True)
    table.add_column("Status", width=12)
    table.add_column("Title", min_width=20)
    table.add_column("Owner", width=16)
    table.add_column("Created", width=20)

    for task in snapshot.tasks:
        color = get_status_color(task.status)
        status_text = Text(sanitize_display_text(task.status))
        status_text.stylize(color)
        table.add_row(
            sanitize_display_text(task.id[:10]),
            status_text,
            sanitize_display_text(task.title),
            sanitize_display_text((task.owner or "(unassigned)").lower()),
            sanitize_display_text(task.created_timestamp),
        )
    return table


def _build_report_table(snapshot: StatusSnapshot) -> Table:
    """Builds a Rich Table of reports."""
    table = Table(
        title="Reports",
        box=box.SIMPLE_HEAVY,
        row_styles=["dim", ""],
    )
    table.add_column("ID", style="dim", width=10, no_wrap=True)
    table.add_column("Title", min_width=20)
    table.add_column("Author", width=16)
    table.add_column("Created", width=20)

    for report in snapshot.reports:
        table.add_row(
            sanitize_display_text(report.id[:10]),
            sanitize_display_text(report.title),
            sanitize_display_text(report.author),
            sanitize_display_text(report.created_timestamp),
        )
    return table


def _build_activity_section(snapshot: StatusSnapshot) -> Panel:
    """Builds a Rich Panel showing recent activity."""
    lines: list[str] = []
    for event in snapshot.activity_timeline:
        lines.append(
            f"  {sanitize_display_text(event.timestamp)}  "
            f"[dim]{sanitize_display_text(event.event_type)}[/dim]  "
            f"{sanitize_display_text(event.summary)}"
        )
    body = "\n".join(lines) if lines else "  (no recent activity)"
    return Panel(body, title="Recent Activity", border_style="dim")


def run_rich(args, cobots_config=None) -> None:
    """Renders a Rich-formatted static snapshot to the console."""
    snapshot = load_snapshot(
        workspace_path=getattr(args, "workspace_path", None),
        activity_count=getattr(args, "activity_count", 20),
        cobots_config=cobots_config,
    )

    console = Console()

    # Header panel.
    header_text = (
        f"[bold]Cobots Status[/bold]  "
        f"Workspace: [{CERULEAN}]"
        f"{sanitize_display_text(snapshot.workspace_name)}"
        f"[/{CERULEAN}]  "
        f"Snapshot: {sanitize_display_text(snapshot.snapshot_timestamp)}"
    )
    console.print(Panel(header_text, border_style=CERULEAN))

    # Summary.
    summary = _build_summary_text(snapshot)
    console.print(Panel(summary, title="Summary", border_style=CERULEAN))

    # Task table.
    console.print(_build_task_table(snapshot))

    # Report table.
    console.print(_build_report_table(snapshot))

    # Activity log.
    console.print(_build_activity_section(snapshot))
