# config-cli

A CLI skill for managing the cobots config file.

## Description

This skill resolves and manages the `cobots-config.yaml` file. The file location is
resolved using the following strategy (in order):

1. **Config file lookup** — Walk up from the current directory looking for an existing `cobots-config.yaml`.
2. **Git root fallback** — If no config file is found, target the git repository root.
3. **Current directory fallback** — If not inside a git repository, target the current working directory.

## Usage

```bash
# Print the resolved config file path (no side effects).
python config-cli.py --show-path

# Create a default config file if one doesn't exist.
python config-cli.py --init
```

## Arguments

* `--show-path` - Print the resolved config file path without modifying anything.
* `--init` - Create a default config file if one does not already exist. Prints whether it was created or already exists.

## Examples

```bash
$ python config-cli.py --show-path
/home/user/my-project/cobots-config.yaml

$ python config-cli.py --init
Created: /home/user/my-project/cobots-config.yaml

$ python config-cli.py --init
Already exists: /home/user/my-project/cobots-config.yaml
```
