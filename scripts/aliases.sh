#!/bin/bash
# aliases.sh - Shell functions for invoking the cobots CLI tools.
#
# Provides convenience commands for the six cobots CLIs (tasks, reports,
# knowledge, workspace, ntfy, tui). Each function locates the repository root
# automatically so the commands work regardless of the user's current directory.
#
# Usage:
#   source scripts/aliases.sh
#
# After sourcing, the following commands are available:
#   cobots-tasks     - Manage cobots tasks.
#   cobots-reports   - Generate cobots reports.
#   cobots-knowledge - Manage the cobots knowledge base.
#   cobots-workspace - Manage the cobots workspace.
#   cobots-ntfy      - Send notifications via ntfy.
#   cobots-tui       - View workspace status (interactive TUI or overview).
#
# All arguments are forwarded to the underlying Python CLI script. For example:
#   cobots-tasks list --status done


# Resolve the base directory that contains the skills/ tree from this script's
# location. Two layouts are supported:
#   - Installed: the aliases file sits flat in the install root (e.g.
#     ~/.copilot/aliases.sh) next to a skills/ subdirectory, so the base dir is
#     the file's own directory.
#   - Repo checkout: the aliases file lives in scripts/, so the base dir is one
#     level up (the repo root, where skills/ lives).
# Detect which layout applies by checking for a skills/ subdirectory.
__COBOTS_BASE_DIR="$(realpath "$(dirname "${BASH_SOURCE[0]}")")"
if [ ! -d "${__COBOTS_BASE_DIR}/skills" ]; then
    __COBOTS_BASE_DIR="$(realpath "${__COBOTS_BASE_DIR}/..")"
fi
__COBOTS_REPO_DIR="${__COBOTS_BASE_DIR}"

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

# Invokes the cobots knowledge CLI (skills/cobots_knowledge/knowledge-cli.py).
function cobots-knowledge()
{
    "${__COBOTS_PYTHON}" "${__COBOTS_REPO_DIR}/skills/cobots_knowledge/knowledge-cli.py" "$@"
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
