# Repository Guidelines

## Scope Update: Add GUI
- We are adding a simple desktop GUI for frame extraction using only Python stdlib (tkinter) and system ffmpeg (no external Python deps).
- The GUI is a thin layer over the existing core logic: assemble args, validate input, build and run the ffmpeg command, and summarize results.

## GUI Plan (High-Level)
- MVP Features: pick input file, pick output directory, start/end time, fps, pattern (with `%d`), overwrite, verbose, dry-run; show summary and basic errors.
- Toolkit: tkinter (stdlib); use filedialogs for inputs, messageboxes for errors.
- Behavior: same defaults as CLI; reuse validation and command-building logic.
- Compatibility: Python 3.9+; rely on system ffmpeg on PATH.

## GUI Tasks (Roadmap)
- Define UI layout and flows (inputs, actions, results).
- Factor core operations into importable functions (no CLI-only side effects).
- Implement tkinter UI (no external deps) wiring to core functions.
- Handle errors and validation with messageboxes; surface ffmpeg failures.
- Add minimal GUI tests (import/open/close) and thorough core logic tests.
- Update README with GUI usage, screenshots optional.
- Package/run: `python gui_app.py` entry; keep CLI unchanged.

## Pre-Work Checklist
- Before coding, run `git status` and ensure there are no uncommitted changes you might overwrite.
- Pull the latest changes: `git pull --rebase origin main` (or your active branch).
- Check open pull requests and align your work (avoid duplicating or conflicting changes).
- Always clean up temporary directories and files you create during testing (e.g., `frames_smoke/`, `out_smoke/`) before finishing your work.

## Project Structure & Module Organization
- `framegrab.py`: Core extraction logic and CLI entrypoint; functions are importable for GUI reuse.
- `gui_app.py` (planned): tkinter-based GUI entrypoint that calls functions from `framegrab.py`.
- `README.md`: Usage, examples, and troubleshooting.
- `.gitignore`: Ignore `__pycache__/`, virtualenvs, and output dirs (e.g., `frames/`, `out/`).
- No external Python deps; rely on stdlib and system `ffmpeg`.

## Build, Test, and Development Commands
- Run CLI: `python framegrab.py <input_video> <output_dir> [flags]`.
- Check ffmpeg: `ffmpeg -version` (must be on PATH).
- Run tests: `pytest -q` (install via `pip install -r requirements-dev.txt`).
- Manual test (all frames): `python framegrab.py sample.mp4 frames/`.
- Manual test (range + fps): `python framegrab.py sample.mp4 out/ --start 00:00:05 --end 00:00:10 --fps 2 --verbose`.
- GUI (planned): `python gui_app.py`.

## Coding Style & Naming Conventions
- Python 3.9+; 4-space indentation; keep lines readable (~100 cols).
- Follow PEP 8 and PEP 257 docstrings for public helpers.
- Use type hints where helpful; prefer small, pure functions.
- Naming: `snake_case` for functions/vars, `UPPER_CASE` for constants.
- CLI flags must be documented in `README.md` with copy-paste examples.
- GUI: keep UI code thin; delegate to core helpers; avoid global state.

## Testing Guidelines
- Always create and run tests for any feature or fix.
- Prefer automated tests using `pytest`; place them in `tests/` and keep them fast and hermetic.
- Use fixtures like `tmp_path`, `monkeypatch`, and `capsys` to isolate behavior.
- Complement with manual, scenario-based checks using the commands above.
- Validate: exit codes, created files, and summary output (e.g., “Wrote N frames…”).
- GUI testing: prioritize unit tests for core logic; add minimal smoke tests for GUI creation and teardown (skip on headless CI if needed).

## Workflow Requirements
- Every change must be committed with a clear, conventional commit message.
- Push commits to the remote after passing tests.
- Keep commits small and focused; update documentation alongside code changes.
- For GUI changes, include a brief UX note in the commit body when behavior changes.

## Commit & Pull Request Guidelines
- Commits: small, focused, with conventional style, e.g., `feat(cli): add --fps via -vf fps=VALUE` or `fix(io): validate output dir`.
- Include rationale in body if behavior changes; reference issues when applicable.
- PRs: clear description, before/after behavior, sample commands, and any docs updates. Screenshots not required.
- GUI PRs: include a small GIF or textual flow description if UI changes are non-trivial (optional).

## Security & Configuration Tips
- Never use `shell=True` with `subprocess`; pass argument lists.
- Validate inputs early: paths exist, `--fps > 0`, time formats parse.
- Abort clearly when `ffmpeg` is missing: "ffmpeg not found on PATH. Install it and try again."
- GUI: validate user inputs before invoking ffmpeg; sanitize paths; prevent blocking UI by running ffmpeg in a worker thread if adding progress later.

## Architecture Overview
- CLI assembles an `ffmpeg` command deterministically:
  - `-ss START` (optional), `-i INPUT`, `-to END` (optional), `-vf fps=VALUE` (optional), output pattern, and overwrite flag (`-y`/`-n`).
- JPEG quality: add `-q:v 2` when output pattern ends with `.jpg/.jpeg`.
- GUI will call the same assembly and execution helpers; no duplicated ffmpeg logic in UI code.
