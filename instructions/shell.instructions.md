---
name: "shell"
description: "Shell and Bash scripting best practices and conventions"
applyTo: "**/*.sh"
---

<!--
Adapted from the awesome-copilot project:

https://github.com/github/awesome-copilot/blob/main/instructions/shell.instructions.md

The original is available at the URL above. This version has been adapted to
match the cobots instruction style.
- Scribs
-->

# Shell Scripting Best Practices

Follow these guidelines when writing shell scripts in Bash, sh, zsh, or other POSIX-compatible shells.

## General Principles

* Write scripts that are clean, simple, and easy to read.
* Add comments where helpful for understanding how the script works.
* Use `shellcheck` for static analysis when available.
* Prefer safe expansions: double-quote variable references (`"$var"`), use `${var}` for clarity, and avoid `eval`.
* Use modern Bash features (`[[ ]]`, `local`, arrays) when portability requirements allow; fall back to POSIX constructs only when targeting `sh`.
* Choose reliable parsers for structured data instead of ad-hoc text processing.

## Error Handling and Safety

* Always enable strict mode at the top of every script:

```bash
set -euo pipefail
```

* `set -e` exits on the first error.
* `set -u` treats unset variables as errors.
* `set -o pipefail` surfaces failures in any stage of a pipeline.

* Validate all required parameters before execution.
* Provide clear error messages with context (include the script name, the failing operation, and what was expected).
* Use `trap` to clean up temporary resources when the script exits.
* Declare immutable values with `readonly` (or `declare -r`) to prevent accidental reassignment.
* Use `mktemp` to create temporary files or directories safely and remove them in your cleanup handler.

## Script Structure

* Start with a clear shebang: `#!/bin/bash` (or `#!/bin/sh` for POSIX scripts).
* Include a header comment explaining the script's purpose.
* Define default values for all variables at the top.
* Use functions for reusable code blocks.
* Keep the main execution flow clean and readable.

### Script Template

```bash
#!/bin/bash

# ============================================================================
# Script Description Here
# ============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------

cleanup() {
    if [[ -n "${TEMP_DIR:-}" && -d "$TEMP_DIR" ]]; then
        rm -rf "$TEMP_DIR"
    fi
}

trap cleanup EXIT

# ---------------------------------------------------------------------------
# Default values
# ---------------------------------------------------------------------------

RESOURCE_GROUP=""
OPTIONAL_PARAM="default-value"
readonly SCRIPT_NAME="$(basename "$0")"

TEMP_DIR=""

# ---------------------------------------------------------------------------
# Functions
# ---------------------------------------------------------------------------

usage() {
    echo "Usage: $SCRIPT_NAME [OPTIONS]"
    echo "Options:"
    echo "  -g, --resource-group   Resource group (required)"
    echo "  -h, --help             Show this help"
    exit 0
}

validate_requirements() {
    if [[ -z "$RESOURCE_GROUP" ]]; then
        echo "Error: Resource group is required" >&2
        exit 1
    fi
}

main() {
    validate_requirements

    # Argument parsing:
    while [[ $# -gt 0 ]]; do
        case $1 in
            -g|--resource-group)
                RESOURCE_GROUP="$2"
                shift 2
                ;;
            -h|--help)
                usage
                ;;
            *)
                echo "Unknown option: $1" >&2
                exit 1
                ;;
        esac
    done

    TEMP_DIR="$(mktemp -d)"
    if [[ ! -d "$TEMP_DIR" ]]; then
        echo "Error: failed to create temporary directory" >&2
        exit 1
    fi

    echo "Starting $SCRIPT_NAME..."

    # Main logic here

    echo "Done."
}

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

main "$@"
```

## Quoting and Variable Expansion

* Always double-quote variable references: `"$var"`, `"${var}"`.
* Use `"${var:-default}"` for variables that may be unset.
* Never use unquoted `$*`; prefer `"$@"` for passing arguments.
* Use arrays for lists of items instead of space-separated strings.

## Working with JSON and YAML

* Prefer dedicated parsers (`jq` for JSON, `yq` for YAML) over ad-hoc text processing with `grep`, `awk`, or shell string splitting.
* Validate that required fields exist and handle missing data explicitly (e.g., check `jq` exit status or use `// empty`).
* Quote `jq`/`yq` filters to prevent shell expansion and prefer `--raw-output` when you need plain strings.
* Treat parser errors as fatal: combine with `set -euo pipefail` or test command success before using results.
* Document parser dependencies at the top of the script and fail fast with a helpful message if required tools are not installed.

```bash
# Check for required tools
for cmd in jq curl; do
    if ! command -v "$cmd" &>/dev/null; then
        echo "Error: $cmd is required but not installed." >&2
        exit 1
    fi
done

# Safe jq usage
name="$(echo "$json_data" | jq --raw-output '.name // empty')"
if [[ -z "$name" ]]; then
    echo "Error: 'name' field is missing from JSON data." >&2
    exit 1
fi
```

## Logging and Output

* Send informational messages to stdout and error messages to stderr (`>&2`).
* Avoid excessive `echo` output; keep execution status concise.
* Use a consistent prefix for log messages when scripts produce substantial output.
* Never leak secrets (passwords, tokens, keys) in log output.
* If you're adding color prints that use `echo -e` or a similar escape-sequence-supporting print, implementation additional logic that first checks to ensure that stdout is pointed at a *terminal* (not a file, pipe, etc.)
    * If (and only if) stdout is pointing to a terminal, color should be written.
      Otherwise, color should *not* be written, such that the output can be cleanly parsed by other programs.

## Patterns to Avoid

* Don't use `eval` — it is a common source of injection vulnerabilities.
* Don't parse `ls` output; use globbing or `find` instead.
* Don't use backticks for command substitution; use `$(...)` instead.
* Don't hardcode paths or values that may change; use variables.
* Avoid deeply nested `if`/`else` blocks — use early returns (the "fail fast" pattern).
* Don't ignore `shellcheck` warnings; treat them as errors during CI.
