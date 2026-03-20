"""Interactive terminal UI for media renaming with a modern look."""

from __future__ import annotations

import os
from pathlib import Path

from .planner import find_junk_files, plan_file_renames, plan_folder_renames, plan_organize
from .storage import load_recent_folders, save_recent_folder, record_renames, load_history

# ── ANSI helpers ─────────────────────────────────────────────────────────────

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
ITALIC = "\033[3m"

FG_CYAN = "\033[36m"
FG_GREEN = "\033[32m"
FG_YELLOW = "\033[33m"
FG_RED = "\033[31m"
FG_MAGENTA = "\033[35m"
FG_WHITE = "\033[97m"
FG_GRAY = "\033[90m"

BG_CYAN = "\033[46m"
BG_RED = "\033[41m"


def _enable_ansi() -> None:
    """Enable ANSI escape processing on Windows 10+."""
    if os.name == "nt":
        import ctypes
        kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)


def _c(text: str, *codes: str) -> str:
    return "".join(codes) + text + RESET


def _format_size(size_bytes: int) -> str:
    """Format a byte count as a human-readable string."""
    for unit in ("B", "KB", "MB", "GB"):
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}" if unit != "B" else f"{size_bytes} B"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


# ── Box-drawing helpers ──────────────────────────────────────────────────────

W = 62  # inner width of the box


def _box_top() -> str:
    return f"╔{'═' * W}╗"


def _box_bottom() -> str:
    return f"╚{'═' * W}╝"


def _box_sep() -> str:
    return f"╠{'═' * W}╣"


def _box_row(text: str, pad: int | None = None) -> str:
    """Render a row inside a box. *pad* is the visible char count of *text*."""
    if pad is None:
        pad = len(text)
    spacing = W - pad
    if spacing < 0:
        spacing = 0
    return f"║ {text}{' ' * (spacing - 1)}║"


# ── Shared UI pieces ────────────────────────────────────────────────────────

LOGO = r"""
    __  ___         ___       ____                            _
   /  |/  /__  ____/ (_)___ _/ __ \___  ____  ____ _____ ___(_)___  ____ _
  / /|_/ / _ \/ __  / / __ `/ /_/ / _ \/ __ \/ __ `/ __ `__ / / __ \/ __ `/
 / /  / /  __/ /_/ / / /_/ / _, _/  __/ / / / /_/ / / / / / / / / / / /_/ /
/_/  /_/\___/\__,_/_/\__,_/_/ |_|\___/_/ /_/\__,_/_/ /_/ /_/_/_/ /_/\__, /
                                                                    /____/
"""


def _clear_screen() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def _pause() -> None:
    input(f"\n{_c('  ⏎  Press Enter to continue...', DIM)}")


def _prompt_yes_no(prompt: str, default: bool = True) -> bool:
    hint = _c("Y", BOLD, FG_GREEN) + "/n" if default else "y/" + _c("N", BOLD, FG_RED)
    while True:
        raw = input(f"  {prompt} [{hint}]: ").strip().lower()
        if not raw:
            return default
        if raw in {"y", "yes"}:
            return True
        if raw in {"n", "no"}:
            return False
        print(f"  {_c('⚠', FG_YELLOW)}  Please enter y or n.")


def _run_renames(mappings: list[tuple[Path, Path]], apply_changes: bool) -> list[tuple[Path, Path]]:
    """Execute or preview renames. Returns successfully applied pairs."""
    if not mappings:
        return []
    applied: list[tuple[Path, Path]] = []
    for source, target in mappings:
        if apply_changes:
            try:
                target.parent.mkdir(parents=True, exist_ok=True)
                source.rename(target)
            except OSError as exc:
                print(f"  {_c('✖', FG_RED, BOLD)}  {source.name}")
                print(f"     {_c('⚠', FG_YELLOW)}  {exc}")
                continue
            applied.append((source, target))
            print(f"  {_c('✔', FG_GREEN, BOLD)}  {source.name}")
            print(f"     {_c('➜', FG_CYAN)}  {target.name}")
        else:
            print(f"  {_c('…', FG_YELLOW)}  {source.name}")
            print(f"     {_c('➜', FG_CYAN)}  {target.name}")
    return applied


# ── Header / status ─────────────────────────────────────────────────────────

