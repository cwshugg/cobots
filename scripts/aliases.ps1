# aliases.ps1 - PowerShell functions for invoking the cobots CLI tools.
#
# Provides convenience commands for the six cobots CLIs (tasks, reports,
# knowledge, workspace, ntfy, tui). Each function locates the repository root
# automatically so the commands work regardless of the user's current directory.
#
# Usage:
#   . scripts/aliases.ps1
#
# After loading, the following commands are available:
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
#     ~/.copilot/aliases.ps1) next to a skills/ subdirectory, so the base dir is
#     the file's own directory.
#   - Repo checkout: the aliases file lives in scripts/, so the base dir is one
#     level up (the repo root, where skills/ lives).
# Detect which layout applies by checking for a skills/ subdirectory.
$script:__CobotBaseDir = Split-Path -Parent ((Resolve-Path $MyInvocation.MyCommand.Path).ProviderPath)
if (-not (Test-Path (Join-Path $script:__CobotBaseDir "skills") -PathType Container)) {
    $script:__CobotBaseDir = Split-Path -Parent $script:__CobotBaseDir
}
$script:__CobotRepoDir = $script:__CobotBaseDir

# Path to the Python interpreter inside the shared virtual environment.
$script:__CobotPython = Join-Path $script:__CobotRepoDir "skills\.venv\Scripts\python.exe"


# Invokes the cobots tasks CLI (skills/cobots_tasks/tasks-cli.py).
function cobots-tasks {
    $script_path = Join-Path $script:__CobotRepoDir "skills\cobots_tasks\tasks-cli.py"
    & $script:__CobotPython $script_path @args
}

# Invokes the cobots reports CLI (skills/cobots_reports/reports-cli.py).
function cobots-reports {
    $script_path = Join-Path $script:__CobotRepoDir "skills\cobots_reports\reports-cli.py"
    & $script:__CobotPython $script_path @args
}

# Invokes the cobots knowledge CLI (skills/cobots_knowledge/knowledge-cli.py).
function cobots-knowledge {
    $script_path = Join-Path $script:__CobotRepoDir "skills\cobots_knowledge\knowledge-cli.py"
    & $script:__CobotPython $script_path @args
}

# Invokes the cobots workspace CLI (skills/cobots_workspace/workspace-cli.py).
function cobots-workspace {
    $script_path = Join-Path $script:__CobotRepoDir "skills\cobots_workspace\workspace-cli.py"
    & $script:__CobotPython $script_path @args
}

# Invokes the cobots ntfy CLI (skills/cobots_ntfy/ntfy-cli.py).
function cobots-ntfy {
    $script_path = Join-Path $script:__CobotRepoDir "skills\cobots_ntfy\ntfy-cli.py"
    & $script:__CobotPython $script_path @args
}

# Invokes the cobots TUI (skills/cobots_tui/cobots-tui.py).
function cobots-tui {
    $script_path = Join-Path $script:__CobotRepoDir "skills\cobots_tui\cobots-tui.py"
    & $script:__CobotPython $script_path @args
}
