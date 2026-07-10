---
name: cobots-knowledge-cli
description: CLI for creating, querying, and managing the cobots knowledge base.
---

# knowledge-cli

A CLI skill for the cobots shared **knowledge base** (KB): a flat-file store
of durable, reusable, tag-categorized knowledge entries.

## Description

This skill provides subcommands to create entries, list and query them by a
boolean tag expression
and/or a regex over title + content, inspect and edit individual entries,
delete entries, and print a per-tag census. Each entry is a markdown document
with YAML frontmatter, assigned a randomly-generated hex ID and saved as
`{id}.knowledge.md` under `.cobots/knowledge/`.

Knowledge entries differ from reports: they are living documents (editable),
tag-categorized, and title/content-searchable. They differ from tasks: they
may be hard-deleted.

## Usage

```bash
# Create a new entry (reads body from STDIN). Tags are a plain, space-
# separated list (not an expression).
echo "ntfy auth uses a token in the Authorization header." \
  | python knowledge-cli.py create \
      --title "How ntfy authentication works" \
      --author "lorey" \
      --tags 'ntfy auth http'

# List all entries (sorted by creation time, ascending).
python knowledge-cli.py list

# List entries matching a boolean tag expression.
python knowledge-cli.py list --tags 'git and !rust'

# Query by tag expression and/or a regex over title + content (AND-combined).
python knowledge-cli.py query --tags 'git and (rust or c)'
python knowledge-cli.py query --regex 'token' --ignore-case
python knowledge-cli.py query --tags 'http and auth' --regex 'Bearer'

# Show one entry's full details (partial ID prefixes are supported).
python knowledge-cli.py get --id abc123

# Edit an entry non-interactively (or open it in $EDITOR with no flags).
python knowledge-cli.py edit --id abc123 --add-tags 'api rest'
python knowledge-cli.py edit --id abc123 --title "A clearer title"
echo "replacement body" | python knowledge-cli.py edit --id abc123 --body

# Delete an entry (agents should pass --force to skip the confirmation).
python knowledge-cli.py delete --id abc123 --force

# Print the per-tag entry census.
python knowledge-cli.py tags
```

## Subcommands

### `create`

Creates a new entry. Reads the entry body from STDIN.

* `--title` *(required)* - The title of the entry.
* `--author` *(required)* - The author of the entry (sanitized: lowercased,
  whitespace to underscores).
* `--tags` *(required)* - One or more tag names, whitespace-separated, e.g.
  `--tags 'git cli python'`. This is a **plain tag list, not an expression**:
  boolean operators (`and`/`or`/`not`/`!`) and parentheses are rejected here.
  Each tag is lowercased and validated; reserved words are rejected.
* `--empty` *(optional)* - Create with an empty body, skipping STDIN.

**NOTE:** Do *not* use colons (`:`) in the title. This will confuse the YAML
parser.

### `list`

Lists entries, one per line, sorted by creation timestamp (ascending).

* `--tags` *(optional)* - A **boolean tag expression** (same grammar as
  `query`, see below) to filter by, e.g. `--tags 'git and !rust'`.
* `--show-path` *(optional)* - Append the absolute file path for each entry.

### `query`

The core discovery command. Filters entries by a tag expression **and/or** a
regex over title + content. When both are given, an entry must satisfy **all**
conditions (logical AND). If neither is given, it behaves like an unfiltered
`list`.

* `--tags` *(optional)* - A boolean tag expression (see the grammar below).
* `--regex` *(optional)* - A regular expression matched with `re.search`
  (partial match anywhere) against each entry's title + full body.
* `--ignore-case` *(optional)* - Apply case-insensitive matching to `--regex`.
* `--show-path` *(optional)* - Append the absolute file path for each entry.

### `get`

Shows full details of an entry: path, ID, timestamps, title, author, tags, and
contents.

* `--id` *(required)* - The entry ID (supports partial ID prefixes).

### `edit`

Updates an entry non-interactively, or — if no update flags are given — opens
the entry file in the user's preferred editor (`$EDITOR`). Any successful
change refreshes the entry's `updated_timestamp`; the `id` and
`created_timestamp` are preserved.

* `--id` *(required)* - The entry ID (supports partial ID prefixes).
* `--add-tags` *(optional)* - Whitespace-separated tags to add (plain list,
  lowercased + validated, deduped against existing tags).
* `--remove-tags` *(optional)* - Whitespace-separated tags to remove (matched
  case-insensitively; no error if absent).
* `--set-tags` *(optional)* - Whitespace-separated tags that replace the
  entire tag set. Mutually exclusive with `--add-tags`/`--remove-tags`.
* `--title` *(optional)* - A new title. Updates both the frontmatter `title`
  and the H1 heading in the body.
* `--body` *(optional)* - Read a new full body from STDIN, replacing the
  existing body.

An edit that would leave the entry with zero tags is rejected.

### `delete`

