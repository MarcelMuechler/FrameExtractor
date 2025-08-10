import argparse
from pathlib import Path

import pytest

import framegrab


def test_parse_time_accepts_seconds_and_hms():
    assert framegrab.parse_time("0") == "0"
    assert framegrab.parse_time("12.5") == "12.5"
    assert framegrab.parse_time("00:00:05") == "00:00:05"
    assert framegrab.parse_time("10:59:59.123") == "10:59:59.123"


@pytest.mark.parametrize("val", ["-1", "abc", "1:2:3", "00:00", "99:99"])
def test_parse_time_rejects_bad_formats(val):
    with pytest.raises(argparse.ArgumentTypeError):
        framegrab.parse_time(val)


def test_positive_fps_validation():
    assert framegrab.positive_fps("1") == 1.0
    assert framegrab.positive_fps("2.5") == 2.5
    with pytest.raises(argparse.ArgumentTypeError):
        framegrab.positive_fps("0")
    with pytest.raises(argparse.ArgumentTypeError):
        framegrab.positive_fps("-3")
    with pytest.raises(argparse.ArgumentTypeError):
        framegrab.positive_fps("NaN")


def test_check_ffmpeg_available_missing(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda _: None)
    with pytest.raises(SystemExit) as ei:
        framegrab.check_ffmpeg_available()
    assert ei.value.code == 1


def test_overwrite_flag_maps_to_ffmpeg_switches():
    base = dict(
        input_video=Path("in.mp4"),
        output_dir=Path("frames"),
        pattern="frame_%06d.png",
    )
    cmd_no = framegrab.build_ffmpeg_cmd(**base, overwrite=False)
    cmd_yes = framegrab.build_ffmpeg_cmd(**base, overwrite=True)
    assert "-n" in cmd_no and "-y" not in cmd_no
    assert "-y" in cmd_yes and "-n" not in cmd_yes


def test_pattern_to_glob_conversion():
    assert framegrab.pattern_to_glob("frame_%06d.jpg") == "frame_*.jpg"
    assert framegrab.pattern_to_glob("img_%d.png") == "img_*.png"


def test_pattern_requires_placeholder_exits(tmp_path, monkeypatch):
    # Ensure ffmpeg check passes
    monkeypatch.setattr("shutil.which", lambda _: "/usr/bin/ffmpeg")
    inp = tmp_path / "video.mp4"
    inp.write_bytes(b"fake")
    outdir = tmp_path / "frames"
    with pytest.raises(SystemExit):
        framegrab.main([str(inp), str(outdir), "--pattern", "frame.jpg"])  # missing %d


def test_pattern_rejects_directories_and_absolute(monkeypatch, tmp_path):
    # Ensure ffmpeg check passes for CLI path validation
    monkeypatch.setattr("shutil.which", lambda _: "/usr/bin/ffmpeg")
    inp = tmp_path / "video.mp4"
    inp.write_bytes(b"fake")
    outdir = tmp_path / "frames"
    # Directory components in pattern
    with pytest.raises(SystemExit):
        framegrab.main([str(inp), str(outdir), "--pattern", "nested/frame_%06d.jpg"])
    # Absolute pattern
    bad_abs = str(tmp_path / "frame_%06d.png")
    with pytest.raises(SystemExit):
        framegrab.main([str(inp), str(outdir), "--pattern", bad_abs])


def test_verbose_sets_ffmpeg_loglevel_info():
    cmd = framegrab.build_ffmpeg_cmd(
        input_video=Path("in.mp4"),
        output_dir=Path("frames"),
        pattern="frame_%06d.jpg",
        verbose=True,
    )
    joined = " ".join(cmd)
    assert "-loglevel info" in joined
    assert "-loglevel error" not in joined
