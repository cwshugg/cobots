# install.ps1 - Installs the AI tools in this repository to the user
# environment. This is the PowerShell equivalent of `install.sh`.
#
# Copies agent files, skill files, and instruction files from the repository
# into the specified install path (default: ~/.copilot).
#
# Usage:
#   .\install.ps1 -h
#   .\install.ps1 -i "C:\Users\me\.copilot"

# Stop on any error so failures don't go unnoticed.
$ErrorActionPreference = "Stop"

# Resolve the absolute path to this script's directory and the repo root.
$script:ScriptDir = Split-Path -Parent (Resolve-Path $MyInvocation.MyCommand.Path).ProviderPath
$script:RepoDir = Split-Path -Parent $script:ScriptDir

# Exit codes used by all functions.
$script:R_SUCCESS = 0
$script:R_FAILURE = 1

# Default installation target directory.
$script:DefaultInstallPath = Join-Path $env:USERPROFILE ".copilot"


# ================================= Logging ================================== #
# Writes a log message to the console.
function __log {
    param([string]$level, [string]$message)
    Write-Host "[$level] $message"
}

# Convenience wrapper for info-level log messages.
function __log_info {
    param([string]$message)
    __log -level "INFO" -message $message
}

# Convenience wrapper for error-level log messages.
function __log_error {
    param([string]$message)
    __log -level "ERROR" -message $message
}


# ============================ Main Installation ============================= #
# Finds all agent markdown files (matching "*.*agent*.md") in the repo's
# `agents/` directory and copies them into the install path, preserving
# relative directory structure.
function __install_agents {
    param([string]$install_path)

    # Ensure the destination agents directory exists.
    $agents_dst = Join-Path $install_path "agents"
    if (-not (Test-Path $agents_dst)) {
        New-Item -ItemType Directory -Path $agents_dst -Force | Out-Null
    }

    # Verify the source directory exists in the repo.
    $agents_src = Join-Path $script:RepoDir "agents"
    if (-not (Test-Path $agents_src)) {
        __log_error "Agents source directory not found: $agents_src"
        return $script:R_FAILURE
    }

    # Resolve to a full path so substring operations against FullName work.
    $agents_src = (Resolve-Path $agents_src).ProviderPath

    # Copy each agent file, creating subdirectories as needed.
    $agent_count = 0
    $agent_files = Get-ChildItem -Path $agents_src -Recurse -File -Filter "*.*agent*.md"
    foreach ($agent_file in $agent_files) {
        $agent_rel = $agent_file.FullName.Substring($agents_src.Length + 1)
        $agent_dst = Join-Path $agents_dst $agent_rel

        $agent_dst_dir = Split-Path -Parent $agent_dst
        if (-not (Test-Path $agent_dst_dir)) {
            New-Item -ItemType Directory -Path $agent_dst_dir -Force | Out-Null
        }

        Copy-Item -Path $agent_file.FullName -Destination $agent_dst -Force
        __log_info "Installed agent `"$($agent_file.Name)`" to: $agent_dst"
        $agent_count++
    }

    __log_info "Installed $agent_count agents to: $agents_dst"
    return $script:R_SUCCESS
}

# Finds all skill-related files (SKILL.md descriptors and .py implementations)
# in the repo's `skills/` directory and copies them into the install path,
# preserving relative directory structure.
function __install_skills {
    param([string]$install_path)

    # Ensure the destination skills directory exists.
    $skills_dst = Join-Path $install_path "skills"
    if (-not (Test-Path $skills_dst)) {
        New-Item -ItemType Directory -Path $skills_dst -Force | Out-Null
    }

    # Verify the source directory exists in the repo.
    $skills_src = Join-Path $script:RepoDir "skills"
    if (-not (Test-Path $skills_src)) {
        __log_error "Skills source directory not found: $skills_src"
        return $script:R_FAILURE
    }

    # Resolve to a full path so substring operations against FullName work.
    $skills_src = (Resolve-Path $skills_src).ProviderPath

    # Copy each skill file. We count SKILL.md files separately so the summary
    # reflects the number of skills (not individual files).
    $skill_count = 0
    $skill_files = Get-ChildItem -Path $skills_src -Recurse -File |
        Where-Object {
            $_.Name -like "*SKILL*.md" -or
            $_.Extension -eq ".py"
        }

    foreach ($skill_file in $skill_files) {
        $skill_rel = $skill_file.FullName.Substring($skills_src.Length + 1)
        $skill_dst = Join-Path $skills_dst $skill_rel

        $skill_dst_dir = Split-Path -Parent $skill_dst
        if (-not (Test-Path $skill_dst_dir)) {
            New-Item -ItemType Directory -Path $skill_dst_dir -Force | Out-Null
        }

        Copy-Item -Path $skill_file.FullName -Destination $skill_dst -Force
        __log_info "Installed skill file `"$skill_rel`" to: $skill_dst"

        # Only count SKILL.md files towards the skill total.
        if ($skill_file.Name -like "*SKILL*.md") {
            $skill_count++
        }
    }

    __log_info "Installed $skill_count skills to: $skills_dst"
    return $script:R_SUCCESS
}

