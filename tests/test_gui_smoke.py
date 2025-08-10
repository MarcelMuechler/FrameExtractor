import os
import pytest


def test_gui_app_creates_and_closes():
    try:
        import tkinter as tk
    except Exception:
        pytest.skip("tkinter not available; skipping GUI test")

    # Attempt to instantiate Tk; skip if display not available
    try:
        root = tk.Tk()
        root.destroy()
    except tk.TclError:
        pytest.skip("No GUI display available; skipping GUI test")

    from gui_app import App
    app = App()
    app.update()
    app.destroy()


def test_gui_preview_forces_dry_run(monkeypatch, tmp_path):
    try:
        import tkinter as tk
    except Exception:
        pytest.skip("tkinter not available; skipping GUI test")

    try:
        root = tk.Tk()
        root.destroy()
    except tk.TclError:
        pytest.skip("No GUI display available; skipping GUI test")

    # Capture kwargs passed to extract_frames
    captured = {}

    def fake_extract_frames(**kwargs):
        captured.update(kwargs)
        # Return a plausible command for preview display
        return 0, 0, [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            "in.mp4",
            str(tmp_path / "out" / "frame_%06d.jpg"),
        ]

    monkeypatch.setattr("framegrab.extract_frames", fake_extract_frames)

    from gui_app import App
    app = App()
    try:
        # Minimal inputs for preview
        app.in_var.set(str(tmp_path / "in.mp4"))
        app.out_var.set(str(tmp_path / "out"))
        app.dry_run_var.set(False)  # even if unchecked, preview must force dry-run
        app._on_preview()
        assert captured.get("dry_run") is True
    finally:
        app.destroy()