Hard-deletes an entry file by ID. Prompts for `y/N` confirmation on stderr
unless a bypass flag is given.

* `--id` *(required)* - The entry ID (supports partial ID prefixes).
* `--force` / `--yes` *(optional)* - Bypass the confirmation prompt (for
  non-interactive agent use).

### `tags`

Lists all tags across every entry with a per-tag entry count, grouped
case-insensitively.

* `--sort {count,name}` *(optional)* - Sort by count (default, descending) or
  by tag name (ascending).
* `--json` *(optional)* - Emit machine-readable JSON.

## Tag Grammar

Both `list --tags` and `query --tags` use the **same** boolean tag-expression
engine. The grammar is a full boolean expression over tag names.

* **Operators:** `and`, `or`, `not`, plus `!` as an alias for `not`. Operator
  keywords are case-insensitive (`and` = `AND` = `And`).
* **Precedence:** `not` (highest) > `and` > `or` (lowest). Binary operators are
  left-associative. Parentheses `(` `)` override precedence and nest.
* **Implicit AND:** two operands separated only by whitespace are implicitly
  ANDed. `git rust` is equivalent to `git and rust`.
* **Case-insensitive tags:** operands and stored tags are lowercased, so `git`
  and `Git` are the same tag.
* **Empty expression:** an empty (or whitespace-only) `--tags` matches every
  entry — it is not an error.

Valid tag names match `[A-Za-z0-9_-]+` and may not be the bare reserved words
`and`, `or`, or `not` (compound tags like `and_gate` or `android` are fine).

### Examples

Given entries `E1{git,c}`, `E2{git,c,rust}`, `E3{git,python}`, `E4{python}`:

| Expression | Matches | Why |
|-----------|---------|-----|
| `git or rust` | E1, E2, E3 | any entry with git or rust |
| `git and (rust or c)` | E1, E2 | git plus (rust or c) |
| `!git and rust and c` | (none) | requires no git but rust and c |
| `git rust` | E2 | implicit AND of git and rust |
| `not git` | E4 | only entry without git |
| `Git AND C` | E1, E2 | operators and tags are case-folded |
| `` (empty) | E1–E4 | empty matches all |

Syntax errors — unbalanced parentheses (`git and (rust`), a dangling operator
(`git and`), empty parentheses (`git and ()`), a bare comma (`git , c`), or a
reserved word / invalid character used as a tag — exit with code `2`.

## Shell-Quoting Guidance

Tag expressions contain spaces and may contain `!`. In **bash**, `!` triggers
history expansion **even inside double quotes**, so prefer **single quotes**:

```bash
python knowledge-cli.py query --tags 'git and !rust'      # recommended
python knowledge-cli.py query --tags 'git and not rust'   # !-free alternative
```

Double quotes (`--tags "git and !rust"`) risk a bash history-expansion error on
the `!`. Using the `not` keyword instead of `!` avoids the issue entirely.
This is a shell-usage note only; it does not affect the grammar.

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Success (including zero query/list matches, which is not an error). |
| `1` | Runtime/resolution failure: entry not found, ambiguous prefix, empty body on `create`, missing `$EDITOR` on interactive `edit`, declined `delete`. |
| `2` | Invalid user input: bad tag syntax, bad tag expression, invalid regex, or a tag operation that would leave zero tags. |

## Output

### `create`

Prints the absolute path to the newly created entry file. The file is named
`{id}.knowledge.md`, where `{id}` is a randomly-generated hex string.

### `list` / `query`

Prints one line per entry in the format:

```
[{id}] [{created_timestamp}] ({author}) {title} #tag1 #tag2
```

With `--show-path`, the absolute path is appended.

### `get`

Prints formatted entry details:

```
Path:           /path/to/entry.knowledge.md
ID:             abc123...
Created:        2026-07-09 15:40:00
Updated:        2026-07-09 15:40:00
Title:          How ntfy authentication works
Author:         lorey
Tags:           ntfy, auth, http

Contents:
  (the body text, with each line indented by 2 spaces)
```

### `tags`

Prints an aligned table (or JSON with `--json`):

```
TAG              COUNT
git                  7
python               5
```

## Example

```bash
$ echo "ntfy auth uses a token in the Authorization header." \
    | python knowledge-cli.py create \
        --title "How ntfy authentication works" \
        --author "lorey" \
        --tags 'ntfy auth http'
/home/user/my-project/.cobots/knowledge/4f9a1c7e0b3d5a62.knowledge.md

$ python knowledge-cli.py list
[4f9a1c7e0b3d5a62] [2026-07-09 15:40:00] (lorey) How ntfy authentication works #ntfy #auth #http

$ python knowledge-cli.py query --tags 'auth and http' --regex 'token'
[4f9a1c7e0b3d5a62] [2026-07-09 15:40:00] (lorey) How ntfy authentication works #ntfy #auth #http

$ python knowledge-cli.py tags
TAG    COUNT
auth       1
http       1
ntfy       1
```
