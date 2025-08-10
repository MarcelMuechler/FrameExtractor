import re
import sys
from pathlib import Path

import pytest

import framegrab


@pytest.fixture(autouse=True)
def ensure_ffmpeg_on_path(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda _: "/usr/bin/ffmpeg")


def test_build_cmd_includes_jpeg_quality_and_fps():
    cmd = framegrab.build_ffmpeg_cmd(
        input_video=Path("in.mp4"),
        output_dir=Path("frames"),
        fps=2.0,
        pattern="frame_%06d.jpg",
    )
    joined = " ".join(cmd)
    assert "-vf" in joined
    assert "fps=2.0" in joined
    assert "-q:v" in joined
    assert "2" in joined


def test_dry_run_prints_command(tmp_path, capsys):
    inp = tmp_path / "video.mp4"
    inp.write_bytes(b"fake")
    outdir = tmp_path / "frames"
    rc = framegrab.main([str(inp), str(outdir), "--dry-run", "--pattern", "img_%05d.png"])
    assert rc == 0
    out = capsys.readouterr().out.strip()
    assert out.startswith("ffmpeg")
    assert "img_%05d.png" in out
    assert not outdir.exists()


def test_run_executes_and_summarizes(tmp_path, monkeypatch, capsys):
    inp = tmp_path / "video.mp4"
    inp.write_bytes(b"fake")
    outdir = tmp_path / "out"

    def fake_run(cmd, *args, **kwargs):
        (outdir / "frame_000001.jpg").parent.mkdir(parents=True, exist_ok=True)
        (outdir / "frame_000001.jpg").write_bytes(b"data")
        class R:  # simple returncode holder
            returncode = 0
        return R()

    monkeypatch.setattr("subprocess.run", fake_run)
    rc = framegrab.main([str(inp), str(outdir)])
    assert rc == 0
    out = capsys.readouterr().out.strip()
    assert re.search(r"Wrote\s+1\s+frames\s+to\s+.+", out)
    assert outdir.exists()


def test_invalid_pattern_exits(tmp_path):
    inp = tmp_path / "video.mp4"
    inp.write_bytes(b"fake")
    outdir = tmp_path / "frames"
    with pytest.raises(SystemExit):
        framegrab.main([str(inp), str(outdir), "--pattern", "foo.txt"])
