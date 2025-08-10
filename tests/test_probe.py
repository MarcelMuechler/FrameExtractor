import json
from pathlib import Path

import pytest

import framegrab


def test_time_to_seconds_parses_numeric_and_hms():
    assert framegrab.time_to_seconds("12.5") == 12.5
    assert framegrab.time_to_seconds("00:01:05.25") == pytest.approx(65.25, rel=1e-6)


def test_probe_video_info_parses_json(monkeypatch, tmp_path):
    # Create a fake input path
    inp = tmp_path / "video.mp4"
    inp.write_bytes(b"fake")

    payload = {
        "streams": [
            {
                "codec_type": "video",
                "width": 1920,
                "height": 1080,
                "avg_frame_rate": "30000/1001",
            }
        ],
        "format": {"duration": "10.5"},
    }

    class R:
        returncode = 0
        stdout = json.dumps(payload)

    def fake_run(cmd, *a, **kw):
        return R()

    monkeypatch.setattr("subprocess.run", fake_run)

    info = framegrab.probe_video_info(inp)
    assert info["width"] == 1920
    assert info["height"] == 1080
    assert info["duration"] == 10.5
    assert info["fps"] == pytest.approx(29.97, rel=1e-3)

