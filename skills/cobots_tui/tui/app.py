"""
app.py - CobotsStatusApp Textual application.

The main Textual App class for the interactive cobots TUI.
"""

import os
import subprocess
import sys
import warnings

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.reactive import reactive
from textual.widgets import Header, Footer, TabbedContent, TabPane, DataTable
from textual import work

from data import load_snapshot, StatusSnapshot, TaskData, ReportData
from security import validate_path_within_workspace, validate_editor


class CobotsStatusApp(App):
    """Interactive Textual TUI for viewing cobots workspace status."""

    TITLE = "Cobots TUI"
    CSS_PATH = "styles/status.tcss"
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
        Binding("e", "edit", "Edit"),
        Binding("v", "view_item", "View"),
        Binding("h", "previous_tab", "← Tab"),
        Binding("l", "next_tab", "Tab →"),
        Binding("tab", "focus_next", "Next Panel", show=False),
        Binding("shift+tab", "focus_previous", "Prev Panel", show=False),
    ]

    snapshot: reactive[StatusSnapshot | None] = reactive(None)

    def __init__(
        self,
        workspace_path: str | None = None,
        refresh_rate: int = 5,
        no_refresh: bool = False,
        activity_count: int = 20,
        cobots_config=None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.workspace_path = workspace_path
        self.refresh_rate = refresh_rate
        self.no_refresh = no_refresh
        self.activity_count = activity_count
        self._cobots_config = cobots_config
        self._refresh_timer = None
        self._workspace_root: str | None = None
        # Disable the sliding underline animation on TabbedContent tabs
        # so tab switches appear instant.
        self.animation_level = "none"

    @property
    def workspace_root(self) -> str:
        """Returns the resolved workspace root, falling back to cwd."""
        if self._workspace_root:
            return self._workspace_root
        if self.snapshot:
            return self.snapshot.workspace_root
        return os.getcwd()

    def compose(self) -> ComposeResult:
        yield Header()
        from tui.widgets.summary_bar import SummaryBar
        from tui.widgets.overview.overview_pane import OverviewPane
        from tui.widgets.task_table import TaskTable
        from tui.widgets.report_table import ReportTable
        from tui.widgets.activity_log import ActivityLog

        yield SummaryBar()
        with TabbedContent("Overview", "Tasks", "Reports"):
            with TabPane("Overview", id="tab-overview"):
                yield OverviewPane()
            with TabPane("Tasks", id="tab-tasks"):
                yield TaskTable()
            with TabPane("Reports", id="tab-reports"):
                yield ReportTable()
        yield ActivityLog()
        yield Footer()

    def on_mount(self) -> None:
        """Performs the initial data load and sets up auto-refresh."""
        self._do_refresh()
        if not self.no_refresh and self.refresh_rate > 0:
            self._refresh_timer = self.set_interval(
                self.refresh_rate, self._do_refresh
            )
        # Hide ActivityLog when terminal height is 40 or below.
        from tui.widgets.activity_log import ActivityLog
        try:
            activity_log = self.query_one(ActivityLog)
            activity_log.display = self.size.height > 40
        except Exception:
            pass
        # Auto-focus the DataTable in the active tab so arrow keys work
        # immediately without requiring the user to click or Tab first.
        self.call_later(self._focus_active_table)

    @work(exclusive=True, thread=True)
    def _do_refresh(self) -> None:
        """Worker that loads the snapshot in a background thread."""
        snap = load_snapshot(
            workspace_path=self.workspace_path,
            activity_count=self.activity_count,
            cobots_config=self._cobots_config,
        )
        self._workspace_root = snap.workspace_root
        self.call_from_thread(self._apply_snapshot, snap)

    def _apply_snapshot(self, snap: StatusSnapshot) -> None:
        """Applies a new snapshot on the main thread."""
        self.snapshot = snap
        self.sub_title = snap.workspace_name

    def watch_snapshot(self, snap: StatusSnapshot | None) -> None:
        """Called whenever the reactive snapshot property changes."""
        if snap is None:
            return
        from textual.css.query import NoMatches
        from tui.widgets.overview.overview_pane import OverviewPane
        from tui.widgets.summary_bar import SummaryBar
        from tui.widgets.task_table import TaskTable
        from tui.widgets.report_table import ReportTable
        from tui.widgets.activity_log import ActivityLog

        try:
            self.query_one(OverviewPane).update_from_snapshot(snap)
        except NoMatches:
            pass
        except Exception as exc:
            warnings.warn(f"Failed to update OverviewPane: {exc}")
        try:
            self.query_one(SummaryBar).update_from_snapshot(snap)
        except NoMatches:
            pass
        except Exception as exc:
            warnings.warn(f"Failed to update SummaryBar: {exc}")
        try:
            self.query_one(TaskTable).update_from_snapshot(snap)
        except NoMatches:
            pass
        except Exception as exc:
            warnings.warn(f"Failed to update TaskTable: {exc}")
        try:
            self.query_one(ReportTable).update_from_snapshot(snap)
        except NoMatches:
            pass
        except Exception as exc:
            warnings.warn(f"Failed to update ReportTable: {exc}")
        try:
            self.query_one(ActivityLog).update_from_snapshot(snap)
        except NoMatches:
            pass
        except Exception as exc:
            warnings.warn(f"Failed to update ActivityLog: {exc}")

    def action_refresh(self) -> None:
        """Manually trigger a data refresh (bound to 'r' key)."""
        self._do_refresh()

    # ------------------------------------------------------------------
    # Focus management
    # ------------------------------------------------------------------

    def _focus_active_table(self) -> None:
        """Focus the first DataTable inside the currently active tab pane.

        This ensures arrow keys (and vim ``j``/``k``) work immediately
        after the app starts and after every tab switch.  The Overview
        tab has no DataTable, so focus falls back to its OverviewPane.
        """
        try:
            tc = self.query_one(TabbedContent)
            pane = tc.get_pane(tc.active)
            try:
                table = pane.query_one(DataTable)
                table.focus()
            except Exception:
                # Overview tab has no DataTable; focus the pane
                # (OverviewPane) so the user can scroll with arrow keys.
                from tui.widgets.overview.overview_pane import OverviewPane
                try:
                    overview = pane.query_one(OverviewPane)
                    overview.focus()
                except Exception:
                    pass
        except Exception:
            pass

    def on_resize(self, event) -> None:
        """Hide ActivityLog when terminal height is 40 or below."""
        from tui.widgets.activity_log import ActivityLog
        try:
            activity_log = self.query_one(ActivityLog)
            activity_log.display = event.size.height > 40
        except Exception:
            pass

    def on_tabbed_content_tab_activated(
        self, event: TabbedContent.TabActivated
    ) -> None:
        """Auto-focus the DataTable when the user switches tabs."""
        self.call_later(self._focus_active_table)

    # ------------------------------------------------------------------
    # Tab switching (vim h / l)
    # ------------------------------------------------------------------

    def action_previous_tab(self) -> None:
        """Switch to the previous tab (bound to 'h' key)."""
        try:
            tc = self.query_one(TabbedContent)
            pane_ids = [pane.id for pane in tc.query(TabPane) if pane.id]
            if not pane_ids:
                return
            current = tc.active
            idx = pane_ids.index(current) if current in pane_ids else 0
            tc.active = pane_ids[(idx - 1) % len(pane_ids)]
        except Exception:
            pass

    def action_next_tab(self) -> None:
        """Switch to the next tab (bound to 'l' key)."""
        try:
            tc = self.query_one(TabbedContent)
            pane_ids = [pane.id for pane in tc.query(TabPane) if pane.id]
            if not pane_ids:
                return
            current = tc.active
            idx = pane_ids.index(current) if current in pane_ids else 0
            tc.active = pane_ids[(idx + 1) % len(pane_ids)]
        except Exception:
            pass

    def _get_selected_item(self) -> TaskData | ReportData | None:
        """Returns the currently selected task or report based on active tab."""
        if self.snapshot is None:
            return None

        try:
            tabs = self.query_one(TabbedContent)
            active_id = tabs.active
        except Exception:
            return None

        if active_id == "tab-tasks":
            from tui.widgets.task_table import TaskTable
            try:
                table = self.query_one(TaskTable)
                return table.get_selected_item(self.snapshot)
            except Exception:
                return None
        elif active_id == "tab-reports":
            from tui.widgets.report_table import ReportTable
            try:
                table = self.query_one(ReportTable)
                return table.get_selected_item(self.snapshot)
            except Exception:
                return None
        return None

    def action_edit(self) -> None:
        """Edit the selected item in $EDITOR (bound to 'e' key)."""
        item = self._get_selected_item()
        if item is None:
            self.notify("No item selected", severity="warning")
            return

        editor = os.environ.get("EDITOR", "").strip()
        if not editor:
            self.notify("EDITOR environment variable not set", severity="error")
            return

        editor_parts = validate_editor(editor)
        if editor_parts is None:
            self.notify(f"Editor not found: {editor}", severity="error")
            return

        try:
            validated_path = validate_path_within_workspace(
                item.path, self.workspace_root
            )
        except ValueError as exc:
            self.notify(str(exc), severity="error")
            return

        if self._refresh_timer:
            self._refresh_timer.pause()
        try:
            with self.suspend():
                result = subprocess.run(editor_parts + [validated_path])
            if result.returncode != 0:
                self.notify(
                    f"{editor_parts[0]} exited with code {result.returncode}",
                    severity="warning",
                )
        except (FileNotFoundError, OSError) as exc:
            self.notify(f"Failed to launch editor: {exc}", severity="error")
        finally:
            if self._refresh_timer:
                self._refresh_timer.resume()
            self.action_refresh()

    def action_view_item(self) -> None:
        """View the selected item in $PAGER (bound to 'v' key)."""
        item = self._get_selected_item()
        if item is None:
            self.notify("No item selected", severity="warning")
            return

        pager = os.environ.get("PAGER", "less").strip()
        pager_parts = validate_editor(pager)
        if pager_parts is None:
            self.notify(f"Pager not found: {pager}", severity="error")
            return

        try:
            validated_path = validate_path_within_workspace(
                item.path, self.workspace_root
            )
        except ValueError as exc:
            self.notify(str(exc), severity="error")
            return

        if self._refresh_timer:
            self._refresh_timer.pause()
        try:
            with self.suspend():
                result = subprocess.run(pager_parts + [validated_path])
            if result.returncode != 0:
                self.notify(
                    f"{pager_parts[0]} exited with code {result.returncode}",
                    severity="warning",
                )
        except (FileNotFoundError, OSError) as exc:
            self.notify(f"Failed to launch pager: {exc}", severity="error")
        finally:
            if self._refresh_timer:
                self._refresh_timer.resume()
            self.action_refresh()
