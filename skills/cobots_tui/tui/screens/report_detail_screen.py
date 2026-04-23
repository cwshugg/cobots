"""
report_detail_screen.py - Pushed screen for viewing a single report body.

Displays the full content of a report file in a scrollable view with
sanitized text.
"""

import os

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Header, Footer, Static
from textual.containers import ScrollableContainer

from data import MAX_FILE_SIZE
from security import sanitize_display_text, validate_path_within_workspace
from cobots_lib.parsing import parse_frontmatter


class ReportDetailScreen(Screen):
    """Full-screen view of a single report body."""

    BINDINGS = [
        Binding("escape", "dismiss", "Back"),
        Binding("q", "dismiss", "Back"),
    ]

    def __init__(
        self,
        report_path: str,
        report_title: str = "",
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.report_path = report_path
        self.report_title = report_title

    def compose(self) -> ComposeResult:
        yield Header()
        with ScrollableContainer():
            yield Static(id="report-body")
        yield Footer()

    def on_mount(self) -> None:
        """Load and display the report content."""
        self.title = f"Report: {sanitize_display_text(self.report_title)}"
        # Re-validate the path at read time (defense-in-depth).
        # The path was validated when the snapshot was built, but time may
        # have passed between snapshot creation and the user opening this
        # detail screen.  Re-validation ensures the security invariant
        # that every file read is explicitly checked at read time.
        try:
            validated = validate_path_within_workspace(
                self.report_path, self.app.workspace_root
            )
        except ValueError:
            self.query_one("#report-body", Static).update(
                sanitize_display_text(
                    "(Report path is outside workspace boundary)"
                )
            )
            return

        # Enforce the same file-size guard used by data.py when scanning
        # workspace files.  Protects against files that grew between the
        # initial snapshot scan and the moment the user opens the detail.
        try:
            size = os.path.getsize(validated)
        except OSError:
            body = "(Could not read report file)"
            self.query_one("#report-body", Static).update(
                sanitize_display_text(body)
            )
            return

        if size > MAX_FILE_SIZE:
            body = (
                f"(Report file too large to display: "
                f"{size:,} bytes exceeds {MAX_FILE_SIZE:,} byte limit)"
            )
            self.query_one("#report-body", Static).update(
                sanitize_display_text(body)
            )
            return

        try:
            _, body = parse_frontmatter(validated)
        except OSError:
            body = "(Could not read report file)"
        safe_body = sanitize_display_text(body)
        self.query_one("#report-body", Static).update(safe_body)
