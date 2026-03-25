# create-task

A CLI skill that creates a new task from the task template.

## Description

This skill copies `template.task.md`, fills in the frontmatter with the provided arguments,
reads the task description from STDIN, generates a random hex task ID of the configured
length (see `task_id_length` in `cobots-config.yaml`), and saves the result under
`.cobots/tasks/`.

## Usage

```bash
echo "Implement the login page" | python create-task.py \
    --title "Implement login page" \
    --author "alice" \
    --status "untouched"
```

## Arguments

* `--title` *(required)* - The title of the task.
* `--author` *(required)* - The name of the human or agent creating the task.
* `--status` *(required)* - The initial status of the task. Must be one of the values defined in `task_status_values` in the cobots config.

## Input

The task description is read from **STDIN**. Pipe or redirect text into the command.

## Output

Prints the absolute path to the newly created task file.

## Example

```bash
$ echo "Build the REST API for user management" | python create-task.py \
    --title "User management API" \
    --author "bob" \
    --status "untouched"
/home/user/my-project/.cobots/tasks/a3f7b2c91de04f18.task.md
```
