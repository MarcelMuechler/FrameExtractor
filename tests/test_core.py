from pathlib import Path

import pytest

import framegrab


@pytest.fixture(autouse=True)
def ensure_ffmpeg_on_path(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda _: "/usr/bin/ffmpeg")


def test_extract_frames_dry_run_returns_cmd(tmp_path):
    inp = tmp_path / "video.mp4"
    inp.write_bytes(b"fake")
    outdir = tmp_path / "frames"
    rc, count, cmd = framegrab.extract_frames(
        input_video=inp,
        output_dir=outdir,
        pattern="frame_%06d.jpg",
        dry_run=True,
    )
    assert rc == 0
    assert count == 0
    assert cmd and cmd[0] == "ffmpeg"
    assert not outdir.exists()


def test_extract_frames_executes_and_counts(tmp_path, monkeypatch):
    inp = tmp_path / "video.mp4"
    inp.write_bytes(b"fake")
    outdir = tmp_path / "frames"

    def fake_run(cmd, *args, **kwargs):
        (outdir / "frame_000001.jpg").parent.mkdir(parents=True, exist_ok=True)
        (outdir / "frame_000001.jpg").write_bytes(b"data")
        class R:
            returncode = 0
        return R()

    monkeypatch.setattr("subprocess.run", fake_run)
    rc, count, _ = framegrab.extract_frames(
        input_video=inp,
        output_dir=outdir,
        pattern="frame_%06d.jpg",
    )
    assert rc == 0
    assert count == 1
    assert outdir.exists()

