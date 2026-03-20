"""Filesystem discovery and rename planning."""

from __future__ import annotations

from pathlib import Path

from .constants import SUBTITLE_EXTENSIONS, VIDEO_EXTENSIONS
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


def _find_subtitles(video_path: Path) -> list[Path]:
    """Find subtitle files that share the same stem as the video."""
    stem = video_path.stem
    return [
        p for p in video_path.parent.iterdir()
        if p.is_file()
        and p.stem == stem
        and p.suffix.lower() in SUBTITLE_EXTENSIONS
    ]


def plan_file_renames(root: Path) -> list[tuple[Path, Path]]:
    """Build source/target mappings for file renames (videos + sidecars)."""
    mappings = []
    reserved: set[Path] = set()
    for path in iter_video_files(root):
        normalized = normalize_name(path.stem)
        target = path.with_name(f"{normalized}{path.suffix}")
        target = unique_target_path(target, reserved)
        if path.name == target.name:
            continue
        mappings.append((path, target))
        # Rename matching subtitle files alongside the video
        for sub in _find_subtitles(path):
            sub_target = sub.with_name(f"{target.stem}{sub.suffix}")
            sub_target = unique_target_path(sub_target, reserved)
            if sub.name != sub_target.name:
                mappings.append((sub, sub_target))
    return mappings


def find_junk_files(root: Path) -> list[Path]:
    """Find non-video, non-subtitle files in directories that contain videos."""
    keep_extensions = VIDEO_EXTENSIONS | SUBTITLE_EXTENSIONS
    video_dirs: set[Path] = set()
    for path in iter_video_files(root):
        video_dirs.add(path.parent)

    junk: list[Path] = []
    for directory in video_dirs:
        for path in directory.iterdir():
            if path.is_file() and path.suffix.lower() not in keep_extensions:
                junk.append(path)
    return sorted(junk)


def plan_organize(root: Path) -> list[tuple[Path, Path]]:
    """Plan moves for loose video (and subtitle) files in root into their own folders."""
    keep_extensions = VIDEO_EXTENSIONS | SUBTITLE_EXTENSIONS
    mappings = []
    reserved: set[Path] = set()

    # Collect loose video files sitting directly in the root
    loose_videos = [
        p for p in root.iterdir()
        if p.is_file() and p.suffix.lower() in VIDEO_EXTENSIONS
    ]

    for video in loose_videos:
        folder_name = normalize_name(video.stem)
        target_dir = root / folder_name
        target = target_dir / video.name
        target = unique_target_path(target, reserved)
        mappings.append((video, target))

        # Move matching subtitle files alongside the video
        for sub in _find_subtitles(video):
            sub_target = target_dir / sub.name
            sub_target = unique_target_path(sub_target, reserved)
            mappings.append((sub, sub_target))

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
        if path.name == target.name:
            continue
        mappings.append((path, target))
    return mappings
