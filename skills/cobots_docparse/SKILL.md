---
name: cobots-docparse-cli
description: CLI for converting documents into readable text (Markdown / plain text).
---

# docparse-cli

A CLI skill for converting documents in a wide range of formats into readable text (Markdown preferred, plain text fallback).

## Description

The `docparse` skill provides a unified interface for extracting text from documents. It wraps the shared `cobots_lib.docparse` library and supports 25 file formats including PDF, Office documents, legacy Office formats, email, markup languages, and data formats.

**Key features:**

* **Markdown-first output** — Structure (headings, tables, lists, links) is preserved as Markdown wherever possible. Plain text is the fallback when structure cannot be inferred.
* **Extensible handler registry** — A priority-based registry selects the best available handler per format. New handlers can be added without modifying the core.
* **Graceful degradation** — Missing optional dependencies produce clear error messages with install instructions; they never crash.
* **Security by default** — Path validation, archive safety checks, subprocess hardening, XML bomb protection, and resource limits are enforced on all input.

## Supported Formats

The skill supports 25 file extensions across 9 handler modules. Handlers are selected by priority — custom (gap-filling) handlers take precedence over the default MarkItDown wrapper when both claim the same extension.

| Extension(s)    | Handler              | System Dependencies     | Output    |
|-----------------|----------------------|-------------------------|-----------|
| `.pdf`          | MarkItDown           | —                       | markdown  |
| `.docx`         | MarkItDown           | —                       | markdown  |
| `.doc`          | Legacy Word          | antiword / catdoc / LO¹ | text²     |
| `.xlsx`         | MarkItDown           | —                       | markdown  |
| `.xls`          | MarkItDown           | —                       | markdown  |
| `.pptx`         | MarkItDown           | —                       | markdown  |
| `.ppt`          | Legacy PowerPoint    | LibreOffice¹            | markdown  |
| `.html`, `.htm` | MarkItDown           | —                       | markdown  |
| `.csv`          | MarkItDown           | —                       | markdown  |
| `.json`         | MarkItDown           | —                       | markdown  |
| `.xml`          | MarkItDown           | —                       | markdown  |
| `.epub`         | MarkItDown           | —                       | markdown  |
| `.msg`          | MarkItDown           | —                       | markdown  |
| `.txt`, `.md`   | MarkItDown           | —                       | markdown  |
| `.rtf`          | RTF (striprtf)       | —                       | text      |
| `.eml`          | EML (stdlib + markdownify) | —                 | markdown  |
| `.odt`          | ODF (odfpy / LO¹)   | —                       | markdown  |
| `.ods`          | ODF (odfpy / LO¹)   | —                       | markdown  |
| `.odp`          | ODF (odfpy / LO¹)   | —                       | markdown  |
| `.yaml`, `.yml` | YAML                 | —                       | markdown  |
| `.rst`          | reStructuredText     | —                       | markdown  |
| `.tex`          | LaTeX                | —                       | markdown  |

¹ *LO = LibreOffice headless. System dependencies are optional; the skill will try available tools in cascading order and report a clear error if none are installed.*

² *Output is plain text when antiword or catdoc is used. When the LibreOffice fallback is used, the file is converted to `.docx` first, producing Markdown output.*

## Usage

```bash
# Parse a document to stdout.
python3 docparse-cli.py parse report.pdf

# Write output to a file.
python3 docparse-cli.py parse report.pdf --output report.md

# Include a YAML metadata header in the output.
python3 docparse-cli.py parse report.pdf --metadata

# Read from stdin (provide a filename hint for format detection).
cat report.pdf | python3 docparse-cli.py parse - --filename report.pdf

# Force plain text output instead of markdown.
python3 docparse-cli.py parse slides.pptx --format text

# Restrict file access to a specific directory (security sandboxing).
python3 docparse-cli.py parse report.pdf --base-dir /safe/documents/

# Validate that file content matches its extension.
python3 docparse-cli.py parse data.xlsx --validate

# List all supported formats and their availability.
python3 docparse-cli.py formats

# Check status of optional system dependencies.
python3 docparse-cli.py check-deps
```

## Subcommands

### `parse`

Convert a document to text (Markdown or plain text).

```
docparse-cli.py parse <FILE> [options]
docparse-cli.py parse - [options]          # Read from stdin
```

