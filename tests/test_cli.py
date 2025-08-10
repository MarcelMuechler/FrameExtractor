import io
import os
import re
import sys
import shutil
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import framegrab


class FrameGrabTests(unittest.TestCase):
    def setUp(self) -> None:
        # Ensure ffmpeg check passes by default
        self.which_patcher = mock.patch.object(shutil, "which", return_value="/usr/bin/ffmpeg")
        self.which_patcher.start()

    def tearDown(self) -> None:
        self.which_patcher.stop()

    def test_build_cmd_includes_jpeg_quality_and_fps(self):
        cmd = framegrab.build_ffmpeg_cmd(
            input_video=Path("in.mp4"),
            output_dir=Path("frames"),
            fps=2.0,
            pattern="frame_%06d.jpg",
        )
        joined = " ".join(cmd)
        self.assertIn("-vf", joined)
        self.assertIn("fps=2.0", joined)
        self.assertIn("-q:v", joined)
        self.assertIn("2", joined)

    def test_dry_run_prints_command(self):
        with tempfile.TemporaryDirectory() as tmp:
            inp = Path(tmp) / "video.mp4"
            inp.write_bytes(b"fake")
            outdir = Path(tmp) / "frames"
            # Do not create outdir; only parent exists
            f = io.StringIO()
            with redirect_stdout(f):
                rc = framegrab.main([str(inp), str(outdir), "--dry-run", "--pattern", "img_%05d.png"])
            self.assertEqual(rc, 0)
            printed = f.getvalue().strip()
            self.assertTrue(printed.startswith("ffmpeg"), printed)
            self.assertIn("img_%05d.png", printed)
            # Directory should not be created in dry-run
            self.assertFalse(outdir.exists())

    def test_run_executes_and_summarizes(self):
        with tempfile.TemporaryDirectory() as tmp:
            inp = Path(tmp) / "video.mp4"
            inp.write_bytes(b"fake")
            outdir = Path(tmp) / "out"  # does not exist initially

            # Simulate ffmpeg by creating one output file during run
            def fake_run(cmd, *args, **kwargs):
                out_pattern = Path(outdir) / "frame_000001.jpg"
                outdir.mkdir(parents=True, exist_ok=True)
                out_pattern.write_bytes(b"data")
                m = mock.Mock()
                m.returncode = 0
                return m

            with mock.patch("subprocess.run", side_effect=fake_run):
                f = io.StringIO()
                with redirect_stdout(f):
                    rc = framegrab.main([str(inp), str(outdir)])
                self.assertEqual(rc, 0)
                printed = f.getvalue().strip()
                self.assertRegex(printed, r"Wrote\s+1\s+frames\s+to\s+.+")
                self.assertTrue(outdir.exists())

    def test_invalid_pattern_exits(self):
        with tempfile.TemporaryDirectory() as tmp:
            inp = Path(tmp) / "video.mp4"
            inp.write_bytes(b"fake")
            outdir = Path(tmp) / "frames"
            g = io.StringIO()
            with redirect_stderr(g):
                with self.assertRaises(SystemExit):
                    framegrab.main([str(inp), str(outdir), "--pattern", "foo.txt"])


if __name__ == "__main__":
    unittest.main()
