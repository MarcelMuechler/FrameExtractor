#!/usr/bin/env python3
"""
FrameExtractor CLI (scaffold)

Parses arguments, validates inputs, checks ffmpeg availability, and assembles the
ffmpeg command. Default behavior executes ffmpeg; use --dry-run to only print.

Usage examples:
  python framegrab.py sample.mp4 frames/
  python framegrab.py sample.mp4 frames/ --start 00:00:05 --end 10 --fps 2 \
      --pattern "img_%05d.png" --verbose --dry-run
"""

from __future__ import annotations

import argparse
import os
import glob
import re
import shlex
import shutil
import sys
from pathlib import Path
from typing import List, Optional, Tuple


TIME_RE = re.compile(r"^(\d{1,2}):(\d{2}):(\d{2})(?:\.(\d{1,3}))?$")


def parse_time(value: str) -> str:
    """Validate and normalize time input.

    Accepts either numeric seconds (int/float) or HH:MM:SS[.ms]. Returns the
    original string if valid; raises argparse.ArgumentTypeError otherwise.
    """
    if value is None:
        return value
    # Numeric seconds
    try:
        # Allow integers and decimals; ensure not negative
        seconds = float(value)
        if seconds < 0:
            raise ValueError
        # Keep the original string representation to pass to ffmpeg as-is
        return value
    except ValueError:
        pass

    # HH:MM:SS[.ms]
    if TIME_RE.match(value):
        return value
    raise argparse.ArgumentTypeError(
        "time must be seconds (e.g., 12.5) or HH:MM:SS[.ms] (e.g., 00:01:05.25)"
    )


def positive_fps(value: str) -> float:
    """Ensure the ``--fps`` argument is a positive number.

    Args:
        value: User-provided frames-per-second value.

    Raises:
        argparse.ArgumentTypeError: If ``value`` is non-numeric or <= 0.
    """
    try:
        fps = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("--fps must be a number > 0") from exc
    if not fps > 0:
        raise argparse.ArgumentTypeError("--fps must be > 0")
    return fps


def check_ffmpeg_available() -> None:
    """Abort if the ``ffmpeg`` executable is not on ``PATH``.

    Raises:
        SystemExit: If ``ffmpeg`` cannot be located.
    """
    if shutil.which("ffmpeg") is None:
        print("ffmpeg not found on PATH. Install it and try again.", file=sys.stderr)
        sys.exit(1)


def validate_paths(input_video: Path, output_dir: Path) -> None:
    """Validate input video and output directory paths.

    Args:
        input_video: Path to an existing video file.
        output_dir: Directory where frames will be written.

    Raises:
        SystemExit: If the input file is missing, the output path is invalid,
            or the destination parent directory is not writable.
    """
    if not input_video.exists() or not input_video.is_file():
        print(f"Input file not found: {input_video}", file=sys.stderr)
        sys.exit(1)
    if output_dir.exists() and not output_dir.is_dir():
        print(f"Output path exists but is not a directory: {output_dir}", file=sys.stderr)
        sys.exit(1)
    # If directory doesn't exist, ensure the parent is writable
    parent = (output_dir if output_dir.exists() else output_dir.parent) or Path(".")
    try:
        # Resolve may raise in some cases; ignore if it does
        parent = parent.resolve()
    except Exception:
        pass
    if not parent.exists():
        print(f"Parent directory does not exist: {parent}", file=sys.stderr)
        sys.exit(1)
    if not os.access(parent, os.W_OK):
        print(f"Parent directory is not writable: {parent}", file=sys.stderr)
        sys.exit(1)


def validate_pattern(pattern: str) -> None:
    """Check that the output filename pattern is supported.

    Args:
        pattern: Filename template containing a ``%d`` placeholder.

    Raises:
        SystemExit: If the extension is not ``.jpg``, ``.jpeg``, or ``.png``,
            or the placeholder is missing.
    """
    allowed_exts = {".jpg", ".jpeg", ".png"}
    ext = Path(pattern).suffix.lower()
    if ext not in allowed_exts:
        print(
            f"Unsupported pattern extension '{ext}'. Use one of: .jpg, .jpeg, .png",
            file=sys.stderr,
        )
        sys.exit(1)
    # Require a printf-style integer placeholder (e.g., %06d or %d)
    if not re.search(r"%0?\d*d", pattern):
        print(
            "Output pattern must include a %d placeholder (e.g., 'frame_%06d.jpg')",
            file=sys.stderr,
        )
        sys.exit(1)


