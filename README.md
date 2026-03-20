# MediaRenaming

Clean up video file and folder names by stripping common release metadata and formatting titles consistently.

## Features
- Removes common scene metadata like codecs, audio formats, resolutions, and release tags.
- Normalizes separators and brackets in names.
- Keeps the first detected year and formats titles as "Title (Year)".
- Supports dry-run previews before applying renames.

## Requirements
- Python 3.10+ (uses type annotations compatible with 3.10)

## Project Structure
```text
MediaRenaming/
	Rename.py
	media_renaming/
		__init__.py
		cli.py
		constants.py
		normalization.py
		planner.py
```

- `Rename.py` remains as a compatibility entrypoint.
- Core logic now lives in small focused modules under `media_renaming/`.

## Usage
Dry-run (default):
```bash
python Rename.py "C:\\Path\\To\\Media"
```

Apply changes:
```bash
python Rename.py "C:\\Path\\To\\Media" --apply
```

Module execution (optional):
```bash
python -m media_renaming.cli "C:\\Path\\To\\Media" --apply
```

If no path is provided, the script prompts for one interactively.

## Examples
Input:
- `Movie.Title.2021.1080p.BluRay.x264.DTS-HD.MA.5.1-FGT.mkv`
- `Movie_Title_1992_720p_WEB-DL_x265_AAC_5.1.mkv`
- `Movie Title (2021) [1080p] {BluRay} <x264> - FGT.mkv`

Output:
- `Movie Title (2021).mkv`

## Notes
- Video extensions supported: `.mkv`, `.mp4`, `.avi`, `.mov`.
- Folder names are also normalized after files to avoid path conflicts.

## Safety
Run without `--apply` first to review the planned changes.
