---
name: cobots-tui
description: CLI for interactively viewing and monitoring cobots workspace status.
---

# cobots-tui

A CLI skill for viewing the current status of a cobots workspace.

## Description

The cobots TUI skill provides two modes for inspecting workspace
state — tasks, reports, activity timeline, and summary statistics:

1. **TUI** (default) — Full interactive Textual-based TUI with
   auto-refresh, sortable DataTables for tasks and reports, tabbed navigation,
   keybindings for viewing/editing items, and a live activity timeline.
2. **`--show-overview`** — Static Rich-formatted terminal output for a
   quick-glance snapshot. No interactivity required; prints and exits.

## Configuration

The `status` section of `cobots-config.yaml` controls default behavior:

```yaml
status:
  refresh_rate: 5          # seconds between auto-refresh cycles (2-3600)
  activity_count: 20       # number of activity events to display (1-100)
```

| Field            | Default | Bounds    | Description                          |
|------------------|---------|-----------|--------------------------------------|
| `refresh_rate`   | `5`     | 2–3600    | Seconds between auto-refresh cycles  |
| `activity_count` | `20`    | 1–100     | Number of activity events to display |

All numeric values are clamped to their bounds — out-of-range values are silently
adjusted rather than rejected.

## Usage

```bash
# Interactive TUI (default).
python3 cobots-tui.py

# Static Rich-formatted overview snapshot.
python3 cobots-tui.py --show-overview

# Custom refresh rate and activity count.
python3 cobots-tui.py --refresh-rate 10 --activity-count 50

# Disable auto-refresh in TUI mode.
python3 cobots-tui.py --no-refresh

# Explicit workspace path.
python3 cobots-tui.py --workspace-path /path/to/.cobots
```

## Arguments

| Flag               | Type   | Default      | Description                            |
|--------------------|--------|--------------|----------------------------------------|
| `--show-overview`  | flag   | false        | Print static Rich overview and exit    |
| `--refresh-rate`   | int    | from config  | Auto-refresh interval in seconds       |
| `--activity-count` | int    | from config  | Number of activity events              |
| `--no-refresh`     | flag   | false        | Disable auto-refresh (TUI only)        |
| `--workspace-path` | str    | auto-resolve | Explicit path to `.cobots/` directory  |

## TUI Mode

