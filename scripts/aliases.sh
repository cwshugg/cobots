#!/bin/bash
# aliases.sh - Shell functions for invoking the cobots CLI tools.
#
# Provides convenience commands for the five cobots CLIs (tasks, reports,
# workspace, ntfy, tui). Each function locates the repository root
# automatically so the commands work regardless of the user's current directory.
#
# Usage:
#   source scripts/aliases.sh
#
# After sourcing, the following commands are available:
#   cobots-tasks     - Manage cobots tasks.
#   cobots-reports   - Generate cobots reports.
#   cobots-workspace - Manage the cobots workspace.
#   cobots-ntfy      - Send notifications via ntfy.
#   cobots-tui       - View workspace status (interactive TUI or overview).
#
# All arguments are forwarded to the underlying Python CLI script. For example:
#   cobots-tasks list --status done


# Resolve the repository root from this script's location.
# The script lives in scripts/, so we go up one level to reach the repo root.
__COBOTS_REPO_DIR="$(realpath "$(dirname "${BASH_SOURCE[0]}")/..")"

# Path to the Python interpreter inside the shared virtual environment.
__COBOTS_PYTHON="${__COBOTS_REPO_DIR}/skills/.venv/bin/python3"


# Invokes the cobots tasks CLI (skills/cobots_tasks/tasks-cli.py).
function cobots-tasks()
{
    "${__COBOTS_PYTHON}" "${__COBOTS_REPO_DIR}/skills/cobots_tasks/tasks-cli.py" "$@"
}

# Invokes the cobots reports CLI (skills/cobots_reports/reports-cli.py).
function cobots-reports()
{
    "${__COBOTS_PYTHON}" "${__COBOTS_REPO_DIR}/skills/cobots_reports/reports-cli.py" "$@"
}

# Invokes the cobots workspace CLI (skills/cobots_workspace/workspace-cli.py).
function cobots-workspace()
{
    "${__COBOTS_PYTHON}" "${__COBOTS_REPO_DIR}/skills/cobots_workspace/workspace-cli.py" "$@"
}

# Invokes the cobots ntfy CLI (skills/cobots_ntfy/ntfy-cli.py).
function cobots-ntfy()
{
    "${__COBOTS_PYTHON}" "${__COBOTS_REPO_DIR}/skills/cobots_ntfy/ntfy-cli.py" "$@"
}

# Invokes the cobots TUI (skills/cobots_tui/cobots-tui.py).
function cobots-tui()
{
    "${__COBOTS_PYTHON}" "${__COBOTS_REPO_DIR}/skills/cobots_tui/cobots-tui.py" "$@"
}
