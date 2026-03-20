"""Compatibility entrypoint for the media renaming CLI."""

from __future__ import annotations

import sys

from media_renaming.cli import main


if __name__ == "__main__":
    sys.exit(main())