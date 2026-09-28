"""Runtime paths for source and PyInstaller executions."""

import sys
from pathlib import Path


def resource_root():
    """Return the directory containing bundled or source resources."""

    bundle_root = getattr(sys, "_MEIPASS", None)
    if bundle_root:
        return Path(bundle_root)

    return Path(__file__).resolve().parents[2]


def resource_path(*parts):
    """Resolve a resource path from the application resource root."""

    return resource_root().joinpath(*parts)