# Finds all instruction markdown files (matching "*.*instruction*.md") in the
# repo's `instructions/` directory and copies them into the install path,
# preserving relative directory structure.
function __install_instructions {
    param([string]$install_path)

    # Ensure the destination instructions directory exists.
    $insts_dst = Join-Path $install_path "instructions"
    if (-not (Test-Path $insts_dst)) {
        New-Item -ItemType Directory -Path $insts_dst -Force | Out-Null
    }

    # Verify the source directory exists in the repo.
    $insts_src = Join-Path $script:RepoDir "instructions"
    if (-not (Test-Path $insts_src)) {
        __log_error "Instructions source directory not found: $insts_src"
        return $script:R_FAILURE
    }

    # Resolve to a full path so substring operations against FullName work.
    $insts_src = (Resolve-Path $insts_src).ProviderPath

    # Copy each instruction file, creating subdirectories as needed.
    $inst_count = 0
    $inst_files = Get-ChildItem -Path $insts_src -Recurse -File -Filter "*.*instruction*.md"
    foreach ($inst_file in $inst_files) {
        $inst_rel = $inst_file.FullName.Substring($insts_src.Length + 1)
        $inst_dst = Join-Path $insts_dst $inst_rel

        $inst_dst_dir = Split-Path -Parent $inst_dst
        if (-not (Test-Path $inst_dst_dir)) {
            New-Item -ItemType Directory -Path $inst_dst_dir -Force | Out-Null
        }

        Copy-Item -Path $inst_file.FullName -Destination $inst_dst -Force
        __log_info "Installed instruction `"$($inst_file.Name)`" to: $inst_dst"
        $inst_count++
    }

    __log_info "Installed $inst_count instructions to: $insts_dst"
    return $script:R_SUCCESS
}

# Prints the usage/help text for this script.
function __show_usage {
    Write-Host "Usage: install.ps1 [OPTIONS]"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -h, -Help                 Show this help message and exit."
    Write-Host "  -i, -InstallPath PATH     Path to install the tools (default: `"$script:DefaultInstallPath`")."
}


# ================================== Main ==================================== #
# Main entry point. Parses arguments, then installs agents, skills, and
# instructions in sequence. Returns a non-zero exit code on failure.
function __main {
    param(
        [Alias("h")]
        [switch]$help,

        [Alias("i")]
        [string]$install_path
    )

    if ($help) {
        __show_usage
        return $script:R_SUCCESS
    }

    # Fall back to the default install path if none was provided.
    $target_path = if ($install_path) { $install_path } else { $script:DefaultInstallPath }

    __log_info "Installing tools to: $target_path"

    # Install each component in order; bail on first failure.
    $result = __install_agents -install_path $target_path
    if ($result -ne $script:R_SUCCESS) {
        __log_error "Failed to install agents."
        return $result
    }

    $result = __install_skills -install_path $target_path
    if ($result -ne $script:R_SUCCESS) {
        __log_error "Failed to install skills."
        return $result
    }

    $result = __install_instructions -install_path $target_path
    if ($result -ne $script:R_SUCCESS) {
        __log_error "Failed to install instructions."
        return $result
    }

    return $script:R_SUCCESS
}

# Invoke `__main` with all script arguments and exit with its return value.
$main_retval = __main @args
exit $main_retval