The interactive TUI is built on the [Textual](https://textual.textualize.io/) framework.
It displays:

* **Summary bar** — Aggregate task counts by status (color-coded), total report count,
  and the last refresh timestamp.
* **Tabbed content** — Two tabs: `Tasks` and `Reports`, each containing a sortable
  DataTable with row-level cursor navigation.
* **Activity log** — A scrollable timeline of recent workspace events (task creation,
  task discussion updates, report creation), sorted newest-first.
* **Header and footer** — Standard Textual chrome showing the app title, workspace name,
  and available keybindings.

Tasks and reports are sorted newest-first by `created_timestamp`. The TUI
auto-refreshes on a configurable interval (default 5 seconds). Data is loaded
in a background thread so the interface remains responsive during refresh cycles.
The cursor row position is preserved across auto-refresh cycles — if the selected
row index exceeds the new row count after a refresh, it is clamped to the last row.

Tab switching is instant (no sliding underline animation).

Pressing `e` opens the selected task or report in `$EDITOR`. Pressing `v` opens it in
`$PAGER` (defaults to `less`). Pressing `Enter` on a report row pushes a detail screen
showing the full report body. Press `Escape` or `q` to return from the detail screen.

If the TUI is launched but stdout is not a TTY, the skill automatically falls back to
`--show-overview` mode with a warning.

## Overview Mode (`--show-overview`)

Renders a static, formatted snapshot to the terminal using the
[Rich](https://rich.readthedocs.io/) library. Output includes:

* A header panel with workspace name and snapshot timestamp
* A summary panel with task counts by status
* A task table (ID, status, title, owner, created) — sorted newest-first
* A report table (ID, title, author, created) — sorted newest-first
* A recent activity panel

This mode is non-interactive and exits immediately after printing. Useful for a quick
glance or for capturing formatted output. Tasks and reports are sorted newest-first
by `created_timestamp`, matching the TUI sort order.

## Color Scheme

The TUI uses a custom color palette:

| Name           | Hex       | Usage                                         |
|----------------|-----------|-----------------------------------------------|
| Warm Charcoal  | `#2D2B28` | Background (dark mode)                        |
| Parchment      | `#F5ECD7` | Primary text                                  |
| Cerulean       | `#227C9D` | Accent 1 — links, cool tones, done tasks      |
| Apricot Cream  | `#FFCB77` | Accent 2 — warm highlights, pending tasks     |
| Grapefruit     | `#FE6D73` | Accent 3 — alerts, emphasis, underway tasks   |
| Dim Parchment  | `#8A8478` | Muted text — abandoned tasks                  |

### Status Color Mappings

Task statuses are color-coded throughout the TUI and overview output:

| Status      | Color         | Hex       |
|-------------|---------------|-----------|
| `pending`   | Apricot Cream | `#FFCB77` |
| `underway`  | Grapefruit    | `#FE6D73` |
| `done`      | Cerulean      | `#227C9D` |
| `abandoned` | Dim Parchment | `#8A8478` |

## TUI Keybindings

### General

| Key          | Action                                              |
|--------------|-----------------------------------------------------|
| `q`          | Quit the application                                |
| `r`          | Manually refresh data                               |
| `e`          | Edit the selected item in `$EDITOR`                 |
| `v`          | View the selected item in `$PAGER` (default: less)  |
| `Enter`      | Open report detail screen (Reports tab)             |
| `Escape`     | Return from detail screen                           |

### Navigation

| Key          | Action                      |
|--------------|-----------------------------|
| `j` / `↓`   | Move cursor down            |
| `k` / `↑`   | Move cursor up              |
| `g`          | Jump to first row           |
| `G`          | Jump to last row            |
| `h`          | Switch to previous tab      |
| `l`          | Switch to next tab          |
| `Tab`        | Focus next panel            |
| `Shift+Tab`  | Focus previous panel        |

Arrow keys, Page Up/Down, and Home/End also work for navigation alongside the
vim-style bindings.

## File Structure

```
skills/cobots_tui/
├── SKILL.md                        # This file
├── __init__.py                     # Package init
├── cobots-tui.py                   # CLI entry point
├── config.py                       # StatusConfig loader
├── constants.py                    # Shared constants (colors, palette)
├── data.py                         # Data layer — dataclasses, parsing, snapshots
├── security.py                     # Path validation, text sanitization
├── modes/
│   ├── __init__.py                 # Package init
│   ├── tui_mode.py                 # Launches the Textual app
│   └── rich_mode.py                # Rich-formatted static output
├── tui/
│   ├── __init__.py                 # Package init
│   ├── app.py                      # CobotsStatusApp (main Textual App)
│   ├── screens/
│   │   ├── __init__.py             # Package init
│   │   └── report_detail_screen.py # Pushed screen for report content
│   ├── widgets/
│   │   ├── __init__.py             # Package init
│   │   ├── vim_nav_table.py        # DataTable with vim keybindings
│   │   ├── task_table.py           # Task DataTable widget
│   │   ├── report_table.py         # Report DataTable widget
│   │   ├── summary_bar.py          # Aggregate statistics bar
│   │   ├── activity_log.py         # Recent activity timeline
│   │   ├── snapshot_widget.py      # Base widget with snapshot caching
│   │   └── overview/
│   │       ├── __init__.py         # Package init
│   │       ├── _chart_utils.py     # Shared chart rendering helpers
│   │       ├── overview_pane.py    # Overview tab grid container
│   │       ├── kpi_panel.py        # KPI digits and completion bar
│   │       ├── status_chart.py     # Horizontal bar chart by status
│   │       ├── owner_chart.py      # Horizontal bar chart by owner
│   │       ├── active_tasks_list.py  # Active tasks summary list
│   │       ├── recent_reports_list.py # Recent reports summary list
│   │       └── activity_feed.py    # Activity feed widget
│   └── styles/
│       └── status.tcss             # Textual CSS stylesheet
└── tests/
    ├── __init__.py                 # Package init
    ├── conftest.py                 # Pytest configuration and fixtures
    ├── helpers.py                  # Shared test fixtures and factory functions
    ├── test_data.py
    ├── test_config.py
    ├── test_security.py
    ├── test_rich_mode.py
    ├── test_tui.py
    ├── test_overview.py
    └── test_mode_e2e.py
```

## Security Considerations

* **Path containment** — All file paths are validated via `validate_path_within_workspace()`,
  which resolves symlinks with `os.path.realpath()` before checking that the path falls
  within the workspace boundary. This prevents path traversal attacks.
* **Markup sanitization** — All file-derived strings are passed through `sanitize_display_text()`
  (which calls `rich.markup.escape()`) before rendering in Rich or Textual widgets. This
  prevents markup injection from task/report content.
* **Editor validation** — The `$EDITOR` and `$PAGER` environment variables are parsed with
  `shlex.split()` and validated with `shutil.which()` before use. Subprocess calls use
  argument lists (`shell=False`), never string interpolation.
* **File size limits** — Files larger than 1 MB are skipped during snapshot loading and
  rejected when opening the report detail screen.
* **No `os.system()`** — All external process execution uses `subprocess.run()` with
  explicit argument lists.

## Return Codes

| Code | Meaning                                            |
|------|----------------------------------------------------|
| 0    | Success                                            |
| 1    | Error (missing workspace, invalid args, etc.)      |

## Library Usage

Other skills and agents can import and use the status data layer directly
instead of spawning a subprocess.

### Quick Start

```python
from cobots_tui.data import load_snapshot

# Load a full workspace snapshot.
snapshot = load_snapshot(workspace_path="/path/to/.cobots", activity_count=10)

print(snapshot.workspace_name)        # "cobots"
print(len(snapshot.tasks))            # 5
print(snapshot.status_counts_dict())  # {"done": 2, "underway": 2, "pending": 1}
```

### `load_snapshot()` Parameters

| Parameter        | Type                   | Default | Description                                              |
|------------------|------------------------|---------|----------------------------------------------------------|
| `workspace_path` | `str \| None`          | `None`  | Path to `.cobots/` directory. Auto-resolved if `None`.   |
| `activity_count` | `int`                  | `20`    | Maximum number of activity events to include.            |
| `cobots_config`  | `CobotsConfig \| None` | `None`  | Pre-loaded config to skip redundant disk I/O.            |

### `StatusSnapshot` Fields

The returned `StatusSnapshot` is a frozen dataclass with the following fields:

| Field                   | Type                        | Description                                  |
|-------------------------|-----------------------------|----------------------------------------------|
| `workspace_name`        | `str`                       | Name of the workspace.                       |
| `workspace_root`        | `str`                       | Absolute path to the `.cobots/` directory.   |
| `tasks`                 | `tuple[TaskData, ...]`      | All parsed tasks.                            |
| `reports`               | `tuple[ReportData, ...]`    | All parsed reports.                          |
| `task_counts_by_status` | `MappingProxyType`          | Task counts keyed by status string.          |
| `task_counts_by_owner`  | `MappingProxyType`          | Task counts keyed by owner name.             |
| `report_count`          | `int`                       | Total number of reports.                     |
| `activity_timeline`     | `tuple[ActivityEvent, ...]` | Recent activity events, newest-first.        |
| `snapshot_timestamp`    | `str`                       | UTC timestamp when the snapshot was created. |

Helper methods `status_counts_dict()` and `owner_counts_dict()` convert the
`MappingProxyType` fields to plain `dict` for JSON serialization.

## Troubleshooting

* **"TUI mode requires a TTY"** — The TUI was requested but stdout is not a terminal.
  The skill falls back to overview mode automatically. Use `--show-overview` explicitly
  when running in non-interactive environments.
* **"The 'textual' package is required for TUI mode"** — The `textual` dependency is
  not installed. Install it with `pip install 'textual>=1.0,<2.0'`.
* **"EDITOR environment variable not set"** — The `e` key was pressed but `$EDITOR` is
  not configured. Set it in your shell (e.g. `export EDITOR=vim`).
* **"Editor not found: …"** — The `$EDITOR` value does not resolve to an executable on
  `$PATH`. Verify the editor is installed and accessible.
* **"Path escapes workspace boundary"** — A file path resolved to a location outside the
  `.cobots/` workspace. This is a security check — the file will not be opened.
* **No data shown** — Ensure you are running from within a project that has an initialized
  cobots workspace (`.cobots/` directory). Use `--workspace-path` to specify the path
  explicitly if auto-resolution fails.
