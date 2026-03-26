"""
venv.py - Virtual environment bootstrap for cobots skills.

Provides a function to activate the shared venv's site-packages so that
dependencies installed via `setup-venv.sh` / `setup-venv.ps1` are available
at import time.
"""

import glob
import os
import site
import sys


# Name of the virtual environment directory under `skills/`.
VENV_DIR_NAME = ".venv"


def activate_venv() -> None:
    """Adds the shared venv's site-packages to `sys.path`.

    Locates the `.venv` directory relative to the `skills/` directory
    (one level above any skill folder) and adds its site-packages so
    that installed dependencies (e.g. pyyaml) are importable.
    """
    # The skills/ directory is one level above this module's directory.
    skills_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
    venv_dir = os.path.join(skills_dir, VENV_DIR_NAME)

    if not os.path.isdir(venv_dir):
        return

    # Determine site-packages path (platform-dependent).
    if sys.platform == "win32":
        site_packages = os.path.join(venv_dir, "Lib", "site-packages")
    else:
        # Match the Python version directory (e.g. python3.12).
        pattern = os.path.join(venv_dir, "lib", "python*", "site-packages")
        matches = glob.glob(pattern)
        site_packages = matches[0] if matches else None

    if site_packages and os.path.isdir(site_packages):
        site.addsitedir(site_packages)
