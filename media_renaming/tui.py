"""Simple interactive terminal UI for media renaming."""

from __future__ import annotations

import os
from pathlib import Path

from .planner import plan_file_renames, plan_folder_renames


def _run_renames(mappings: list[tuple[Path, Path]], apply_changes: bool) -> None:
    """Execute or preview renames based on the apply flag."""
    if not mappings:
        return

    for source, target in mappings:
        if apply_changes:
            source.rename(target)
            print(f"Renamed: {source} -> {target}")
        else:
            print(f"Dry-run: {source} -> {target}")


def _clear_screen() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def _pause() -> None:
    input("\nPress Enter to continue...")


def _prompt_yes_no(prompt: str, default: bool = True) -> bool:
    default_hint = "Y/n" if default else "y/N"
    while True:
        raw = input(f"{prompt} [{default_hint}]: ").strip().lower()
        if not raw:
            return default
        if raw in {"y", "yes"}:
            return True
        if raw in {"n", "no"}:
            return False
        print("Please enter y or n.")


def _print_title() -> None:
    print("=" * 64)
    print("MediaRenaming Interactive Terminal UI")
    print("=" * 64)


def _print_mappings(mappings: list[tuple[Path, Path]], heading: str, limit: int = 30) -> None:
    print(f"\n{heading} ({len(mappings)} planned)")
    print("-" * 64)
    if not mappings:
        print("No changes planned.")
        return

    shown = mappings[:limit]
    for source, target in shown:
        print(f"- {source.name}")
        print(f"  -> {target.name}")

    if len(mappings) > limit:
        print(f"\n... and {len(mappings) - limit} more")


def _prompt_directory(default_path: Path | None = None) -> Path | None:
    default_str = f" [{default_path}]" if default_path else ""
    raw = input(f"Enter media root directory{default_str}: ").strip()

    candidate_raw = raw or (str(default_path) if default_path else "")
    if not candidate_raw:
        print("No directory entered.")
        return None

    candidate = Path(candidate_raw).expanduser().resolve()
    if not candidate.exists() or not candidate.is_dir():
        print(f"Invalid directory: {candidate}")
        return None

    return candidate


def launch_interactive_ui(initial_path: str | None = None, apply_default: bool = False) -> int:
    """Run a lightweight menu-driven terminal interface for rename operations."""
    root: Path | None = None
    file_mappings: list[tuple[Path, Path]] = []
    folder_mappings: list[tuple[Path, Path]] = []
    apply_changes = apply_default

    if initial_path:
        candidate = Path(initial_path).expanduser().resolve()
        if candidate.exists() and candidate.is_dir():
            root = candidate
            file_mappings = plan_file_renames(root)
            folder_mappings = plan_folder_renames(root)

    while True:
        _clear_screen()
        _print_title()

        print(f"Current folder: {root if root else '(not set)'}")
        print(f"Mode: {'Apply changes' if apply_changes else 'Dry-run preview'}")
        print(f"File renames planned: {len(file_mappings)}")
        print(f"Folder renames planned: {len(folder_mappings)}")

        print("\nChoose an option:")
        print("1) Select or change folder")
        print("2) Scan folder and refresh plan")
        print("3) Preview file rename plan")
        print("4) Preview folder rename plan")
        print("5) Toggle mode (dry-run/apply)")
        print("6) Run planned operation")
        print("7) Exit")

        choice = input("\nEnter choice [1-7]: ").strip()

        if choice == "1":
            selected = _prompt_directory(root)
            if selected is not None:
                root = selected
                file_mappings = plan_file_renames(root)
                folder_mappings = plan_folder_renames(root)
                print("Folder selected and plan updated.")
            _pause()
            continue

        if choice == "2":
            if root is None:
                print("Set a folder first.")
            else:
                file_mappings = plan_file_renames(root)
                folder_mappings = plan_folder_renames(root)
                print("Plan refreshed.")
            _pause()
            continue

        if choice == "3":
            _print_mappings(file_mappings, "File rename preview")
            _pause()
            continue

        if choice == "4":
            _print_mappings(folder_mappings, "Folder rename preview")
            _pause()
            continue

        if choice == "5":
            apply_changes = not apply_changes
            print(f"Mode changed to: {'Apply changes' if apply_changes else 'Dry-run preview'}")
            _pause()
            continue

        if choice == "6":
            if root is None:
                print("Set a folder first.")
                _pause()
                continue

            if not file_mappings and not folder_mappings:
                print("No files or folders need renaming.")
                _pause()
                continue

            if apply_changes:
                ok = _prompt_yes_no("This will rename files and folders. Continue?", default=False)
                if not ok:
                    print("Cancelled.")
                    _pause()
                    continue

            _run_renames(file_mappings, apply_changes)
            _run_renames(folder_mappings, apply_changes)
            if not apply_changes:
                print("\nDry-run completed. Toggle mode to apply real changes.")
            else:
                print("\nRename operation completed.")
                file_mappings = plan_file_renames(root)
                folder_mappings = plan_folder_renames(root)
            _pause()
            continue

        if choice == "7":
            return 0

        print("Invalid choice. Please pick a number from 1 to 7.")
        _pause()
