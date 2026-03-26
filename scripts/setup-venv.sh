#!/bin/bash
# setup-venv.sh - Creates a Python virtual environment for cobots skills and
# installs dependencies from requirements.txt.
#
# Usage:
#   ./setup-venv.sh [OPTIONS]
#
# The virtual environment is created under <install-path>/skills/.venv/.


SCRIPT_DIR="$(realpath "$(dirname "${BASH_SOURCE[0]}")")"
REPO_DIR="$(dirname "${SCRIPT_DIR}")"

# Exit codes
R_SUCCESS=0
R_FAILURE=1

# Globals/defaults
DEFAULT_INSTALL_PATH="${HOME}/.copilot"

# Name of the virtual environment directory.
VENV_DIR_NAME=".venv"


# ================================= Logging ================================== #

# Info-level logging.
function __log_info()
{
    echo -e "[INFO] $1" 1>&2
}

# Error-level logging.
function __log_error()
{
    echo -e "[ERROR] $1" 1>&2
}


# ================================= Usage =================================== #

# Shows help menu.
function __show_usage()
{
    echo "Usage $(basename "$0") [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help                Show this help message and exit."
    echo "  -i, --install-path PATH   Path to the install root (default: \"${DEFAULT_INSTALL_PATH}\")."

    return ${R_SUCCESS}
}


# ================================== Main ==================================== #

# Main function.
function __main()
{
    local install_path="${DEFAULT_INSTALL_PATH}"

    # Initialize and parse arguments.
    local parsed_args=$(
        getopt \
            --options "hi:" \
            --longoptions "help,install-path:" \
            --name "$(basename "$0")" \
            -- "$@"
    ) || {
        __show_usage
        return ${R_FAILURE}
    }

    # Parse through the command-line arguments.
    eval set -- "${parsed_args}"
    while true; do
        case "$1" in
            -h|--help)
                __show_usage
                return ${R_SUCCESS}
                ;;
            -i|--install-path)
                install_path="$2"
                shift 2
                ;;
            --)
                shift
                break
                ;;
            *)
                __log_error "Unexpected option: $1"
                __show_usage
                return ${R_FAILURE}
                ;;
        esac
    done

    local skills_dir="${install_path}/skills"
    local venv_path="${skills_dir}/${VENV_DIR_NAME}"
    local requirements="${skills_dir}/requirements.txt"

    # Verify the skills directory exists.
    if [ ! -d "${skills_dir}" ]; then
        __log_error "Skills directory not found: ${skills_dir}"
        return ${R_FAILURE}
    fi

    # Verify requirements.txt exists.
    if [ ! -f "${requirements}" ]; then
        __log_error "requirements.txt not found: ${requirements}"
        return ${R_FAILURE}
    fi

    # Create the virtual environment if it doesn't exist.
    if [ ! -d "${venv_path}" ]; then
        __log_info "Creating virtual environment at: ${venv_path}"
        python3 -m venv "${venv_path}" || {
            __log_error "Failed to create virtual environment."
            return ${R_FAILURE}
        }
    else
        __log_info "Virtual environment already exists: ${venv_path}"
    fi

    # Install dependencies.
    __log_info "Installing dependencies from: ${requirements}"
    "${venv_path}/bin/pip" install --quiet -r "${requirements}" || {
        __log_error "Failed to install dependencies."
        return ${R_FAILURE}
    }

    __log_info "Virtual environment ready: ${venv_path}"
    return ${R_SUCCESS}
}

__main "$@"
main_retval=$?
exit ${main_retval}
