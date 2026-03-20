"""Persistent storage for recent folders and rename history.

Data is stored as JSON under the platform-appropriate app data directory:
  - Windows: %APPDATA%/MediaRenaming/
  - macOS:   ~/Library/Application Support/MediaRenaming/
  - Linux:   ~/.local/share/MediaRenaming/
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

APP_NAME = "MediaRenaming"
MAX_RECENT_FOLDERS = 10


def _data_dir() -> Path:
    """Return the app data directory, creating it if necessary."""
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    elif os.uname().sysname == "Darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))

    directory = base / APP_NAME
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def _read_json(path: Path) -> dict | list:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _write_json(path: Path, data: dict | list) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


# ── Recent folders ───────────────────────────────────────────────────────────

def _recent_folders_path() -> Path:
    return _data_dir() / "recent_folders.json"


def load_recent_folders() -> list[str]:
    """Return a list of recently used folder paths (most recent first)."""
    data = _read_json(_recent_folders_path())
    if isinstance(data, dict):
        return data.get("folders", [])
    return []


def save_recent_folder(folder: str | Path) -> None:
    """Add *folder* to the top of the recent folders list (deduped, capped)."""
    folder_str = str(Path(folder).resolve())
    folders = load_recent_folders()

    # Remove duplicates (case-insensitive on Windows)
    if os.name == "nt":
        folders = [f for f in folders if f.lower() != folder_str.lower()]
    else:
        folders = [f for f in folders if f != folder_str]

    folders.insert(0, folder_str)
    folders = folders[:MAX_RECENT_FOLDERS]
    _write_json(_recent_folders_path(), {"folders": folders})


# ── Rename history ───────────────────────────────────────────────────────────

def _history_path() -> Path:
    return _data_dir() / "rename_history.json"


def load_history() -> list[dict]:
    """Return the full rename history (list of session records)."""
    data = _read_json(_history_path())
    if isinstance(data, dict):
        return data.get("sessions", [])
    return []


def record_renames(folder: str | Path,
                   mappings: list[tuple[Path, Path]]) -> None:
    """Append a rename session to the history log."""
    if not mappings:
        return

    sessions = load_history()
    session = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "folder": str(Path(folder).resolve()),
        "renames": [
            {"from": str(src.name), "to": str(tgt.name)}
            for src, tgt in mappings
        ],
    }
    sessions.append(session)
    _write_json(_history_path(), {"sessions": sessions})
