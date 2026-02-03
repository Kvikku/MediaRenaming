"""Cleanup and rename video files and folders in a specified directory tree.

Example input:
"Movie.Title.2021.1080p.BluRay.x264.DTS-HD.MA.5.1-FGT.mkv"
"Movie_Title_1992_720p_WEB-DL_x265_AAC_5.1.mkv"
"Movie Title (2021) [1080p] {BluRay} <x264> - FGT.mkv"

Example output:
"Movie Title (2021).mkv"
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


VIDEO_EXTENSIONS = {".mkv", ".mp4", ".avi", ".mov"}

TOKEN_SET = {
    "bluray",
    "brrip",
    "bdrip",
    "webrip",
    "webdl",
    "web-dl",
    "hdrip",
    "dvdrip",
    "remux",
    "x264",
    "x265",
    "h264",
    "h265",
    "hevc",
    "avc",
    "xvid",
    "divx",
    "dts",
    "dtshd",
    "truehd",
    "atmos",
    "aac",
    "ac3",
    "ddp",
    "dd",
    "ma",
    "hdr",
    "sdr",
    "10bit",
    "8bit",
    "proper",
    "repack",
}

NORMALIZED_TOKEN_SET = {re.sub(r"[^a-z0-9]+", "", token.lower()) for token in TOKEN_SET}

RESOLUTION_RE = re.compile(r"^\d{3,4}p$|^\d{1,2}k$")
FRAMERATE_RE = re.compile(r"^\d{2}(?:\.\d{1,3})?fps$")
AUDIO_CHANNEL_RE = re.compile(r"^\d\.\d$")
YEAR_RE = re.compile(r"^(19\d{2}|20\d{2})$")
BRACKET_RE = re.compile(r"\[[^\]]*\]|\{[^\}]*\}|<[^>]*>")
SEPARATOR_RE = re.compile(r"[._]+")
MULTISPACE_RE = re.compile(r"\s+")
TRAILING_GROUP_RE = re.compile(r"\s-\s[\w.]+$")


def normalize_token(token: str) -> str:
    # Normalize tokens for reliable metadata filtering.
    return re.sub(r"[^a-z0-9]+", "", token.lower())


def smart_title(words: list[str]) -> str:
    # Apply simple title casing while preserving acronyms and numbers.
    title_words = []
    for word in words:
        if not word:
            continue
        if any(char.isdigit() for char in word):
            title_words.append(word)
            continue
        if word.isupper() and len(word) <= 4:
            title_words.append(word)
            continue
        title_words.append(word[:1].upper() + word[1:].lower())
    return " ".join(title_words)


def normalize_name(stem: str) -> str:
    # Strip metadata and format the cleaned title with an optional year.
    cleaned = BRACKET_RE.sub(" ", stem)
    cleaned = TRAILING_GROUP_RE.sub("", cleaned)
    cleaned = SEPARATOR_RE.sub(" ", cleaned)
    cleaned = MULTISPACE_RE.sub(" ", cleaned).strip()

    words = []
    year = None
    for raw in cleaned.split(" "):
        token = raw.strip("-_")
        if not token:
            continue
        normalized = normalize_token(token)
        if YEAR_RE.match(token) and year is None:
            year = token
            continue
        if RESOLUTION_RE.match(normalized) or FRAMERATE_RE.match(normalized):
            continue
        if AUDIO_CHANNEL_RE.match(token):
            continue
        if normalized in NORMALIZED_TOKEN_SET:
            continue
        words.append(token)

    title = smart_title(words)
    if not title:
        title = "Unknown Title"

    if year:
        return f"{title} ({year})"
    return title


def unique_target_path(target: Path, reserved: set[Path]) -> Path:
    # Ensure the target filename is unique, appending a numeric suffix if needed.
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
    # Recursively collect video files under the root folder.
    return [path for path in root.rglob("*") if path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS]


def iter_folders(root: Path) -> list[Path]:
    # Collect folders bottom-up to avoid breaking child paths during renames.
    folders = [path for path in root.rglob("*") if path.is_dir()]
    return sorted(folders, key=lambda p: len(p.parts), reverse=True)


def plan_renames(root: Path) -> list[tuple[Path, Path]]:
    # Build a list of source/target rename mappings.
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
    # Build a list of folder rename mappings.
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


def run_renames(mappings: list[tuple[Path, Path]], apply_changes: bool) -> None:
    # Execute or preview renames based on the apply flag.
    if not mappings:
        return

    for source, target in mappings:
        if apply_changes:
            source.rename(target)
            print(f"Renamed: {source} -> {target}")
        else:
            print(f"Dry-run: {source} -> {target}")


def parse_args() -> argparse.Namespace:
    # Parse CLI arguments.
    parser = argparse.ArgumentParser(description="Cleanup and rename video files.")
    parser.add_argument("path", nargs="?", help="Root directory containing video files")
    parser.add_argument("--apply", action="store_true", help="Apply renames (default is dry-run)")
    return parser.parse_args()


def main() -> int:
    # Entry point handling user input, planning, and execution.
    args = parse_args()
    input_path = args.path or input("Enter a folder path: ").strip()
    if not input_path:
        print("No path provided.")
        return 1

    root = Path(input_path).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        print(f"Invalid directory: {root}")
        return 1

    file_mappings = plan_renames(root)
    folder_mappings = plan_folder_renames(root)

    if not file_mappings and not folder_mappings:
        print("No files or folders need renaming.")
        return 0

    run_renames(file_mappings, args.apply)
    run_renames(folder_mappings, args.apply)

    if not args.apply:
        print("Dry-run completed. Re-run with --apply to rename files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())