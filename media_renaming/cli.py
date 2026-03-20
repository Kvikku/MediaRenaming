"""CLI orchestration for planning and executing renames."""

from __future__ import annotations

import argparse
from pathlib import Path

from .planner import find_junk_files, plan_file_renames, plan_folder_renames
from .storage import record_renames
from .tui import launch_interactive_ui


def _format_size(size_bytes: int) -> str:
    """Format a byte count as a human-readable string."""
    for unit in ("B", "KB", "MB", "GB"):
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}" if unit != "B" else f"{size_bytes} B"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def run_renames(mappings: list[tuple[Path, Path]], apply_changes: bool) -> list[tuple[Path, Path]]:
    """Execute or preview renames based on the apply flag.

    Returns the list of successfully applied rename pairs.
    """
    if not mappings:
        return []

    applied: list[tuple[Path, Path]] = []
    for source, target in mappings:
        if apply_changes:
            try:
                source.rename(target)
            except OSError as exc:
                print(f"FAILED: {source} -> {target}  ({exc})")
                continue
            applied.append((source, target))
            print(f"Renamed: {source} -> {target}")
        else:
            print(f"Dry-run: {source} -> {target}")
    return applied


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Cleanup and rename video files.")
    parser.add_argument("path", nargs="?", help="Root directory containing video files")
    parser.add_argument("--apply", action="store_true", help="Apply renames (default is dry-run)")
    parser.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        help="Open interactive terminal UI",
    )
    return parser.parse_args()


def main() -> int:
    """Handle user input, planning, and rename execution."""
    args = parse_args()
    if args.interactive or not args.path:
        return launch_interactive_ui(initial_path=args.path, apply_default=args.apply)

    input_path = args.path
    if not input_path:
        print("No path provided.")
        return 1

    root = Path(input_path).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        print(f"Invalid directory: {root}")
        return 1

    file_mappings = plan_file_renames(root)
    folder_mappings = plan_folder_renames(root)
    junk_files = find_junk_files(root)

    if not file_mappings and not folder_mappings and not junk_files:
        print("No files or folders need renaming and no junk found.")
        return 0

    applied_files = run_renames(file_mappings, args.apply)
    applied_folders = run_renames(folder_mappings, args.apply)

    # Delete junk files
    deleted_count = 0
    freed_bytes = 0
    for jf in junk_files:
        if args.apply:
            try:
                size = jf.stat().st_size
                jf.unlink()
            except OSError as exc:
                print(f"FAILED to delete: {jf}  ({exc})")
                continue
            deleted_count += 1
            freed_bytes += size
            print(f"Deleted: {jf}  ({_format_size(size)})")
        else:
            try:
                size = jf.stat().st_size
                print(f"Dry-run: would delete {jf}  ({_format_size(size)})")
            except OSError:
                print(f"Dry-run: would delete {jf}")

    if args.apply:
        all_applied = applied_files + applied_folders
        if all_applied:
            record_renames(root, all_applied)
        if deleted_count:
            print(f"Deleted {deleted_count} junk file(s), freed {_format_size(freed_bytes)}.")
    else:
        print("Dry-run completed. Re-run with --apply to rename files and delete junk.")
    return 0
