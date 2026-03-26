# tasks-cli

A CLI skill for managing cobots tasks.

## Description

This skill provides subcommands to create, list, inspect, and update task files stored
under `.cobots/tasks/`. Task files use markdown with YAML frontmatter and end in `.task.md`.

## Usage

```bash
# Create a new task (reads description from STDIN).
echo "Implement feature X" | python tasks-cli.py create \
    --title "Feature X" \
    --author "alice" \
    --status "untouched" \
    --owner "bob" \
    --linked-tasks "abc123,def456"

# List all tasks.
python tasks-cli.py list

# List tasks filtered by status, showing file paths.
python tasks-cli.py list --status "underway" --show-path

# Show details of a task.
python tasks-cli.py get --id "abc123"

# Update a task's status.
python tasks-cli.py set-status --id "abc123" --status "done"

# Add a discussion entry (reads content from STDIN).
echo "Looks good so far" | python tasks-cli.py add-discussion \
    --id "abc123" \
    --author "alice"
```

## Subcommands

### `create`

Creates a new task from `template.task.md`. Reads the description from STDIN.

* `--title` *(required)* - The title of the task.
* `--author` *(required)* - The creator of the task.
* `--status` *(required)* - The initial status (must be a configured status value).
* `--owner` *(optional)* - The owner working on the task.
* `--linked-tasks` *(optional)* - Comma-separated list of linked task IDs.

### `list`

Lists all tasks, one per line, showing task ID, title, and status.

* `--owner` *(optional)* - Filter tasks by owner.
* `--status` *(optional)* - Filter tasks by status.
* `--show-path` *(optional)* - Include the full file path for each task.

### `get`

Shows full details of a task: file path, ID, title, all frontmatter fields, description, and the latest discussion entry.

* `--id` *(required)* - The task ID.

### `set-status`

Updates the status field of a task.

* `--id` *(required)* - The task ID.
* `--status` *(required)* - The new status (must be a configured status value).

### `add-discussion`

Appends a timestamped discussion entry to the bottom of the task file. Reads discussion content from STDIN.

* `--id` *(required)* - The task ID.
* `--author` *(required)* - The author of the discussion entry.
