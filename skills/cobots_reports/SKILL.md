---
name: cobots-reports-cli
description: CLI for creating cobots reports from a template.
---

# reports-cli

A CLI skill for creating, listing, and inspecting cobots reports.

## Description

This skill provides subcommands to create reports from `template.report.md`, list
existing reports, and inspect individual reports stored under `.cobots/reports/`.
Each report is assigned a randomly-generated hex ID and saved as `{id}.report.md`.

## Usage

```bash
# Create a new report (reads body from STDIN).
echo "Report body goes here" | python reports-cli.py create \
    --title "Architecture Review" \
    --author "alice"

# List all reports.
python reports-cli.py list

# List reports showing file paths.
python reports-cli.py list --show-path

# Show details of a report by ID (supports partial ID prefixes).
python reports-cli.py get --id "abc123"
```

## Subcommands

### `create`

Creates a new report from the template. Reads the report body from STDIN.

* `--title` *(required)* - The title of the report.
* `--author` *(required)* - The author of the report.
* `--empty` *(optional)* - Create the report with empty contents, skipping STDIN.

**NOTE:** When specifying these fields, please do *not* use colons (`:`) in the text.
This will confuse the YAML parser.

### `list`

Lists all reports, one per line, showing report ID, timestamp, author, and title.

* `--show-path` *(optional)* - Include the full file path for each report.

### `get`

Shows full details of a report: file path, ID, title, author, timestamp, and contents.

* `--id` *(required)* - The report ID (supports partial ID prefixes).

## Output

### `create`

Prints the absolute path to the newly created report file.

The file is named `{id}.report.md`, where `{id}` is a randomly-generated hex string.

### `list`

Prints one line per report in the format:

```
[{id}] [{timestamp}] ({author}) {title}
```

### `get`

Prints formatted report details:

```
Path:           /path/to/report.report.md
ID:             abc123...
Title:          Report Title
Author:         alice
Timestamp:      2026-03-26 15:16:55

Contents:
  (the body text, with each line indented by 2 spaces)
```

## Example

```bash
$ echo "We reviewed the auth module design." | python reports-cli.py create \
    --title "Auth Module Review" \
    --author "alice"
/home/user/my-project/.cobots/reports/a1b2c3d4e5f67890.report.md

$ python reports-cli.py list
[a1b2c3d4e5f67890] [2026-03-26 15:16:55] (alice) Auth Module Review

$ python reports-cli.py get --id a1b2c3d4
Path:           /home/user/my-project/.cobots/reports/a1b2c3d4e5f67890.report.md
ID:             a1b2c3d4e5f67890
Title:          Auth Module Review
Author:         alice
Timestamp:      2026-03-26 15:16:55

Contents:
  We reviewed the auth module design.
```