def _print_header(root: Path | None, apply_changes: bool,
                  file_count: int, folder_count: int, junk_count: int,
                  organize_count: int) -> None:
    print(_c(LOGO, FG_CYAN, BOLD))
    print(_box_top())

    folder_display = str(root) if root else _c("not set", DIM, ITALIC)
    mode_label = (
        _c(" ● LIVE ", BG_RED, FG_WHITE, BOLD)
        if apply_changes
        else _c(" ● DRY-RUN ", BG_CYAN, FG_WHITE, BOLD)
    )

    print(_box_row(f"📂  Folder : {folder_display}", pad=W - 1))
    print(_box_row(f"⚙️   Mode   : {mode_label}", pad=W - 1))
    print(_box_sep())

    files_str = _c(str(file_count), FG_GREEN, BOLD) if file_count else _c("0", DIM)
    folders_str = _c(str(folder_count), FG_GREEN, BOLD) if folder_count else _c("0", DIM)
    junk_str = _c(str(junk_count), FG_RED, BOLD) if junk_count else _c("0", DIM)
    organize_str = _c(str(organize_count), FG_MAGENTA, BOLD) if organize_count else _c("0", DIM)
    print(_box_row(f"🎬  File renames   : {files_str}", pad=W - 1))
    print(_box_row(f"📁  Folder renames : {folders_str}", pad=W - 1))
    print(_box_row(f"📦  Organize loose : {organize_str}", pad=W - 1))
    print(_box_row(f"🗑️   Junk files     : {junk_str}", pad=W - 1))

    print(_box_bottom())


# ── Menu ─────────────────────────────────────────────────────────────────────

MENU_ITEMS = [
    ("1", "📂", "Select / change folder"),
    ("2", "🔄", "Scan folder & refresh plan"),
    ("3", "🎬", "Preview file renames"),
    ("4", "📁", "Preview folder renames"),
    ("5", "📦", "Preview organize (loose files → folders)"),
    ("6", "🗑️", "Preview junk files to delete"),
    ("7", "🔀", "Toggle mode (dry-run / apply)"),
    ("8", "🚀", "Run planned operation"),
    ("9", "📜", "View rename history"),
    ("0", "👋", "Exit"),
]


def _print_menu() -> None:
    print()
    for key, icon, label in MENU_ITEMS:
        num = _c(key, FG_CYAN, BOLD)
        print(f"    {num}  {icon}  {label}")
    print()


# ── Previews ─────────────────────────────────────────────────────────────────

def _print_mappings(mappings: list[tuple[Path, Path]], heading: str, icon: str,
                    limit: int = 30) -> None:
    total = len(mappings)
    print(f"\n  {icon}  {_c(heading, BOLD, FG_CYAN)}  {_c(f'({total} planned)', DIM)}")
    print(f"  {'─' * 58}")

    if not mappings:
        print(f"  {_c('Nothing to do — all names are already clean.', DIM)}")
        return

    for source, target in mappings[:limit]:
        print(f"    {_c('•', FG_GRAY)}  {source.name}")
        print(f"       {_c('➜', FG_GREEN)}  {_c(target.name, FG_GREEN)}")

    if total > limit:
        print(f"\n  {_c(f'… and {total - limit} more', DIM)}")


# ── History display ───────────────────────────────────────────────────────────

def _print_history(limit: int = 20) -> None:
    sessions = load_history()
    total = len(sessions)
    print(f"\n  📜  {_c('Rename history', BOLD, FG_CYAN)}  {_c(f'({total} sessions)', DIM)}")
    print(f"  {'─' * 58}")

    if not sessions:
        print(f"  {_c('No rename history yet.', DIM)}")
        return

    for session in reversed(sessions[-limit:]):
        ts = session.get('timestamp', '?')[:19].replace('T', ' ')
        folder = session.get('folder', '?')
        count = len(session.get('renames', []))
        print(f"    {_c(ts, FG_GRAY)}  {_c(str(count), FG_GREEN, BOLD)} renames")
        print(f"      📂 {folder}")
        for entry in session.get('renames', [])[:5]:
            print(f"        {_c('•', FG_GRAY)}  {entry.get('from', '?')}")
            print(f"           {_c('➜', FG_GREEN)}  {_c(entry.get('to', '?'), FG_GREEN)}")
        remaining = count - 5
        if remaining > 0:
            print(f"        {_c(f'… and {remaining} more', DIM)}")
        print()


