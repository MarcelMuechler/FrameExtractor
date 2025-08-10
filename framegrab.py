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
from typing import List, Optional


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
    try:
        fps = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("--fps must be a number > 0") from exc
    if fps <= 0:
        raise argparse.ArgumentTypeError("--fps must be > 0")
    return fps


def check_ffmpeg_available() -> None:
    if shutil.which("ffmpeg") is None:
        print("ffmpeg not found on PATH. Install it and try again.", file=sys.stderr)
        sys.exit(1)


def validate_paths(input_video: Path, output_dir: Path) -> None:
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
    allowed_exts = {".jpg", ".jpeg", ".png"}
    ext = Path(pattern).suffix.lower()
    if ext not in allowed_exts:
        print(
            f"Unsupported pattern extension '{ext}'. Use one of: .jpg, .jpeg, .png",
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
) -> List[str]:
    cmd: List[str] = ["ffmpeg", "-hide_banner", "-loglevel", "error"]
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

    # Validate environment and inputs
    check_ffmpeg_available()
    validate_paths(args.input_video, args.output_dir)
    validate_pattern(args.pattern)

    if args.verbose:
        print("Assembling ffmpeg command...", file=sys.stderr)

    cmd = build_ffmpeg_cmd(
        args.input_video,
        args.output_dir,
        start=args.start,
        end=args.end,
        fps=args.fps,
        pattern=args.pattern,
        overwrite=args.overwrite,
    )

    printable = " ".join(shlex.quote(part) for part in cmd)
    if args.dry_run:
        print(printable)
        if args.verbose:
            print("(dry-run) Not executing ffmpeg.", file=sys.stderr)
        return 0

    # Ensure output directory exists before running
    if not args.output_dir.exists():
        args.output_dir.mkdir(parents=True, exist_ok=True)

    if args.verbose:
        print(f"Executing: {printable}", file=sys.stderr)

    # Execute ffmpeg
    import subprocess

    proc = subprocess.run(cmd)
    if proc.returncode != 0:
        # ffmpeg likely printed errors to stderr due to -loglevel error
        return proc.returncode

    # Summarize number of frames written
    gpat = pattern_to_glob(args.pattern)
    files = glob.glob(str(args.output_dir / gpat))
    print(f"Wrote {len(files)} frames to {args.output_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())


if __name__ == "__main__":
    sys.exit(main())
