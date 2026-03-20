"""CLI orchestration for planning and executing renames."""

from __future__ import annotations

import argparse
from pathlib import Path

from .planner import plan_file_renames, plan_folder_renames
from .tui import launch_interactive_ui


def run_renames(mappings: list[tuple[Path, Path]], apply_changes: bool) -> None:
    """Execute or preview renames based on the apply flag."""
    if not mappings:
        return

    for source, target in mappings:
        if apply_changes:
            source.rename(target)
            print(f"Renamed: {source} -> {target}")
        else:
            print(f"Dry-run: {source} -> {target}")


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

    if not file_mappings and not folder_mappings:
        print("No files or folders need renaming.")
        return 0

    run_renames(file_mappings, args.apply)
    run_renames(folder_mappings, args.apply)

    if not args.apply:
        print("Dry-run completed. Re-run with --apply to rename files.")
    return 0
