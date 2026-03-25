# working-dir-cli

A CLI skill for managing the cobots working directory.

## Description

This skill resolves and manages the `.cobots/` directory where agents store intermediate
output and other working files. The directory location is resolved using the following
strategy (in order):

1. **Config file lookup** — Walk up from the current directory looking for `cobots-config.yaml`. If found, the working directory is `.cobots/` in the same directory as the config file.
2. **Git root fallback** — If no config file is found, detect the root of the current git repository and place `.cobots/` there.
3. **Current directory fallback** — If not inside a git repository, use `.cobots/` in the current working directory.

## Usage

```bash
# Print the resolved working directory path (no side effects).
python working-dir-cli.py --show-path

# Create the working directory if it doesn't exist.
python working-dir-cli.py --init
```

## Arguments

* `--show-path` - Print the resolved working directory path without modifying anything.
* `--init` - Create the working directory if it does not already exist. Prints whether it was created or already exists.

## Examples

```bash
$ python working-dir-cli.py --show-path
/home/user/my-project/.cobots

$ python working-dir-cli.py --init
Created: /home/user/my-project/.cobots

$ python working-dir-cli.py --init
Already exists: /home/user/my-project/.cobots
```
