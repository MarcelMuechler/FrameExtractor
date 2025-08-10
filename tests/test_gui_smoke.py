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
