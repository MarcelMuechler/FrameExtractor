#!/usr/bin/env python3
"""
FrameExtractor GUI (tkinter + ttk)

Modernized, stdlib-only GUI that reuses ``framegrab.extract_frames``.
Adds source info, FPS guard, estimates, pattern preview, reset, and prefs.
"""

from __future__ import annotations

import json
import os
import queue
import re
import shlex
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from typing import Optional

from pathlib import Path

import framegrab


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("FrameExtractor")
        self.minsize(720, 460)
        self._apply_styles()
        self._build_menu()
        self._prefs_path = Path.home() / ".frameextractor.json"

        self._build_ui()
        self._job: Optional[threading.Thread] = None
        self._msgs: "queue.Queue[str]" = queue.Queue()
        self._src_info: Optional[dict] = None
        self._theme: str = "system"

        self._load_prefs()
        self.protocol("WM_DELETE_WINDOW", self._on_exit)

    def _apply_styles(self) -> None:
        style = ttk.Style()
        for candidate in ("clam", "vista", "default"):
            try:
                style.theme_use(candidate)
                break
            except Exception:
                continue
        style.configure("TFrame", padding=6)
        style.configure("TLabel", padding=(2, 2))
        style.configure("TButton", padding=(6, 4))
        style.configure("Status.TLabel", anchor="w")
        style.configure("Valid.TEntry")
        style.configure("Invalid.TEntry", foreground="#b00020")

    def _build_menu(self) -> None:
        menubar = tk.Menu(self)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Exit", command=self._on_exit)
        menubar.add_cascade(label="File", menu=file_menu)

        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_radiobutton(label="System Theme", command=lambda: self._set_theme("system"))
        view_menu.add_radiobutton(label="Light Theme", command=lambda: self._set_theme("light"))
        view_menu.add_radiobutton(label="Dark Theme", command=lambda: self._set_theme("dark"))
        menubar.add_cascade(label="View", menu=view_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(
            label="About",
            command=lambda: messagebox.showinfo(
                "About FrameExtractor",
                "FrameExtractor – extract video frames with ffmpeg\n"
                "Python stdlib GUI using tkinter/ttk",
            ),
        )
        menubar.add_cascade(label="Help", menu=help_menu)
        self.config(menu=menubar)

    def _set_theme(self, mode: str) -> None:
        self._theme = mode
        style = ttk.Style()
        if mode in ("system", "light"):
            try:
                self.status.configure(background="white", foreground="black")
            except Exception:
                pass
            return
        if mode == "dark":
            bg = "#1e1e1e"
            fg = "#dddddd"
            style.configure("TFrame", background=bg)
            style.configure("TLabel", background=bg, foreground=fg)
            style.configure("TButton", background=bg, foreground=fg)
            style.configure("TCheckbutton", background=bg, foreground=fg)
            style.configure("Status.TLabel", background=bg, foreground=fg)
            style.configure("Valid.TEntry", fieldbackground="#2a2a2a", foreground=fg)
            style.configure("Invalid.TEntry", fieldbackground="#3a1a1a", foreground="#ff8080")
            try:
                self.status.configure(background="#111111", foreground=fg, insertbackground=fg)
            except Exception:
                pass

    def _build_ui(self) -> None:
        root = ttk.Frame(self)
        root.grid(row=0, column=0, sticky="nsew")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Input section
        input_fr = ttk.LabelFrame(root, text="Input / Output")
        input_fr.grid(row=0, column=0, sticky="ew")
        input_fr.grid_columnconfigure(1, weight=1)

        ttk.Label(input_fr, text="Input Video:").grid(row=0, column=0, sticky="e")
        self.in_var = tk.StringVar()
        in_entry = ttk.Entry(input_fr, textvariable=self.in_var)
        in_entry.grid(row=0, column=1, sticky="ew", padx=(6, 6))
        in_entry.bind("<FocusOut>", lambda e: self._schedule_probe())
        ttk.Button(input_fr, text="Browse", command=self._choose_input).grid(row=0, column=2, sticky="w")

        ttk.Label(input_fr, text="Output Dir:").grid(row=1, column=0, sticky="e")
        self.out_var = tk.StringVar()
        out_entry = ttk.Entry(input_fr, textvariable=self.out_var)
        out_entry.grid(row=1, column=1, sticky="ew", padx=(6, 6))
        out_entry.bind("<FocusOut>", lambda e: self._update_pattern_preview())
        ttk.Button(input_fr, text="Browse", command=self._choose_output).grid(row=1, column=2, sticky="w")

        # Options section
        opts_fr = ttk.LabelFrame(root, text="Options")
        opts_fr.grid(row=1, column=0, sticky="ew", pady=(6, 0))
        for c in range(7):
            opts_fr.grid_columnconfigure(c, weight=1)

        ttk.Label(opts_fr, text="Start:").grid(row=0, column=0, sticky="e")
        self.start_var = tk.StringVar()
        start_entry = ttk.Entry(opts_fr, textvariable=self.start_var, width=12, style="Valid.TEntry")
        start_entry.grid(row=0, column=1, sticky="w")
        start_entry.bind("<FocusOut>", lambda e: (self._validate_fields(), self._update_estimate()))
        self._start_entry = start_entry
        self._start_err = tk.StringVar(value="")
        ttk.Label(opts_fr, textvariable=self._start_err, foreground="#b00020").grid(row=1, column=1, sticky="w")

        ttk.Label(opts_fr, text="End:").grid(row=0, column=2, sticky="e")
        self.end_var = tk.StringVar()
        end_entry = ttk.Entry(opts_fr, textvariable=self.end_var, width=12, style="Valid.TEntry")
        end_entry.grid(row=0, column=3, sticky="w")
        end_entry.bind("<FocusOut>", lambda e: (self._validate_fields(), self._update_estimate()))
        self._end_entry = end_entry
        self._end_err = tk.StringVar(value="")
        ttk.Label(opts_fr, textvariable=self._end_err, foreground="#b00020").grid(row=1, column=3, sticky="w")

        ttk.Label(opts_fr, text="FPS:").grid(row=0, column=4, sticky="e")
        self.fps_var = tk.StringVar()
        fps_entry = ttk.Entry(opts_fr, textvariable=self.fps_var, width=8, style="Valid.TEntry")
        fps_entry.grid(row=0, column=5, sticky="w")
        fps_entry.bind("<FocusOut>", lambda e: (self._enforce_fps_limit(), self._validate_fields()))
        self._fps_entry = fps_entry
        self._fps_err = tk.StringVar(value="")
        ttk.Label(opts_fr, textvariable=self._fps_err, foreground="#b00020").grid(row=1, column=5, sticky="w")

        ttk.Label(opts_fr, text="Pattern:").grid(row=2, column=0, sticky="e", pady=(6, 0))
        self.pattern_var = tk.StringVar(value="frame_%06d.jpg")
        pattern_entry = ttk.Entry(opts_fr, textvariable=self.pattern_var, style="Valid.TEntry")
        pattern_entry.grid(row=2, column=1, columnspan=4, sticky="ew", pady=(6, 0))
        pattern_entry.bind("<FocusOut>", lambda e: (self._validate_fields(), self._update_pattern_preview()))
        self._pattern_entry = pattern_entry
        self._pattern_err = tk.StringVar(value="")
        ttk.Label(opts_fr, textvariable=self._pattern_err, foreground="#b00020").grid(row=3, column=1, columnspan=4, sticky="w")

        ttk.Label(opts_fr, text="Preset:").grid(row=2, column=5, sticky="e", pady=(6, 0))
        self._preset = tk.StringVar(value="JPEG (.jpg)")
        preset = ttk.Combobox(
            opts_fr,
            textvariable=self._preset,
            values=["JPEG (.jpg)", "PNG (.png)"],
            state="readonly",
            width=12,
        )
        preset.grid(row=2, column=6, sticky="w", padx=(6, 0))
        preset.bind("<<ComboboxSelected>>", self._on_preset)

        # Pattern preview
        self.pattern_preview_var = tk.StringVar(value="Preview: –")
        ttk.Label(opts_fr, textvariable=self.pattern_preview_var).grid(row=4, column=1, columnspan=6, sticky="w")

        # Toggles
        toggles_fr = ttk.Frame(opts_fr)
        toggles_fr.grid(row=5, column=0, columnspan=7, sticky="w", pady=(6, 0))
        self.overwrite_var = tk.BooleanVar(value=False)
        self.verbose_var = tk.BooleanVar(value=False)
        self.dry_run_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(toggles_fr, text="Overwrite", variable=self.overwrite_var).grid(row=0, column=0, padx=(0, 12))
        ttk.Checkbutton(toggles_fr, text="Verbose", variable=self.verbose_var).grid(row=0, column=1, padx=(0, 12))
        ttk.Checkbutton(toggles_fr, text="Dry-run", variable=self.dry_run_var).grid(row=0, column=2)

        # Actions
        actions_fr = ttk.Frame(root)
        actions_fr.grid(row=2, column=0, sticky="ew", pady=(8, 0))
        actions_fr.grid_columnconfigure(0, weight=1)
        self.preview_btn = ttk.Button(actions_fr, text="Preview Command", command=self._on_preview)
        self.preview_btn.grid(row=0, column=0, sticky="w")
        self.extract_btn = ttk.Button(actions_fr, text="Extract Frames", command=self._on_extract)
        self.extract_btn.grid(row=0, column=1, sticky="e")
        self.open_out_btn = ttk.Button(actions_fr, text="Open Output", command=self._open_output, state="disabled")
        self.open_out_btn.grid(row=0, column=2, sticky="e", padx=(8, 0))
        self.reset_btn = ttk.Button(actions_fr, text="Reset", command=self._on_reset)
        self.reset_btn.grid(row=0, column=3, sticky="e", padx=(8, 0))

        # Status area
        status_fr = ttk.LabelFrame(root, text="Status / Output")
        status_fr.grid(row=3, column=0, sticky="nsew", pady=(8, 0))
        root.grid_rowconfigure(3, weight=1)
        root.grid_columnconfigure(0, weight=1)
        self.status = tk.Text(status_fr, height=10, wrap="word", state="disabled")
        self.status.grid(row=0, column=0, sticky="nsew")
        status_fr.grid_rowconfigure(0, weight=1)
        status_fr.grid_columnconfigure(0, weight=1)

        # Bottom status bar
        self.statusbar_var = tk.StringVar(value="Ready")
        self.statusbar = ttk.Label(root, textvariable=self.statusbar_var, style="Status.TLabel")
        self.statusbar.grid(row=4, column=0, sticky="ew", pady=(6, 0))

        # Source info + estimate
        self.srcinfo_var = tk.StringVar(value="Source: –")
        self.estimate_var = tk.StringVar(value="Estimate: –")
        info_fr = ttk.Frame(root)
        info_fr.grid(row=5, column=0, sticky="ew")
        ttk.Label(info_fr, textvariable=self.srcinfo_var).grid(row=0, column=0, sticky="w")
        ttk.Label(info_fr, textvariable=self.estimate_var).grid(row=0, column=1, sticky="e")

    def _choose_input(self) -> None:
        path = filedialog.askopenfilename(
            title="Select video file",
            filetypes=[
                ("Video files", ".mp4 .mov .mkv .avi .webm .m4v"),
                ("All files", "*"),
            ],
        )
        if path:
            self.in_var.set(path)
            self._schedule_probe()

    def _choose_output(self) -> None:
        path = filedialog.askdirectory(title="Select output directory")
        if path:
            self.out_var.set(path)
            self._update_pattern_preview()

    def _append_status(self, text: str) -> None:
        self.status.configure(state="normal")
        self.status.insert("end", text + "\n")
        self.status.see("end")
        self.status.configure(state="disabled")
        self.statusbar_var.set(text if len(text) < 80 else text[:77] + "...")

    def _clear_status(self) -> None:
        self.status.configure(state="normal")
        self.status.delete("1.0", "end")
        self.status.configure(state="disabled")

    def _schedule_probe(self) -> None:
        path = self.in_var.get().strip()
        if not path:
            return
        p = Path(path)
        if not p.exists():
            return
        def worker():
            try:
                info = framegrab.probe_video_info(p)
            except Exception as exc:
                self._msgs.put(f"Probe error: {exc}")
                info = None
            self._msgs.put(("__SRCINFO__", info))
        threading.Thread(target=worker, daemon=True).start()

    def _update_srcinfo_ui(self, info: Optional[dict]) -> None:
        self._src_info = info or None
        if not info:
            self.srcinfo_var.set("Source: –")
            return
        fps = info.get("fps")
        wh = (info.get("width"), info.get("height"))
        dur = info.get("duration")
        parts = []
        if wh[0] and wh[1]:
            parts.append(f"{wh[0]}x{wh[1]}")
        if fps:
            parts.append(f"{fps:.2f} fps")
        if dur:
            parts.append(f"{dur:.2f} s")
        self.srcinfo_var.set("Source: " + (", ".join(parts) if parts else "–"))
        self._enforce_fps_limit()
        self._update_estimate()
        self._update_pattern_preview()

    def _on_preset(self, _evt=None) -> None:
        val = self._preset.get()
        if "PNG" in val:
            self.pattern_var.set("frame_%06d.png")
        else:
            self.pattern_var.set("frame_%06d.jpg")
        self._validate_fields()
        self._update_pattern_preview()

    def _enforce_fps_limit(self) -> None:
        if not self._src_info:
            return
        src_fps = self._src_info.get("fps")
        if not src_fps:
            return
        val = self.fps_var.get().strip()
        if not val:
            return
        try:
            user_fps = framegrab.positive_fps(val)
        except Exception:
            return
        if user_fps > src_fps:
            self.fps_var.set(f"{src_fps:.3f}")
            self._append_status(f"FPS limited to source rate: {src_fps:.3f}")
        self._update_estimate()

    def _update_estimate(self) -> None:
        info = self._src_info or {}
        dur = info.get("duration")
        start_s = None
        end_s = None
        try:
            s = self.start_var.get().strip()
            if s:
                start_s = framegrab.time_to_seconds(s)
        except Exception:
            start_s = None
        try:
            e = self.end_var.get().strip()
            if e:
                end_s = framegrab.time_to_seconds(e)
        except Exception:
            end_s = None
        if start_s is not None and end_s is not None and end_s > start_s:
            dur_range = end_s - start_s
        else:
            dur_range = dur
        fps = None
        try:
            fv = self.fps_var.get().strip()
            if fv:
                fps = framegrab.positive_fps(fv)
        except Exception:
            fps = None
        est = None
        if dur_range and fps:
            est = int(max(0, dur_range) * fps)
        self.estimate_var.set("Estimate: " + (f"~{est} frames" if est is not None else "–"))
        self._update_pattern_preview()

    def _validate_fields(self) -> bool:
        ok = True
        try:
            s = self.start_var.get().strip()
            if s:
                framegrab.parse_time(s)
            self._start_entry.configure(style="Valid.TEntry")
            self._start_err.set("")
        except Exception:
            self._start_entry.configure(style="Invalid.TEntry")
            self._start_err.set("Invalid time")
            ok = False
        try:
            e = self.end_var.get().strip()
            if e:
                framegrab.parse_time(e)
            self._end_entry.configure(style="Valid.TEntry")
            self._end_err.set("")
        except Exception:
            self._end_entry.configure(style="Invalid.TEntry")
            self._end_err.set("Invalid time")
            ok = False
        try:
            f = self.fps_var.get().strip()
            if f:
                framegrab.positive_fps(f)
            self._fps_entry.configure(style="Valid.TEntry")
            self._fps_err.set("")
        except Exception:
            self._fps_entry.configure(style="Invalid.TEntry")
            self._fps_err.set("FPS > 0")
            ok = False
        try:
            patt = self.pattern_var.get().strip() or "frame_%06d.jpg"
            framegrab.validate_pattern(patt)
            self._pattern_entry.configure(style="Valid.TEntry")
            self._pattern_err.set("")
        except SystemExit as e:
            self._pattern_entry.configure(style="Invalid.TEntry")
            self._pattern_err.set(str(e))
            ok = False
        except Exception:
            self._pattern_entry.configure(style="Invalid.TEntry")
            self._pattern_err.set("Invalid pattern")
            ok = False
        return ok

    def _update_pattern_preview(self) -> None:
        patt = (self.pattern_var.get() or "frame_%06d.jpg").strip()
        m = re.search(r"%0?(\d*)d", patt)
        if not m:
            self.pattern_preview_var.set("Preview: –")
            return
        width_s = m.group(1)
        width = int(width_s) if width_s else 0
        def fmt(n: int) -> str:
            num = f"{n:0{width}d}" if width else str(n)
            return re.sub(r"%0?\d*d", num, patt, count=1)
        first = fmt(1)
        last = None
        m2 = re.search(r"~(\d+) frames", self.estimate_var.get())
        if m2:
            count = int(m2.group(1))
            if count > 0:
                last = fmt(count)
        self.pattern_preview_var.set(
            f"Preview: {first} … {last}" if last else f"Preview: {first}"
        )

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
            except Exception as exc:
                raise ValueError(str(exc)) from exc
        pattern = self.pattern_var.get().strip() or "frame_%06d.jpg"
        overwrite = bool(self.overwrite_var.get())
        verbose = bool(self.verbose_var.get())
        dry_run = bool(self.dry_run_var.get())
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
            if not self._validate_fields():
                self._append_status("Fix validation errors above.")
                return
            kwargs = self._gather_args()
            # Preview should never execute ffmpeg; always force dry-run here.
            kwargs["dry_run"] = True
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
            if not self._validate_fields():
                self._append_status("Fix validation errors above.")
                return
            kwargs = self._gather_args()
        except Exception as exc:
            messagebox.showerror("Error", str(exc))
            return

        self.preview_btn.configure(state="disabled")
        self.extract_btn.configure(state="disabled")
        self.statusbar_var.set("Running...")

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
            except Exception as exc:
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
                    self.statusbar_var.set("Ready")
                    self.open_out_btn.configure(state="normal")
                else:
                    if isinstance(msg, tuple) and msg and msg[0] == "__SRCINFO__":
                        self._update_srcinfo_ui(msg[1])
                    else:
                        self._append_status(msg)
        except queue.Empty:
            pass
        if self._job and self._job.is_alive():
            self.after(100, self._drain_queue)

    def _open_output(self) -> None:
        path = self.out_var.get().strip()
        if not path:
            return
        p = Path(path)
        try:
            if p.exists():
                import subprocess, sys
                if sys.platform.startswith("darwin"):
                    subprocess.Popen(["open", str(p)])
                elif os.name == "nt":
                    os.startfile(str(p))  # type: ignore[attr-defined]
                else:
                    subprocess.Popen(["xdg-open", str(p)])
        except Exception as exc:
            messagebox.showerror("Open Output", f"Could not open: {exc}")

    def _on_reset(self) -> None:
        self.in_var.set("")
        self.out_var.set("")
        self.start_var.set("")
        self.end_var.set("")
        self.fps_var.set("")
        self.pattern_var.set("frame_%06d.jpg")
        self.overwrite_var.set(False)
        self.verbose_var.set(False)
        self.dry_run_var.set(False)
        self._src_info = None
        self.srcinfo_var.set("Source: –")
        self.estimate_var.set("Estimate: –")
        self.pattern_preview_var.set("Preview: –")
        self.statusbar_var.set("Ready")
        self.open_out_btn.configure(state="disabled")
        self._clear_status()
        self._validate_fields()

    def _load_prefs(self) -> None:
        try:
            if not self._prefs_path.exists():
                return
            data = json.loads(self._prefs_path.read_text())
        except Exception:
            return
        self.in_var.set(data.get("input_video", ""))
        self.out_var.set(data.get("output_dir", ""))
        self.start_var.set(data.get("start", ""))
        self.end_var.set(data.get("end", ""))
        self.fps_var.set(str(data.get("fps", "") or ""))
        self.pattern_var.set(data.get("pattern", "frame_%06d.jpg"))
        self.overwrite_var.set(bool(data.get("overwrite", False)))
        self.verbose_var.set(bool(data.get("verbose", False)))
        self.dry_run_var.set(bool(data.get("dry_run", False)))
        theme = data.get("theme")
        if theme in ("system", "light", "dark"):
            self._set_theme(theme)
        self._validate_fields()
        self._schedule_probe()
        self._update_estimate()
        self._update_pattern_preview()

    def _save_prefs(self) -> None:
        data = {
            "input_video": self.in_var.get().strip(),
            "output_dir": self.out_var.get().strip(),
            "start": self.start_var.get().strip(),
            "end": self.end_var.get().strip(),
            "fps": self.fps_var.get().strip(),
            "pattern": self.pattern_var.get().strip(),
            "overwrite": bool(self.overwrite_var.get()),
            "verbose": bool(self.verbose_var.get()),
            "dry_run": bool(self.dry_run_var.get()),
            "theme": self._theme,
        }
        try:
            self._prefs_path.write_text(json.dumps(data, indent=2))
        except Exception:
            pass

    def _on_exit(self) -> None:
        self._save_prefs()
        self.destroy()


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
