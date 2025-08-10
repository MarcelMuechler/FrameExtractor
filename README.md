# FrameExtractor

Simple CLI and GUI to extract frames from a video using ffmpeg. Requires Python 3.9+ and a system `ffmpeg` available on `PATH`.

Usage
- Run CLI: `python framegrab.py <input_video> <output_dir> [flags]`.
- Check ffmpeg: `ffmpeg -version` (must be on PATH).
 - Run GUI: `python gui_app.py` (ttk-based, stdlib-only).

Examples
- All frames (default JPEGs):
  - `python framegrab.py sample.mp4 frames/`
- Range + fps with verbose:
  - `python framegrab.py sample.mp4 out/ --start 00:00:05 --end 00:00:10 --fps 2 --verbose`
 - Overwrite any existing frames:
   - `python framegrab.py sample.mp4 frames/ --overwrite`
- Dry-run (print command only):
  - `python framegrab.py sample.mp4 frames/ --dry-run --pattern "img_%05d.png"`

Flags
- `--start`: Start time (seconds or `HH:MM:SS[.ms]`).
- `--end`: End time (seconds or `HH:MM:SS[.ms]`).
- `--fps`: Fixed frames per second (must be > 0).
 - `--pattern`: Output filename pattern ending with `.jpg/.jpeg/.png` and containing a `%d` placeholder (e.g., `frame_%06d.jpg`). Default: `frame_%06d.jpg`.
 - `--overwrite`: Overwrite existing files (`ffmpeg -y`).
 - `--verbose`: Print additional details.
 - `--dry-run`: Do not execute ffmpeg; only print the constructed command.

 Behavior
 - Assembles: `-ss START` (optional), `-i INPUT`, `-to END` (optional), `-vf fps=VALUE` (optional), JPEG quality tweak (`-q:v 2` for `.jpg/.jpeg`), overwrite flag (`-y`/`-n`), and the output pattern.
 - `--verbose` raises ffmpeg loglevel to `info` for more output.
 - On success, prints a summary like: `Wrote N frames to ./frames`.
 - Non-zero exit code when ffmpeg fails (propagates `subprocess.run` return code).

Troubleshooting
- Error: `ffmpeg not found on PATH. Install it and try again.` → Install ffmpeg and ensure it’s on PATH.
- Invalid time formats → Use numeric seconds or `HH:MM:SS[.ms]`.

## Development

- Setup: `pip install -r requirements-dev.txt`
- Run tests: `pytest -q`
- Manual checks:
  - All frames: `python framegrab.py sample.mp4 frames/`
  - Range+fps: `python framegrab.py sample.mp4 out/ --start 00:00:05 --end 00:00:10 --fps 2 --verbose`
  - Overwrite: `python framegrab.py sample.mp4 frames/ --overwrite`
  - Dry-run: `python framegrab.py sample.mp4 frames/ --dry-run --pattern "img_%05d.png"`

## GUI

- Toolkit: tkinter + ttk (stdlib only).
- Launch: `python gui_app.py`.
- Inputs: pick Input Video and Output Dir via file dialogs.
 - Options: Start, End, FPS, Pattern with `%d` placeholder; Overwrite, Verbose, Dry-run.
- Preview Command: shows the constructed ffmpeg command (no execution).
- Extract Frames: runs extraction; status pane shows summary/errors.
- Notes: on headless environments (no display), the GUI cannot run; use the CLI instead.

Quality of life
- Source info: shows resolution, source FPS, and duration (via ffprobe).
- FPS guard: if you enter FPS higher than the source FPS, it is limited to the source.
- Estimate: shows an approximate frame count based on range and FPS.
- Open output: quickly open the output folder after a run.
