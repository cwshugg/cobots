#!/usr/bin/env python3
"""
docparse-cli.py - CLI for converting documents to readable text.

Provides subcommands to parse documents into Markdown / plain text,
list supported formats, and check optional dependency status.
"""

import argparse
import logging
import shutil
import sys
import os

# -----------------------------------------------------------------------
# Boilerplate: add skills/ to path, activate venv.
# -----------------------------------------------------------------------
_SKILLS_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..")
)
if _SKILLS_DIR not in sys.path:
    sys.path.insert(0, _SKILLS_DIR)

from venv.venv import activate_venv
activate_venv()

from cobots_lib.docparse import (
    parse_file,
    parse_bytes,
    supported_formats as get_supported_formats,
    DocparseError,
    SecurityError,
)
from cobots_lib.docparse.converter import DocumentConverter
from cobots_lib.docparse.constants import (
    DEFAULT_TIMEOUT,
    MAX_STDIN_SIZE,
)


# -----------------------------------------------------------------------
# Subcommand handlers
# -----------------------------------------------------------------------


def cmd_parse(args: argparse.Namespace) -> int:
    """Handle the ``parse`` subcommand."""
    # Configure logging.
    _configure_logging(args)

    kwargs = {
        "output_format": args.format,
        "timeout": args.timeout,
        "include_metadata": args.metadata,
        "validate": args.validate,
    }
    if args.encoding:
        kwargs["encoding"] = args.encoding
    if args.base_dir:
        kwargs["base_dir"] = args.base_dir
    if args.max_decompressed_size:
        kwargs["max_decompressed_size"] = (
            args.max_decompressed_size * 1024 * 1024
        )

    try:
        if args.file == "-":
            result = _parse_stdin(args, kwargs)
        else:
            result = parse_file(args.file, **kwargs)
    except DocparseError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    # Build output.
    output = ""
    if args.metadata:
        output += _build_metadata_header(result)
    output += result.content

    # Write output.
    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8") as fh:
                fh.write(output)
        except OSError as exc:
            print(f"Error writing output: {exc}", file=sys.stderr)
            return 1
    else:
        print(output)

    return 0


def _parse_stdin(
    args: argparse.Namespace, kwargs: dict
) -> "ParseResult":
    """Read stdin and parse via ``parse_bytes``."""
    max_size = args.max_size * 1024 * 1024
    data = sys.stdin.buffer.read(max_size + 1)
    if len(data) > max_size:
        raise DocparseError(
            f"Stdin input exceeds {args.max_size} MB limit."
        )

    filename = args.filename or "stdin_input"
    return parse_bytes(
        data, filename, source_path="<stdin>", **kwargs
    )


def _build_metadata_header(result) -> str:
    """Build a YAML metadata header from a ParseResult."""
    lines = ["---"]
    for key, value in sorted(result.metadata.items()):
        if isinstance(value, list):
            lines.append(f"{key}:")
            for item in value:
                lines.append(f'  - "{item}"')
        elif isinstance(value, str):
            lines.append(f'{key}: "{value}"')
        else:
            lines.append(f"{key}: {value}")
    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def cmd_formats(args: argparse.Namespace) -> int:
    """Handle the ``formats`` subcommand."""
    converter = DocumentConverter()
    statuses = converter.handler_status()

    # Explode each handler into one row per extension so the table
    # stays clean even when a handler covers many extensions.
    rows: list[tuple[str, str, str]] = []
    for info in statuses:
        avail = "yes" if info["available"] else "no"
        for ext in info["extensions"]:
            rows.append((ext, info["name"], avail))

    # Sort alphabetically by extension for easy scanning/grepping.
    rows.sort(key=lambda r: r[0])

    # Compute column widths dynamically.
    ext_w = max(len("Extension"), max(len(r[0]) for r in rows))
    name_w = max(len("Handler"), max(len(r[1]) for r in rows))
    avail_w = len("Available")

    print(
        f"{'Extension':<{ext_w}}  "
        f"{'Handler':<{name_w}}  "
        f"{'Available':<{avail_w}}"
    )
    print(
        f"{'-' * ext_w}  "
        f"{'-' * name_w}  "
        f"{'-' * avail_w}"
    )

    for ext, name, avail in rows:
        print(
            f"{ext:<{ext_w}}  "
            f"{name:<{name_w}}  "
            f"{avail:<{avail_w}}"
        )

    return 0


