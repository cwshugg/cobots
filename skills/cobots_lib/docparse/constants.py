"""
constants.py - Named constants for the docparse library.

Defines priorities, size limits, timeouts, extension lists, and other
configuration values used across the docparse modules.  All magic numbers
from the architecture are centralised here.
"""

# ---------------------------------------------------------------------------
# Handler priority levels (higher wins when multiple handlers claim the
# same extension).
# ---------------------------------------------------------------------------

PRIORITY_DEFAULT = 0       # MarkItDown wrapper
PRIORITY_CUSTOM = 10       # Gap-filling handlers
PRIORITY_PREMIUM = 20      # Reserved for future high-quality handlers

# ---------------------------------------------------------------------------
# Resource / size limits
# ---------------------------------------------------------------------------

MAX_OUTPUT_SIZE = 50 * 1024 * 1024          # 50 MB output size limit
MAX_DECOMPRESSED_SIZE = 1024 * 1024 * 1024  # 1 GB decompressed size
MAX_COMPRESSION_RATIO = 100                 # Maximum 100:1 ratio
MAX_ARCHIVE_ENTRIES = 10_000                # Maximum ZIP entries
MAX_STDIN_SIZE = 500 * 1024 * 1024          # 500 MB max stdin input
LARGE_FILE_WARNING_THRESHOLD = (
    100 * 1024 * 1024                       # 100 MB warning threshold
)

# ---------------------------------------------------------------------------
# Timeouts (seconds)
# ---------------------------------------------------------------------------

DEFAULT_TIMEOUT = 300       # Per-handler timeout
SUBPROCESS_TIMEOUT = 120    # Default subprocess timeout
LIBREOFFICE_TIMEOUT = 300   # LibreOffice subprocess timeout

# ---------------------------------------------------------------------------
# Temporary file / directory security
# ---------------------------------------------------------------------------

TEMP_DIR_MODE = 0o700       # Owner-only permissions for temp dirs
RECURSION_DEPTH_LIMIT = 1   # Max recursion for archive processing

# ---------------------------------------------------------------------------
# Extensions handled natively by MarkItDown
# ---------------------------------------------------------------------------

MARKITDOWN_EXTENSIONS: list[str] = [
    ".pdf",
    ".docx",
    ".xlsx",
    ".xls",
    ".pptx",
    ".html",
    ".htm",
    ".csv",
    ".json",
    ".xml",
    ".epub",
    ".msg",
    ".txt",
    ".md",
]

# ---------------------------------------------------------------------------
# ZIP-based extensions that need archive pre-validation before delegating
# to MarkItDown or other libraries.
# ---------------------------------------------------------------------------

ZIP_BASED_EXTENSIONS: list[str] = [
    ".docx",
    ".xlsx",
    ".pptx",
    ".epub",
    ".odt",
    ".ods",
    ".odp",
]

# ---------------------------------------------------------------------------
# Shell metacharacters rejected in file paths (defense-in-depth)
# ---------------------------------------------------------------------------

SHELL_METACHARACTERS: set[str] = {
    ";", "|", "&", "$", "`", "(", ")", "{", "}", "<", ">",
}

# ---------------------------------------------------------------------------
# LibreOffice lock file path
# ---------------------------------------------------------------------------

LIBREOFFICE_LOCK_FILENAME = ".docparse_libreoffice.lock"
