"""Filesystem discovery and rename planning."""

from __future__ import annotations

from pathlib import Path

from .constants import VIDEO_EXTENSIONS
from .normalization import normalize_name


def unique_target_path(target: Path, reserved: set[Path]) -> Path:
    """Ensure the target path is unique with an optional numeric suffix."""
    if target not in reserved and not target.exists():
        reserved.add(target)
        return target

    base = target.stem
    suffix = target.suffix
    counter = 1
    while True:
        candidate = target.with_name(f"{base} ({counter}){suffix}")
        if candidate not in reserved and not candidate.exists():
            reserved.add(candidate)
            return candidate
        counter += 1


def iter_video_files(root: Path) -> list[Path]:
    """Recursively collect video files under the root folder."""
    return [path for path in root.rglob("*") if path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS]


def iter_folders(root: Path) -> list[Path]:
    """Collect folders bottom-up to avoid breaking child paths during renames."""
    folders = [path for path in root.rglob("*") if path.is_dir()]
    return sorted(folders, key=lambda p: len(p.parts), reverse=True)


def plan_file_renames(root: Path) -> list[tuple[Path, Path]]:
    """Build source/target mappings for file renames."""
    mappings = []
    reserved: set[Path] = set()
    for path in iter_video_files(root):
        normalized = normalize_name(path.stem)
        target = path.with_name(f"{normalized}{path.suffix}")
        target = unique_target_path(target, reserved)
        if path == target:
            continue
        mappings.append((path, target))
    return mappings


def plan_folder_renames(root: Path) -> list[tuple[Path, Path]]:
    """Build source/target mappings for folder renames."""
    mappings = []
    reserved: set[Path] = set()
    for path in iter_folders(root):
        if path == root:
            continue
        normalized = normalize_name(path.name)
        target = path.with_name(normalized)
        target = unique_target_path(target, reserved)
        if path == target:
            continue
        mappings.append((path, target))
    return mappings