def build_ffmpeg_cmd(
    input_video: Path,
    output_dir: Path,
    *,
    start: Optional[str] = None,
    end: Optional[str] = None,
    fps: Optional[float] = None,
    pattern: str = "frame_%06d.jpg",
    overwrite: bool = False,
    verbose: bool = False,
) -> List[str]:
    """Assemble the ``ffmpeg`` command for extracting frames.

    Args:
        input_video: Source video path.
        output_dir: Destination directory for frames.
        start: Optional start time.
        end: Optional end time.
        fps: Optional frame rate to sample.
        pattern: Output filename template.
        overwrite: Whether to overwrite existing files.
        verbose: Whether to use ``info`` log level.

    Returns:
        List of command arguments to run with ``subprocess``.
    """
    cmd: List[str] = ["ffmpeg", "-hide_banner"]
    # Use more verbose output when requested
    cmd += ["-loglevel", "info" if verbose else "error"]
    if start is not None:
        cmd += ["-ss", str(start)]
    cmd += ["-i", str(input_video)]
    if end is not None:
        cmd += ["-to", str(end)]
    if fps is not None:
        cmd += ["-vf", f"fps={fps}"]

    # JPEG quality tweak when writing JPEGs
    if Path(pattern).suffix.lower() in {".jpg", ".jpeg"}:
        cmd += ["-q:v", "2"]

    cmd += ["-y" if overwrite else "-n"]
    cmd += [str(output_dir / pattern)]
    return cmd


def pattern_to_glob(pattern: str) -> str:
    """Convert a printf-style frame pattern (e.g., %06d) to a glob string.

    Example: 'frame_%06d.jpg' -> 'frame_*.jpg'
    """
    return re.sub(r"%0?\d*d", "*", pattern)


def extract_frames(
    input_video: Path,
    output_dir: Path,
    *,
    start: Optional[str] = None,
    end: Optional[str] = None,
    fps: Optional[float] = None,
    pattern: str = "frame_%06d.jpg",
    overwrite: bool = False,
    verbose: bool = False,
    dry_run: bool = False,
) -> Tuple[int, int, List[str]]:
    """Extract frames according to options and return status.

    Returns a tuple of ``(return_code, frames_written, cmd)`` where ``cmd`` is the
    argument list passed to ``ffmpeg``. In ``dry_run`` mode, no files are written
    and ``frames_written`` is ``0``.
    """
    check_ffmpeg_available()
    validate_paths(input_video, output_dir)
    validate_pattern(pattern)

    cmd = build_ffmpeg_cmd(
        input_video,
        output_dir,
        start=start,
        end=end,
        fps=fps,
        pattern=pattern,
        overwrite=overwrite,
        verbose=verbose,
    )

    if dry_run:
        return 0, 0, cmd

    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)

    import subprocess

    proc = subprocess.run(cmd)
    if proc.returncode != 0:
        return proc.returncode, 0, cmd

    gpat = pattern_to_glob(pattern)
    files = glob.glob(str(output_dir / gpat))
    return 0, len(files), cmd


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="framegrab.py",
        description=(
            "Extract frames from a video via ffmpeg. This scaffold prints the constructed "
            "ffmpeg command in --dry-run mode."
        ),
    )
    parser.add_argument("input_video", type=Path, help="Path to input video file")
    parser.add_argument("output_dir", type=Path, help="Directory for extracted frames")
    parser.add_argument("--start", type=parse_time, help="Start time (sec or HH:MM:SS[.ms])")
    parser.add_argument("--end", type=parse_time, help="End time (sec or HH:MM:SS[.ms])")
    parser.add_argument("--fps", type=positive_fps, help="Sample at fixed frames per second")
    parser.add_argument(
        "--pattern",
        default="frame_%06d.jpg",
        help="Output filename pattern (.jpg/.jpeg/.png), e.g., frame_%06d.jpg",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing output files (ffmpeg -y)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print more details while preparing the command",
    )
    parser.add_argument(
        "--dry-run",
        dest="dry_run",
        action="store_true",
        default=False,
        help="Do not execute ffmpeg; only print the constructed command",
    )

    args = parser.parse_args(argv)

    if args.verbose:
        print("Assembling ffmpeg command...", file=sys.stderr)

    rc, count, cmd = extract_frames(
        args.input_video,
        args.output_dir,
        start=args.start,
        end=args.end,
        fps=args.fps,
        pattern=args.pattern,
        overwrite=args.overwrite,
        verbose=args.verbose,
        dry_run=args.dry_run,
    )

    printable = " ".join(shlex.quote(part) for part in cmd)
    if args.dry_run:
        print(printable)
        if args.verbose:
            print("(dry-run) Not executing ffmpeg.", file=sys.stderr)
        return rc

    if rc != 0:
        return rc

    print(f"Wrote {count} frames to {args.output_dir}")
    return rc


if __name__ == "__main__":
    sys.exit(main())
