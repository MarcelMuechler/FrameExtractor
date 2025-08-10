# FrameExtractor

Simple CLI to extract frames from a video using ffmpeg.

Usage
- Run CLI: `python framegrab.py <input_video> <output_dir> [flags]`.
- Check ffmpeg: `ffmpeg -version` (must be on PATH).

Examples
- All frames (default JPEGs):
  - `python framegrab.py sample.mp4 frames/`
- Range + fps with verbose:
  - `python framegrab.py sample.mp4 out/ --start 00:00:05 --end 00:00:10 --fps 2 --verbose`
- Dry-run (print command only):
  - `python framegrab.py sample.mp4 frames/ --dry-run --pattern "img_%05d.png"`

Flags
- `--start`: Start time (seconds or `HH:MM:SS[.ms]`).
- `--end`: End time (seconds or `HH:MM:SS[.ms]`).
- `--fps`: Fixed frames per second (must be > 0).
- `--pattern`: Output filename pattern ending with `.jpg/.jpeg/.png` (default `frame_%06d.jpg`).
- `--overwrite`: Overwrite existing files (`ffmpeg -y`).
- `--verbose`: Print additional details.
- `--dry-run`: Do not execute ffmpeg; only print the constructed command.

Behavior
- The CLI assembles: `-ss START` (optional), `-i INPUT`, `-to END` (optional), `-vf fps=VALUE` (optional), JPEG quality tweak (`-q:v 2` for `.jpg/.jpeg`), overwrite flag (`-y`/`-n`), and the output pattern.
- On success, prints a summary like: `Wrote N frames to ./frames`.

Troubleshooting
- Error: `ffmpeg not found on PATH. Install it and try again.` → Install ffmpeg and ensure it’s on PATH.
- Invalid time formats → Use numeric seconds or `HH:MM:SS[.ms]`.
