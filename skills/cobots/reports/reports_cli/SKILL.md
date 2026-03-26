---
name: reports-cli
description: CLI for creating cobots reports from a template.
---

# reports-cli

A CLI skill for creating cobots reports.

## Description

This skill creates report files from `template.report.md`, filling in the frontmatter
with the provided arguments and reading the report body from STDIN. Reports are saved
under `.cobots/reports/` with timestamped file names.

## Usage

```bash
echo "Report body goes here" | python reports-cli.py create \
    --title "Architecture Review" \
    --author "alice"
```

## Subcommands

### `create`

Creates a new report from the template. Reads the report body from STDIN.

* `--title` *(required)* - The title of the report.
* `--author` *(required)* - The author of the report.

## Output

Prints the absolute path to the newly created report file.

The file is named `YYYY-MM-DD_HH-MM-SS_report_title.report.md`, where `report_title`
is a lowercase, underscore-separated slug of the `--title` argument.

## Example

```bash
$ echo "We reviewed the auth module design." | python reports-cli.py create \
    --title "Auth Module Review" \
    --author "alice"
/home/user/my-project/.cobots/reports/2026-03-26_15-16-55_auth_module_review.report.md
```
