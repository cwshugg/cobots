#!/bin/bash
# Script that installs the AI tools in this repository to the user environment.


SCRIPT_DIR="$(realpath "$(dirname "${BASH_SOURCE[0]}")")"
REPO_DIR="$(dirname "${SCRIPT_DIR}")"

# Exit codes
R_SUCCESS=0
R_FAILURE=1

# Globals/defaults
DEFAULT_INSTALL_PATH="${HOME}/.copilot"


# ================================= Logging ================================== #
# Writes a message to output; used for logging progress.
function __log()
{
    level="$1"
    message="$2"
    echo -e "[${level}] ${message}" 1>&2
}

# Info-level logging.
function __log_info()
{
    __log "INFO" "$1"
}

# Error-level logging.
function __log_error()
{
    __log "ERROR" "$1"
}


# ============================ Main Installation ============================= #
# Installs agent files.
function __install_agents()
{
    local install_path="$1"

    # Does an agents directory not exist? If so, create it.
    agents_dst="$(realpath "${install_path}/agents")"
    if [ ! -d "${agents_dst}" ]; then
        mkdir -p "${agents_dst}"
    fi

    # Make sure we have an agents source directory:
    agents_src="${REPO_DIR}/agents"
    if [ ! -d "${agents_src}" ]; then
        __log_error "Agents source directory not found: ${agents_src}"
        return ${R_FAILURE}
    fi

    # Locate all agent markdown files and copy them into the agents directory:
    agent_count=0
    while IFS= read -r -d '' agent_file; do
        agent_fname="$(basename "${agent_file}")"
        agent_rel="${agent_file#${agents_src}/}"
        agent_dst="${agents_dst}/${agent_rel}"
        install -D "${agent_file}" "${agent_dst}"

        __log_info "Installed agent \"${agent_fname}\" to: ${agent_dst}"
        agent_count=$((agent_count + 1))
    done < <(find "${agents_src}" -type f -name "*.*agent*.md" -print0)

    __log_info "Installed ${agent_count} agents to: ${agents_dst}"
    return ${R_SUCCESS}
}

# Installs skill files.
function __install_skills()
{
    local install_path="$1"

    # Does an skills directory not exist? If so, create it.
    skills_dst="$(realpath "${install_path}/skills")"
    if [ ! -d "${skills_dst}" ]; then
        mkdir -p "${skills_dst}"
    fi

    # Make sure we have an skills source directory:
    skills_src="${REPO_DIR}/skills"
    if [ ! -d "${skills_src}" ]; then
        __log_error "Skills source directory not found: ${skills_src}"
        return ${R_FAILURE}
    fi

    # Locate all skill files and copy them into the skills directory:
    skill_count=0
    while IFS= read -r -d '' skill_file; do
        skill_fname="$(basename "${skill_file}")"
        skill_rel="${skill_file#${skills_src}/}"
        skill_dst="${skills_dst}/${skill_rel}"
        install -D "${skill_file}" "${skill_dst}"

        __log_info "Installed skill file \"${skill_rel}\" to: ${skill_dst}"

        # Only increase the skill count if we're installing a `SKILL.md` file
        # during this iteration; this keeps the skill count accurate.
        if [[ "${skill_fname}" == *SKILL*.md ]]; then
            skill_count=$((skill_count + 1))
        fi
    done < <( \
        find "${skills_src}" \
        -type f \
        \( \
            -name "*SKILL*.md" -or \
            -name "template.*.md" -or \
            -name "requirements.txt" -or \
            -name "*.py" -or \
            -name "*.tcss" \
        \) -and \
        \( \
            -not -wholename "*/.venv/*" \
        \) \
        -print0 \
    )

    __log_info "Installed ${skill_count} skills to: ${skills_dst}"
    return ${R_SUCCESS}
}

# Installs instruction files.
function __install_instructions()
{
    local install_path="$1"

    # Does an instructions directory not exist? If so, create it.
    insts_dst="$(realpath "${install_path}/instructions")"
    if [ ! -d "${insts_dst}" ]; then
        mkdir -p "${insts_dst}"
    fi

    # Make sure we have an instructions source directory:
    insts_src="${REPO_DIR}/instructions"
    if [ ! -d "${insts_src}" ]; then
        __log_error "Agents source directory not found: ${insts_src}"
        return ${R_FAILURE}
    fi

    # Locate all instruction markdown files and copy them into the instructions
    # directory:
    inst_count=0
    while IFS= read -r -d '' inst_file; do
        inst_fname="$(basename "${inst_file}")"
        inst_rel="${inst_file#${insts_src}/}"
        inst_dst="${insts_dst}/${inst_rel}"
        install -D "${inst_file}" "${inst_dst}"

        __log_info "Installed instruction \"${inst_fname}\" to: ${inst_dst}"
        inst_count=$((inst_count + 1))
    done < <(find "${insts_src}" -type f -name "*.*instruction*.md" -print0)

    __log_info "Installed ${inst_count} instructions to: ${insts_dst}"
    return ${R_SUCCESS}
}

# Shows help menu.
function __show_usage()
{
    echo "Usage $(basename "$0") [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help                Show this help message and exit."
    echo "  -i, --install-path PATH   Path to install the tools (default: \"${DEFAULT_INSTALL_PATH}\")."

    return ${R_SUCCESS}
}

# Main function.
function __main()
{
    local install_path="${DEFAULT_INSTALL_PATH}"

    # Initialize and parser arguments:
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

    # Parse through the command-line arguments:
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

    __log_info "Installing tools to: ${install_path}"

    # Install agents
    __install_agents "${install_path}"
    local retval=$?
    if [ ${retval} -ne 0 ]; then
        __log_error "Failed to install agents."
        return ${retval}
    fi

    # Install skills
    __install_skills "${install_path}"
    local retval=$?
    if [ ${retval} -ne 0 ]; then
        __log_error "Failed to install skills."
        return ${retval}
    fi

    # Install instructions
    __install_instructions "${install_path}"
    local retval=$?
    if [ ${retval} -ne 0 ]; then
        __log_error "Failed to install instructions."
        return ${retval}
    fi

    # Set up the Python virtual environment for skills.
    local setup_venv="${SCRIPT_DIR}/setup-venv.sh"
    if [ -f "${setup_venv}" ]; then
        __log_info "Setting up Python virtual environment..."
        bash "${setup_venv}" --install-path "${install_path}"
        local retval=$?
        if [ ${retval} -ne 0 ]; then
            __log_error "Failed to set up virtual environment."
            return ${retval}
        fi
    fi

    # Install the aliases file:
    aliases_src="${REPO_DIR}/scripts/aliases.sh"
    aliases_dst="${install_path}/aliases.sh"
    if [ -f "${aliases_src}" ]; then
        install -D "${aliases_src}" "${aliases_dst}"
        __log_info "Installed aliases file to: ${aliases_dst}"
    else
        __log_error "Aliases source file not found (\"${aliases_src}\"). Skipping."
    fi

    return ${R_SUCCESS}
}

__main "$@"
main_retval=$?
exit ${main_retval}

