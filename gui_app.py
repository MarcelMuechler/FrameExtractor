#!/usr/bin/env python3
"""
FrameExtractor GUI (tkinter)

Thin tkinter-based GUI that reuses ``framegrab.extract_frames`` for execution.
Stdlib-only; no external dependencies.
"""

from __future__ import annotations

import queue
import shlex
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Optional

from pathlib import Path

import framegrab


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("FrameExtractor")
        self._build_ui()
        self._job: Optional[threading.Thread] = None
        self._msgs: "queue.Queue[str]" = queue.Queue()

    def _build_ui(self) -> None:
        pad = {"padx": 6, "pady": 4}
        # Row 0: Input
        tk.Label(self, text="Input Video:").grid(row=0, column=0, sticky="e", **pad)
        self.in_var = tk.StringVar()
        tk.Entry(self, textvariable=self.in_var, width=50).grid(row=0, column=1, **pad)
        tk.Button(self, text="Browse", command=self._choose_input).grid(row=0, column=2, **pad)

        # Row 1: Output
        tk.Label(self, text="Output Dir:").grid(row=1, column=0, sticky="e", **pad)
        self.out_var = tk.StringVar()
        tk.Entry(self, textvariable=self.out_var, width=50).grid(row=1, column=1, **pad)
        tk.Button(self, text="Browse", command=self._choose_output).grid(row=1, column=2, **pad)

        # Row 2: Times and fps
        tk.Label(self, text="Start:").grid(row=2, column=0, sticky="e", **pad)
        self.start_var = tk.StringVar()
        tk.Entry(self, textvariable=self.start_var, width=12).grid(row=2, column=1, sticky="w", **pad)

        tk.Label(self, text="End:").grid(row=2, column=1, sticky="e", **pad)
        self.end_var = tk.StringVar()
        tk.Entry(self, textvariable=self.end_var, width=12).grid(row=2, column=1, sticky="", padx=140, pady=4)

        tk.Label(self, text="FPS:").grid(row=2, column=1, sticky="e", padx=290, pady=4)
        self.fps_var = tk.StringVar()
        tk.Entry(self, textvariable=self.fps_var, width=8).grid(row=2, column=1, sticky="e", padx=230, pady=4)

        # Row 3: Pattern
        tk.Label(self, text="Pattern:").grid(row=3, column=0, sticky="e", **pad)
        self.pattern_var = tk.StringVar(value="frame_%06d.jpg")
        tk.Entry(self, textvariable=self.pattern_var, width=50).grid(row=3, column=1, **pad)

        # Row 4: Options
        self.overwrite_var = tk.BooleanVar(value=False)
        tk.Checkbutton(self, text="Overwrite", variable=self.overwrite_var).grid(row=4, column=0, sticky="w", padx=80, pady=4)

        self.verbose_var = tk.BooleanVar(value=False)
        tk.Checkbutton(self, text="Verbose", variable=self.verbose_var).grid(row=4, column=1, sticky="w", padx=0, pady=4)

        self.dry_run_var = tk.BooleanVar(value=False)
        tk.Checkbutton(self, text="Dry-run", variable=self.dry_run_var).grid(row=4, column=1, sticky="w", padx=100, pady=4)

        # Row 5: Actions
        self.preview_btn = tk.Button(self, text="Preview Command", command=self._on_preview)
        self.preview_btn.grid(row=5, column=0, sticky="w", padx=80, pady=6)
        self.extract_btn = tk.Button(self, text="Extract Frames", command=self._on_extract)
        self.extract_btn.grid(row=5, column=1, sticky="e", padx=80, pady=6)

        # Row 6: Status area
        tk.Label(self, text="Status / Output:").grid(row=6, column=0, sticky="nw", **pad)
        self.status = tk.Text(self, height=10, width=80, state="disabled")
        self.status.grid(row=6, column=1, columnspan=2, sticky="nsew", **pad)

        # Make status expand
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(6, weight=1)

    def _choose_input(self) -> None:
        path = filedialog.askopenfilename(title="Select video file")
        if path:
            self.in_var.set(path)

    def _choose_output(self) -> None:
        path = filedialog.askdirectory(title="Select output directory")
        if path:
            self.out_var.set(path)

    def _append_status(self, text: str) -> None:
        self.status.configure(state="normal")
        self.status.insert("end", text + "\n")
        self.status.see("end")
        self.status.configure(state="disabled")

    def _gather_args(self):
        input_video = Path(self.in_var.get().strip())
        output_dir = Path(self.out_var.get().strip())
        start = self.start_var.get().strip() or None
        end = self.end_var.get().strip() or None
        fps_val = self.fps_var.get().strip()
        fps = None
        if fps_val:
            try:
                fps = framegrab.positive_fps(fps_val)
            except Exception as exc:  # argparse.ArgumentTypeError
                raise ValueError(str(exc)) from exc
        pattern = self.pattern_var.get().strip() or "frame_%06d.jpg"
        overwrite = bool(self.overwrite_var.get())
        verbose = bool(self.verbose_var.get())
        dry_run = bool(self.dry_run_var.get())
        # Normalize times (will be validated later in extract)
        if start is not None:
            start = framegrab.parse_time(start)
        if end is not None:
            end = framegrab.parse_time(end)
        return {
            "input_video": input_video,
            "output_dir": output_dir,
            "start": start,
            "end": end,
            "fps": fps,
            "pattern": pattern,
            "overwrite": overwrite,
            "verbose": verbose,
            "dry_run": dry_run,
        }

    def _on_preview(self) -> None:
        try:
            kwargs = self._gather_args()
            rc, _count, cmd = framegrab.extract_frames(**kwargs)
            printable = " ".join(shlex.quote(part) for part in cmd)
            self._append_status(printable)
            if rc != 0:
                self._append_status(f"ffmpeg returned non-zero exit code: {rc}")
        except SystemExit as e:
            messagebox.showerror("Validation Error", f"{e}")
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    def _on_extract(self) -> None:
        if self._job and self._job.is_alive():
            messagebox.showinfo("Busy", "An extraction is already running.")
            return
        try:
            kwargs = self._gather_args()
        except Exception as exc:
            messagebox.showerror("Error", str(exc))
            return

        self.preview_btn.configure(state="disabled")
        self.extract_btn.configure(state="disabled")

        def worker():
            try:
                rc, count, cmd = framegrab.extract_frames(**kwargs)
                printable = " ".join(shlex.quote(part) for part in cmd)
                if rc == 0 and not kwargs.get("dry_run", False):
                    self._msgs.put(printable)
                    self._msgs.put(f"Wrote {count} frames to {kwargs['output_dir']}")
                elif rc == 0 and kwargs.get("dry_run", False):
                    self._msgs.put(printable)
                    self._msgs.put("(dry-run) Not executing ffmpeg.")
                else:
                    self._msgs.put(printable)
                    self._msgs.put(f"ffmpeg returned non-zero exit code: {rc}")
            except Exception as exc:  # surface error
                self._msgs.put(f"Error: {exc}")
            finally:
                self._msgs.put("__DONE__")

        self._job = threading.Thread(target=worker, daemon=True)
        self._job.start()
        self.after(50, self._drain_queue)

    def _drain_queue(self) -> None:
        try:
            while True:
                msg = self._msgs.get_nowait()
                if msg == "__DONE__":
                    self.preview_btn.configure(state="normal")
                    self.extract_btn.configure(state="normal")
                else:
                    self._append_status(msg)
        except queue.Empty:
            pass
        if self._job and self._job.is_alive():
            self.after(100, self._drain_queue)


def main() -> int:
    try:
        app = App()
        app.mainloop()
    except tk.TclError as exc:
        print(f"GUI error: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