def cmd_check_deps(args: argparse.Namespace) -> int:
    """Handle the ``check-deps`` subcommand."""
    deps = [
        ("antiword", "apt install antiword",
         ".doc (primary)"),
        ("catdoc", "apt install catdoc",
         ".doc (alternative)"),
        ("libreoffice", "apt install libreoffice",
         ".doc, .ppt, .odt/.ods/.odp (fallback)"),
        ("tesseract", "apt install tesseract-ocr",
         "OCR for scanned PDFs"),
    ]

    print(
        f"{'Dependency':<15} {'Status':<12} "
        f"{'Required For':<40} {'Install'}"
    )
    print(
        f"{'-'*15} {'-'*12} {'-'*40} {'-'*30}"
    )

    for name, install, purpose in deps:
        found = shutil.which(name) is not None
        status = "installed" if found else "missing"
        print(
            f"{name:<15} {status:<12} {purpose:<40} {install}"
        )

    return 0


# -----------------------------------------------------------------------
# Logging configuration
# -----------------------------------------------------------------------


def _configure_logging(args: argparse.Namespace) -> None:
    """Set up logging based on CLI flags."""
    if getattr(args, "quiet", False):
        level = logging.CRITICAL
    elif getattr(args, "verbose", False):
        level = logging.DEBUG
    else:
        level = logging.WARNING

    logging.basicConfig(
        level=level,
        format="%(levelname)s: %(message)s",
        stream=sys.stderr,
    )


# -----------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------


def main() -> int:
    """Entry point.  Parses subcommands and dispatches."""
    parser = argparse.ArgumentParser(
        description=(
            "Convert documents to readable text "
            "(Markdown / plain text)."
        ),
    )
    subparsers = parser.add_subparsers(
        dest="command", required=True
    )

    # --- parse subcommand ---
    parse_p = subparsers.add_parser(
        "parse", help="Convert a document to text."
    )
    parse_p.add_argument(
        "file", help="Path to document, or '-' for stdin."
    )
    parse_p.add_argument(
        "--output", "-o", help="Write output to file."
    )
    parse_p.add_argument(
        "--format", "-f",
        choices=["markdown", "text", "auto"],
        default="auto",
        help="Output format (default: auto).",
    )
    parse_p.add_argument(
        "--filename",
        help="Filename hint for stdin input.",
    )
    parse_p.add_argument(
        "--encoding",
        help="Override input encoding.",
    )
    parse_p.add_argument(
        "--metadata", "-m",
        action="store_true",
        help="Prepend YAML metadata header.",
    )
    parse_p.add_argument(
        "--quiet", "-q", action="store_true",
        help="Suppress warnings on stderr.",
    )
    parse_p.add_argument(
        "--verbose", "-v", action="store_true",
        help="Show debug output on stderr.",
    )
    parse_p.add_argument(
        "--validate", action="store_true",
        help="Validate file content matches extension.",
    )
    parse_p.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT,
        help="Per-conversion timeout in seconds (default: 300).",
    )
    parse_p.add_argument(
        "--max-size",
        type=int,
        default=500,
        help="Max input size in MB (stdin, default: 500).",
    )
    parse_p.add_argument(
        "--max-decompressed-size",
        type=int,
        default=1024,
        help="Max decompressed archive size in MB (default: 1024).",
    )
    parse_p.add_argument(
        "--base-dir",
        help="Restrict file access to this directory.",
    )

    # --- formats subcommand ---
    subparsers.add_parser(
        "formats", help="List supported formats."
    )

    # --- check-deps subcommand ---
    subparsers.add_parser(
        "check-deps", help="Check optional dependencies."
    )

    args = parser.parse_args()
    handlers = {
        "parse": cmd_parse,
        "formats": cmd_formats,
        "check-deps": cmd_check_deps,
    }
    return handlers[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
