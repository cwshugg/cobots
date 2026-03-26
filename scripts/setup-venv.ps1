# setup-venv.ps1 - Creates a Python virtual environment for cobots skills and
# installs dependencies from requirements.txt.
#
# Usage:
#   .\setup-venv.ps1 [OPTIONS]
#
# The virtual environment is created under <install-path>/skills/.venv/.

$ErrorActionPreference = "Stop"

$script:ScriptDir = Split-Path -Parent (Resolve-Path $MyInvocation.MyCommand.Path).ProviderPath
$script:RepoDir = Split-Path -Parent $script:ScriptDir

# Exit codes
$script:R_SUCCESS = 0
$script:R_FAILURE = 1

# Globals/defaults
$script:DefaultInstallPath = Join-Path $env:USERPROFILE ".copilot"

# Name of the virtual environment directory.
$script:VenvDirName = ".venv"


# ================================= Logging ================================== #

# Info-level logging.
function __log_info {
    param([string]$message)
    Write-Host "[INFO] $message"
}

# Error-level logging.
function __log_error {
    param([string]$message)
    Write-Host "[ERROR] $message"
}


# ================================= Usage =================================== #

# Prints the usage/help text for this script.
function __show_usage {
    Write-Host "Usage: setup-venv.ps1 [OPTIONS]"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -h, -Help                 Show this help message and exit."
    Write-Host "  -i, -InstallPath PATH     Path to the install root (default: `"$script:DefaultInstallPath`")."
}


# ================================== Main ==================================== #

# Main function. Parses arguments, then creates the venv and installs deps.
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

    $skills_dir = Join-Path $target_path "skills"
    $venv_path = Join-Path $skills_dir $script:VenvDirName
    $requirements = Join-Path $skills_dir "requirements.txt"

    # Verify the skills directory exists.
    if (-not (Test-Path $skills_dir)) {
        __log_error "Skills directory not found: $skills_dir"
        return $script:R_FAILURE
    }

    # Verify requirements.txt exists.
    if (-not (Test-Path $requirements)) {
        __log_error "requirements.txt not found: $requirements"
        return $script:R_FAILURE
    }

    # Create the virtual environment if it doesn't exist.
    if (-not (Test-Path $venv_path)) {
        __log_info "Creating virtual environment at: $venv_path"
        python -m venv $venv_path
        if ($LASTEXITCODE -ne 0) {
            __log_error "Failed to create virtual environment."
            return $script:R_FAILURE
        }
    } else {
        __log_info "Virtual environment already exists: $venv_path"
    }

    # Install dependencies.
    __log_info "Installing dependencies from: $requirements"
    $pip_path = Join-Path $venv_path "Scripts\pip.exe"
    & $pip_path install --quiet -r $requirements
    if ($LASTEXITCODE -ne 0) {
        __log_error "Failed to install dependencies."
        return $script:R_FAILURE
    }

    __log_info "Virtual environment ready: $venv_path"
    return $script:R_SUCCESS
}

# Invoke __main with all script arguments and exit with its return value.
$main_retval = __main @args
exit $main_retval
