# FrameExtractor

Simple CLI to extract frames from a video using ffmpeg. Requires Python 3.9+ and a system `ffmpeg` available on `PATH`.

Usage
- Run CLI: `python framegrab.py <input_video> <output_dir> [flags]`.
- Check ffmpeg: `ffmpeg -version` (must be on PATH).

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

## GUI Wireframe (Planned)

The GUI uses tkinter (stdlib) and reuses the core `extract_frames(...)` function from `framegrab.py`.

Wireframe

```
+--------------------------------------------------------------+
| FrameExtractor                                              |
|--------------------------------------------------------------|
| Input Video:  [ /path/to/video.mp4                 ] [Browse]|
| Output Dir:   [ /path/to/output/frames             ] [Browse]|
|                                                              |
| Start: [ 00:00:05 ]   End: [ 00:00:10 ]   FPS: [ 2.0 ]       |
| Pattern: [ frame_%06d.jpg ]                                   |
|                                                              |
| [ ] Overwrite existing   [ ] Verbose logs   [ ] Dry-run       |
|                                                              |
| [ Preview Command ]                     [ Extract Frames ]    |
|--------------------------------------------------------------|
| Status / Output                                              |
| ffmpeg -hide_banner -loglevel info -ss 00:00:05 -i ...       |
| Wrote 10 frames to /path/to/output/frames                    |
|                                                              |
| (Errors and validation messages appear here)                 |
+--------------------------------------------------------------+
```

Behavior
- Inputs: validate with existing helpers; disable Extract until valid.
- Preview: shows constructed ffmpeg command in the Status area (no execution).
- Extract: calls `extract_frames(...)`; prints summary or errors in Status.
- Verbose: sets `-loglevel info` and prints extra details.
- Dry-run: shows command without writing files.
- Overwrite: maps to `-y`; unchecked maps to `-n` (default).

Notes
- No external dependencies; tkinter only.
- Progress bars are out of scope for MVP; may be added later.
- GUI entrypoint: `python gui_app.py` (placeholder exists; UI TBA).

## GUI Usage (MVP)

- Launch: `python gui_app.py`
- Pick an input video and output directory, set optional Start/End/FPS/Pattern.
- Options: enable Overwrite, Verbose, or Dry-run as needed.
- Preview Command prints the constructed ffmpeg invocation without executing.
- Extract Frames runs the extraction and prints a summary in the Status area.

Notes:
- On headless environments (no display), the GUI cannot run; use the CLI.
