# Repository Guidelines

## Project Structure & Module Organization
- `framegrab.py`: Single-file Python CLI; all logic lives here.
- `README.md`: Usage, examples, and troubleshooting.
- `.gitignore`: Ignore `__pycache__/`, virtualenvs, and output dirs (e.g., `frames/`, `out/`).
- No external Python deps; rely on stdlib and system `ffmpeg`.

## Build, Test, and Development Commands
- Run CLI: `python framegrab.py <input_video> <output_dir> [flags]`.
- Check ffmpeg: `ffmpeg -version` (must be on PATH).
- Manual test (all frames): `python framegrab.py sample.mp4 frames/`.
- Manual test (range + fps): `python framegrab.py sample.mp4 out/ --start 00:00:05 --end 00:00:10 --fps 2 --verbose`.

## Coding Style & Naming Conventions
- Python 3.9+; 4-space indentation; keep lines readable (~100 cols).
- Follow PEP 8 and PEP 257 docstrings for public helpers.
- Use type hints where helpful; prefer small, pure functions.
- Naming: `snake_case` for functions/vars, `UPPER_CASE` for constants.
- CLI flags must be documented in `README.md` with copy-paste examples.

## Testing Guidelines
- Always create and run tests for any feature or fix.
- Prefer automated tests using stdlib `unittest`; place them in `tests/` and keep them fast and hermetic.
- Complement with manual, scenario-based checks using the commands above.
- Validate: exit codes, created files, and summary output (e.g., “Wrote N frames…”).

## Workflow Requirements
- Every change must be committed with a clear, conventional commit message.
- Push commits to the remote after passing tests.
- Keep commits small and focused; update documentation alongside code changes.

## Commit & Pull Request Guidelines
- Commits: small, focused, with conventional style, e.g., `feat(cli): add --fps via -vf fps=VALUE` or `fix(io): validate output dir`.
- Include rationale in body if behavior changes; reference issues when applicable.
- PRs: clear description, before/after behavior, sample commands, and any docs updates. Screenshots not required.

## Security & Configuration Tips
- Never use `shell=True` with `subprocess`; pass argument lists.
- Validate inputs early: paths exist, `--fps > 0`, time formats parse.
- Abort clearly when `ffmpeg` is missing: "ffmpeg not found on PATH. Install it and try again."

## Architecture Overview
- CLI assembles an `ffmpeg` command deterministically:
  - `-ss START` (optional), `-i INPUT`, `-to END` (optional), `-vf fps=VALUE` (optional), output pattern, and overwrite flag (`-y`/`-n`).
- JPEG quality: add `-q:v 2` when output pattern ends with `.jpg/.jpeg`.