* `FILE` *(required)* — Path to the document, or `-` to read from stdin.
* `--output`, `-o` *(optional)* — Write output to a file instead of stdout.
* `--format`, `-f` *(optional)* — Output format: `markdown`, `text`, or `auto` (default: `auto`). When `auto`, the handler's native format is used.
* `--filename` *(optional)* — Filename hint for format detection when reading from stdin.
* `--encoding` *(optional)* — Override the input file encoding (e.g. `latin-1`). Falls back to UTF-8 with replacement on failure.
* `--metadata`, `-m` *(optional)* — Prepend a YAML front-matter metadata header to the output.
* `--quiet`, `-q` *(optional)* — Suppress warnings on stderr.
* `--verbose`, `-v` *(optional)* — Show debug output on stderr.
* `--validate` *(optional)* — Cross-check the file extension against magic-byte detection.
* `--timeout` *(optional)* — Per-conversion timeout in seconds (default: `300`).
* `--max-size` *(optional)* — Maximum input size in MB when reading from stdin (default: `500`).
* `--max-decompressed-size` *(optional)* — Maximum decompressed archive size in MB (default: `1024`).
* `--base-dir` *(optional)* — Restrict file access to paths within this directory. Symlinks are resolved before the check.

**Output (success):** Converted text to stdout (or to the file specified by `--output`), exit `0`.

**Output (failure):** `Error: <description>` to stderr, exit `1`.

### `formats`

Prints a table of all supported formats, their handler name, and whether the handler is currently available (i.e. its dependencies are installed).

```
$ python3 docparse-cli.py formats
Extension    Handler                   Available
------------ ------------------------- ----------
.csv         MarkItDown                yes
.doc         Legacy Word               yes
.docx        MarkItDown                yes
...
```

### `check-deps`

Prints the status of all optional system dependencies.

```
$ python3 docparse-cli.py check-deps
Dependency      Status       Required For                             Install
--------------- ------------ ---------------------------------------- ------------------------------
antiword        installed    .doc (primary)                           apt install antiword
catdoc          missing      .doc (alternative)                       apt install catdoc
libreoffice     installed    .doc, .ppt, .odt/.ods/.odp (fallback)   apt install libreoffice
tesseract       missing      OCR for scanned PDFs                     apt install tesseract-ocr
```

## Library API

Other skills and agents can import and use docparse programmatically via the `cobots_lib.docparse` module.

### Quick Start

```python
from cobots_lib.docparse import parse_file, parse_bytes, supported_formats

# Parse a file — returns a ParseResult.
result = parse_file("/path/to/report.pdf")
print(result.content)          # Markdown text
print(result.output_format)    # "markdown" or "text"
print(result.metadata)         # {"word_count": 1234, ...}

# Parse with security sandboxing (recommended for untrusted paths).
result = parse_file(
    user_provided_path,
    base_dir="/safe/documents/",
    timeout=60,
)

# Parse raw bytes (e.g. downloaded content).
result = parse_bytes(pdf_data, filename="report.pdf")

# List all supported extensions.
print(supported_formats())     # [".csv", ".doc", ".docx", ...]
```

### Using `DocumentConverter` Directly

For more control, create a `DocumentConverter` instance:

```python
from cobots_lib.docparse import DocumentConverter

converter = DocumentConverter()

# Convert a file.
result = converter.convert("/path/to/document.docx", timeout=120)

# Convert raw bytes.
result = converter.convert_bytes(data, "spreadsheet.xlsx")

# Inspect handler availability.
for info in converter.handler_status():
    print(f"{info['name']}: {info['extensions']} — available={info['available']}")
```

### Error Handling

All docparse exceptions inherit from `DocparseError`, so callers can catch broadly or specifically:

```python
from cobots_lib.docparse import (
    parse_file,
    DocparseError,
    UnsupportedFormatError,
    DependencyMissingError,
    ParseError,
    DetectionError,
    SecurityError,
)

try:
    result = parse_file("unknown.xyz")
except UnsupportedFormatError:
    print("Format not supported")
except DependencyMissingError as exc:
    print(f"Missing dependency: {exc}")
except DetectionError:
    print("Could not determine format")
except SecurityError:
    print("Security check failed")
except ParseError:
    print("Parsing failed")
except DocparseError:
    print("General docparse error")
```

### `ParseResult` Attributes

The `parse_file()` and `parse_bytes()` functions return a `ParseResult` dataclass:

