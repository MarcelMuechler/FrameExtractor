#!/usr/bin/env python3
"""
GUI entrypoint (planned)

This is a placeholder for a tkinter-based GUI that reuses the core helpers in
``framegrab.py`` (validation, command assembly, and execution). No UI is
implemented yet; this file serves as the future entrypoint.
"""

from __future__ import annotations

# Intentionally defer tkinter-specific implementation until GUI is built.
# from tkinter import Tk

def main() -> int:
    # Placeholder: GUI not implemented yet
    # When implemented, construct the UI and call into framegrab.extract_frames(...)
    print("GUI is not implemented yet. Use the CLI: python framegrab.py ...")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