# ── Directory prompt ─────────────────────────────────────────────────────────

def _prompt_directory(default_path: Path | None = None) -> Path | None:
    recent = load_recent_folders()
    valid_recent = [f for f in recent if Path(f).is_dir()]

    if valid_recent:
        print(f"\n  {_c('Recent folders:', BOLD, FG_CYAN)}")
        for idx, folder in enumerate(valid_recent, 1):
            print(f"    {_c(str(idx), FG_CYAN, BOLD)}  {folder}")
        print(f"    {_c('0', FG_CYAN, BOLD)}  Enter a new path")
        pick = input(f"\n  Pick a recent folder or 0 for new [{_c('0', DIM)}]: ").strip()
        if pick.isdigit() and 1 <= int(pick) <= len(valid_recent):
            return Path(valid_recent[int(pick) - 1])

    hint = f" {_c(f'[{default_path}]', DIM)}" if default_path else ""
    raw = input(f"  📂  Enter media root directory{hint}: ").strip()

    candidate_raw = raw or (str(default_path) if default_path else "")
    if not candidate_raw:
        print(f"  {_c('⚠', FG_YELLOW)}  No directory entered.")
        return None

    candidate = Path(candidate_raw).expanduser().resolve()
    if not candidate.exists() or not candidate.is_dir():
        print(f"  {_c('✖', FG_RED, BOLD)}  Invalid directory: {candidate}")
        return None

    return candidate


# ── Main loop ────────────────────────────────────────────────────────────────

