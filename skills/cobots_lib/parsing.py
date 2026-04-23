"""
parsing.py - Shared parsing utilities for cobots markdown files.

Provides functions to parse YAML frontmatter and discussion headers
from markdown files used by tasks, reports, and other cobots skills.
"""

import re

import yaml

# Regex matching a discussion header: ## YYYY-MM-DD HH:MM:SS - AuthorName
DISCUSSION_HEADER_RE = re.compile(
    r"^## (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) - (.+)$"
)


def parse_frontmatter(path: str) -> tuple[dict, str]:
    """Splits a markdown file on ``---`` delimiters.

    Returns ``(frontmatter_dict, body_str)``.  On any parse error
    (missing delimiters, malformed YAML, etc.) returns ``({}, full_content)``.
    """
    with open(path, "r", encoding="utf-8") as fh:
        content = fh.read()
    if not content.startswith("---"):
        return {}, content
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content
    try:
        frontmatter = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError:
        return {}, content
    body = parts[2].strip()
    return frontmatter, body


def parse_discussion_headers(body: str) -> list[tuple[str, str]]:
    """Extracts ``(timestamp, author)`` tuples from discussion headers."""
    results: list[tuple[str, str]] = []
    for line in body.splitlines():
        m = DISCUSSION_HEADER_RE.match(line.strip())
        if m:
            results.append((m.group(1), m.group(2)))
    return results
