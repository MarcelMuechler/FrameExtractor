import shutil
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg not installed")
def test_cli_extracts_frames_end_to_end(tmp_path):
    video = tmp_path / "in.mp4"
    subprocess.run(
        [
            "ffmpeg",
            "-f",
            "lavfi",
            "-i",
            "testsrc=duration=1:size=32x32:rate=1",
            str(video),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    outdir = tmp_path / "frames"
    result = subprocess.run(
        [sys.executable, "framegrab.py", str(video), str(outdir)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "Wrote 1 frames" in result.stdout
    frames = sorted(outdir.glob("frame_*"))
    assert len(frames) == 1
    assert frames[0].is_file()