def launch_interactive_ui(initial_path: str | None = None,
                          apply_default: bool = False) -> int:
    """Run a menu-driven terminal interface for rename operations."""
    _enable_ansi()

    root: Path | None = None
    file_mappings: list[tuple[Path, Path]] = []
    folder_mappings: list[tuple[Path, Path]] = []
    organize_mappings: list[tuple[Path, Path]] = []
    junk_files: list[Path] = []
    apply_changes = apply_default

    if initial_path:
        candidate = Path(initial_path).expanduser().resolve()
        if candidate.exists() and candidate.is_dir():
            root = candidate
            save_recent_folder(root)
            file_mappings = plan_file_renames(root)
            folder_mappings = plan_folder_renames(root)
            organize_mappings = plan_organize(root)
            junk_files = find_junk_files(root)
    else:
        recent = load_recent_folders()
        if recent and Path(recent[0]).is_dir():
            root = Path(recent[0])
            file_mappings = plan_file_renames(root)
            folder_mappings = plan_folder_renames(root)
            organize_mappings = plan_organize(root)
            junk_files = find_junk_files(root)

    while True:
        _clear_screen()
        _print_header(root, apply_changes, len(file_mappings), len(folder_mappings),
                      len(junk_files), len(organize_mappings))
        _print_menu()

        choice = input(f"  {_c('❯', FG_CYAN, BOLD)} Enter choice [0-9]: ").strip()

        # 1 — Select folder
        if choice == "1":
            selected = _prompt_directory(root)
            if selected is not None:
                root = selected
                save_recent_folder(root)
                file_mappings = plan_file_renames(root)
                folder_mappings = plan_folder_renames(root)
                organize_mappings = plan_organize(root)
                junk_files = find_junk_files(root)
                print(f"\n  {_c('✔', FG_GREEN, BOLD)}  Folder selected & plan updated.")
            _pause()
            continue

        # 2 — Refresh scan
        if choice == "2":
            if root is None:
                print(f"  {_c('⚠', FG_YELLOW)}  Set a folder first (option 1).")
            else:
                file_mappings = plan_file_renames(root)
                folder_mappings = plan_folder_renames(root)
                organize_mappings = plan_organize(root)
                junk_files = find_junk_files(root)
                print(f"  {_c('✔', FG_GREEN, BOLD)}  Plan refreshed.")
            _pause()
            continue

        # 3 — Preview files
        if choice == "3":
            _print_mappings(file_mappings, "File rename preview", "🎬")
            _pause()
            continue

        # 4 — Preview folders
        if choice == "4":
            _print_mappings(folder_mappings, "Folder rename preview", "📁")
            _pause()
            continue

        # 5 — Preview organize
        if choice == "5":
            _print_mappings(organize_mappings, "Organize preview (loose files → folders)", "📦")
            _pause()
            continue

        # 6 — Preview junk
        if choice == "6":
            total = len(junk_files)
            print(f"\n  🗑️   {_c('Junk files to delete', BOLD, FG_CYAN)}  {_c(f'({total} found)', DIM)}")
            print(f"  {'─' * 58}")
            if not junk_files:
                print(f"  {_c('No junk files found.', DIM)}")
            else:
                for jf in junk_files[:30]:
                    print(f"    {_c('✖', FG_RED)}  {jf.relative_to(root) if root else jf}")
                if total > 30:
                    print(f"\n  {_c(f'… and {total - 30} more', DIM)}")
            _pause()
            continue

        # 7 — Toggle mode
        if choice == "7":
            apply_changes = not apply_changes
            tag = (
                _c(" LIVE ", BG_RED, FG_WHITE, BOLD)
                if apply_changes
                else _c(" DRY-RUN ", BG_CYAN, FG_WHITE, BOLD)
            )
            print(f"\n  🔀  Mode switched to {tag}")
            _pause()
            continue

        # 8 — Execute
        if choice == "8":
            if root is None:
                print(f"  {_c('⚠', FG_YELLOW)}  Set a folder first (option 1).")
                _pause()
                continue

            if not file_mappings and not folder_mappings and not organize_mappings and not junk_files:
                print(f"  {_c('✔', FG_GREEN)}  Nothing to do — all names look good and no junk found!")
                _pause()
                continue

            if apply_changes:
                ok = _prompt_yes_no(
                    f"{_c('⚠', FG_YELLOW)}  This will rename, organize files & folders and delete junk. Continue?",
                    default=False,
                )
                if not ok:
                    print(f"  {_c('✖', FG_RED)}  Cancelled.")
                    _pause()
                    continue

            print()
            # Organize loose files into folders first
            applied_organize = _run_renames(organize_mappings, apply_changes)
            applied_files = _run_renames(file_mappings, apply_changes)
            applied_folders = _run_renames(folder_mappings, apply_changes)

            # Delete junk files
            deleted_count = 0
            freed_bytes = 0
            for jf in junk_files:
                if apply_changes:
                    try:
                        size = jf.stat().st_size
                        jf.unlink()
                    except OSError as exc:
                        print(f"  {_c('✖', FG_RED, BOLD)}  {jf.name}")
                        print(f"     {_c('⚠', FG_YELLOW)}  {exc}")
                        continue
                    deleted_count += 1
                    freed_bytes += size
                    print(f"  {_c('✔', FG_RED)}  Deleted: {jf.name}  {_c(f'({_format_size(size)})', DIM)}")
                else:
                    try:
                        size = jf.stat().st_size
                        print(f"  {_c('…', FG_YELLOW)}  Would delete: {jf.name}  {_c(f'({_format_size(size)})', DIM)}")
                    except OSError:
                        print(f"  {_c('…', FG_YELLOW)}  Would delete: {jf.name}")

            if not apply_changes:
                print(f"\n  {_c('ℹ', FG_CYAN)}  Dry-run complete. Toggle mode (7) to apply for real.")
            else:
                all_applied = applied_organize + applied_files + applied_folders
                if all_applied:
                    record_renames(root, all_applied)
                total = len(organize_mappings) + len(file_mappings) + len(folder_mappings) + len(junk_files)
                failed = total - len(all_applied) - deleted_count
                if failed:
                    print(f"\n  {_c('⚠', FG_YELLOW, BOLD)}  Done with {failed} failure(s).")
                else:
                    print(f"\n  {_c('🎉', BOLD)}  All done! Renames applied and junk cleaned up.")
                if deleted_count:
                    print(f"  {_c('🗑️', BOLD)}  Deleted {_c(str(deleted_count), FG_RED, BOLD)} junk file(s), freed {_c(_format_size(freed_bytes), FG_GREEN, BOLD)}.")
                file_mappings = plan_file_renames(root)
                folder_mappings = plan_folder_renames(root)
                organize_mappings = plan_organize(root)
                junk_files = find_junk_files(root)
            _pause()
            continue

        # 9 — View history
        if choice == "9":
            _print_history()
            _pause()
            continue

        # 0 — Exit
        if choice == "0":
            print(f"\n  {_c('👋  See you!', FG_CYAN, BOLD)}\n")
            return 0

        print(f"  {_c('⚠', FG_YELLOW)}  Invalid choice — pick a number from 0 to 9.")
        _pause()