| Attribute       | Type             | Description                                                  |
|-----------------|------------------|--------------------------------------------------------------|
| `content`       | `str`            | The extracted text (Markdown or plain text).                 |
| `output_format` | `str`            | `"markdown"` or `"text"`.                                    |
| `source_path`   | `str`            | Original file path, or `"<stdin>"` / `"<bytes>"`.            |
| `source_format` | `str`            | Detected extension (e.g. `".pdf"`).                          |
| `handler_name`  | `str`            | Which handler produced the result (e.g. `"MarkItDown"`).     |
| `metadata`      | `dict[str, Any]` | Metadata dict. Always includes `word_count`. PII fields (`title`, `author`, `date`, `subject`) are only populated when `include_metadata=True`. Currently, `subject` and `date` are populated for `.eml` files. `title` and `author` are reserved for future handler support. |
| `warnings`      | `list[str]`      | Non-fatal warnings collected during parsing.                 |

## Security Considerations

* **Path sandboxing** — Use `--base-dir` (CLI) or `base_dir=` (API) when parsing files from untrusted sources. Symlinks are resolved via `os.path.realpath()` before containment checks.
* **Archive validation** — ZIP-based formats (`.docx`, `.xlsx`, `.pptx`, `.epub`, `.odt`, `.ods`, `.odp`) are validated against decompression size limits, compression ratio limits, entry count limits, and path traversal before processing.
* **XML bomb protection** — ODF files are pre-validated with `defusedxml` to block entity expansion (billion-laughs) and DTD attacks before `odfpy` processes them.
* **Subprocess hardening** — All external tool invocations use array-form arguments with `shell=False`, argument terminators (`--`), and enforced timeouts.
* **LibreOffice profile hardening** — LibreOffice is run with a temporary profile that sets `MacroSecurityLevel=3` (Very High), disabling macro execution.
* **Filename sanitisation** — Filenames containing shell metacharacters (`;`, `|`, `&`, `$`, `` ` ``, etc.) are rejected.
* **Metadata and PII** — Metadata fields that may contain PII (`title`, `author`, `date`, `subject`) are only populated when explicitly requested via `--metadata` / `include_metadata=True`.
* **Resource limits** — Output is capped at 50 MB, stdin input at 500 MB, and decompressed archives at 1 GB by default. All values are configurable.

## Optional System Dependencies

All Python dependencies are installed via `requirements.txt`. The following *system-level* tools are optional and expand format support:

| Dependency   | Required For                            | Install Command            |
|--------------|----------------------------------------|----------------------------|
| `antiword`   | `.doc` files (primary tool)            | `apt install antiword`     |
| `catdoc`     | `.doc` files (fallback if no antiword) | `apt install catdoc`       |
| `libreoffice`| `.doc`, `.ppt`, `.odt/.ods/.odp` (fallback) | `apt install libreoffice`  |
| `tesseract`  | OCR for scanned PDFs                   | `apt install tesseract-ocr`|

For `.doc` files, the handler tries tools in order: **antiword → catdoc → LibreOffice**. At least one must be installed. For `.ppt` files, **LibreOffice is required**. For `.odt/.ods/.odp` files, the **odfpy** Python package is the primary engine; LibreOffice is the fallback.

## Return Codes

| Exit Code | Meaning                   |
|-----------|---------------------------|
| `0`       | Success                   |
| `1`       | Error (see stderr output) |

## Troubleshooting

* **"No handler for format '…'"** — The file extension is not recognised. Run `formats` to see all supported extensions.
* **"Handlers for '…' exist but none are available"** — The handler's Python package is missing. Reinstall dependencies from `requirements.txt`.
* **"File does not exist"** — Check the file path. Relative paths are resolved from the current working directory. This is reported as a `SecurityError` (subclass of `DocparseError`).
* **"Path escapes base directory"** — The resolved path (after following symlinks) is outside the `--base-dir` restriction.
* **"LibreOffice conversion failed"** — Ensure LibreOffice is installed and `libreoffice` is on `PATH`. Check stderr for details.
* **"Handler '…' timed out"** — The conversion exceeded the timeout. Increase it with `--timeout` or reduce the file size.
* **"Stdin input exceeds … MB limit"** — The piped input is too large. Increase the limit with `--max-size` or write the file to disk and parse by path.
* **"Archive total decompressed size exceeds limit"** — The ZIP-based file expands beyond the safety limit. Increase it with `--max-decompressed-size` if the file is trusted.
* **"Malicious XML detected in ODF entry"** — The ODF file contains a potentially malicious XML payload (entity expansion, DTD, or external references). Do not process this file.
