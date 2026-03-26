---
name: workspace-cli
description: CLI for initializing and managing the cobots workspace.
---

# workspace-cli

A CLI skill for managing the cobots workspace.

## Description

This skill resolves and manages the `.cobots/` workspace directory, which contains the
config file, tasks, and reports. Locations are resolved using the following strategy
(in order):

1. **Workspace lookup** — Walk up from the current directory looking for an existing `.cobots/` directory.
2. **Git root fallback** — If no workspace is found, target the git repository root.
3. **Current directory fallback** — If not inside a git repository, target the current working directory.

## Usage

```bash
# Print the resolved config file path (no side effects).
python workspace-cli.py --show-config-path

# Print the resolved working directory path (no side effects).
python workspace-cli.py --show-working-dir-path

# Initialize the full workspace.
python workspace-cli.py --init
```

## Arguments

* `--show-config-path` - Print the resolved config file path without modifying anything.
* `--show-working-dir-path` - Print the resolved working directory path without modifying anything.
* `--init` - Initialize the full workspace: creates `.cobots/`, `cobots-config.yaml`, `tasks/`, and `reports/`.

## Examples

```bash
$ python workspace-cli.py --show-config-path
/home/user/my-project/.cobots/cobots-config.yaml

$ python workspace-cli.py --show-working-dir-path
/home/user/my-project/.cobots

$ python workspace-cli.py --init
Initialized workspace: /home/user/my-project/.cobots

$ python workspace-cli.py --init
Already initialized: /home/user/my-project/.cobots
```
