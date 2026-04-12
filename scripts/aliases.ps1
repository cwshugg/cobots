# aliases.ps1 - PowerShell functions for invoking the cobots CLI tools.
#
# Provides convenience commands for the three cobots CLIs (tasks, reports,
# workspace). Each function locates the repository root automatically so the
# commands work regardless of the user's current directory.
#
# Usage:
#   . scripts/aliases.ps1
#
# After loading, the following commands are available:
#   cobots-tasks     - Manage cobots tasks.
#   cobots-reports   - Generate cobots reports.
#   cobots-workspace - Manage the cobots workspace.
#
# All arguments are forwarded to the underlying Python CLI script. For example:
#   cobots-tasks list --status done


# Resolve the repository root from this script's location.
$script:__CobotRepoDir = Split-Path -Parent (Resolve-Path $MyInvocation.MyCommand.Path).ProviderPath

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

# Invokes the cobots workspace CLI (skills/cobots_workspace/workspace-cli.py).
function cobots-workspace {
    $script_path = Join-Path $script:__CobotRepoDir "skills\cobots_workspace\workspace-cli.py"
    & $script:__CobotPython $script_path @args
}
