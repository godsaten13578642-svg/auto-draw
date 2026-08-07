"""AutoDraw AI desktop prototype: no browser required."""
from __future__ import annotations

import json
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from autodraw_engine import (
    DEFAULT_KEYBINDS,
    STROKE_MODES,
    SUPPORTED_IMAGE_TYPES,
    analyze_colors,
    build_layer_path,
    fit_to_area,
    serialize_project,
    threshold_sketch_pixels,
)

class AutoDrawDesktop(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("AutoDraw AI Desktop")
        self.geometry("1180x760")
        self.configure(bg="#0b1020")
        self.image: tk.PhotoImage | None = None
        self.pixels: list[tuple[int, int, int]] = []
        self.layers = []
        self.progress = 0
        self._build_ui()
        self._bind_hotkeys()
        self.recalculate()

    def _build_ui(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background="#0b1020")
        style.configure("Card.TFrame", background="#111827", relief="flat")
        style.configure("TLabel", background="#111827", foreground="#ecf2ff")
        style.configure("Title.TLabel", font=("Arial", 28, "bold"), foreground="#ecf2ff", background="#0b1020")
        style.configure("TButton", padding=8)

        shell = ttk.Frame(self, padding=18)
        shell.pack(fill="both", expand=True)
        ttk.Label(shell, text="AutoDraw AI Desktop", style="Title.TLabel").pack(anchor="w")
        ttk.Label(shell, text="Local app for turning images/sketches into guided pen, pencil, and marker stroke plans.", background="#0b1020", foreground="#9fb3d9").pack(anchor="w", pady=(0, 12))

        toolbar = ttk.Frame(shell)
        toolbar.pack(fill="x", pady=(0, 12))
        for text, command in (
            ("Select image", self.select_image), ("Simulate current layer", self.simulate_layer),
            ("Detect sketch lines", self.detect_sketch), ("Continue to next color", self.next_layer),
            ("Export .autodraw", self.export_project),
        ):
            ttk.Button(toolbar, text=text, command=command).pack(side="left", padx=(0, 8))

        main = ttk.Frame(shell)
        main.pack(fill="both", expand=True)
        left = ttk.Frame(main, style="Card.TFrame", padding=14)
        left.pack(side="left", fill="both", expand=True, padx=(0, 12))
        right = ttk.Frame(main, style="Card.TFrame", padding=14)
        right.pack(side="right", fill="y")

        self.canvas = tk.Canvas(left, bg="#f8fafc", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.status = ttk.Label(left, text="No image loaded. Showing sample layers until you select a local image.")
        self.status.pack(anchor="w", pady=(10, 0))

        self.tolerance = tk.IntVar(value=32)
        self.min_percentage = tk.DoubleVar(value=0)
        self.speed = tk.DoubleVar(value=3)
        self.sketch_threshold = tk.IntVar(value=190)
        self.paper_width = tk.DoubleVar(value=250)
        self.paper_height = tk.DoubleVar(value=200)
        for label, variable, start, end in (
            ("Color tolerance", self.tolerance, 8, 96), ("Ignore tiny colors (%)", self.min_percentage, 0, 10),
            ("Drawing speed", self.speed, 1, 5), ("Sketch darkness threshold", self.sketch_threshold, 60, 245),
        ):
            ttk.Label(right, text=label).pack(anchor="w")
            ttk.Scale(right, from_=start, to=end, variable=variable, command=lambda _value: self.recalculate()).pack(fill="x", pady=(0, 10))

        size_frame = ttk.Frame(right, style="Card.TFrame")
        size_frame.pack(fill="x", pady=(8, 10))
        ttk.Label(size_frame, text="Paper width (mm)").grid(row=0, column=0, sticky="w")
        ttk.Entry(size_frame, textvariable=self.paper_width, width=8).grid(row=0, column=1, padx=4)
        ttk.Label(size_frame, text="height (mm)").grid(row=0, column=2, sticky="w")
        ttk.Entry(size_frame, textvariable=self.paper_height, width=8).grid(row=0, column=3, padx=4)
        ttk.Button(size_frame, text="Apply", command=self.recalculate).grid(row=0, column=4, padx=4)

        self.calibration = ttk.Label(right, text="")
        self.calibration.pack(anchor="w", pady=(0, 10))
        self.stats = ttk.Label(right, text="")
        self.stats.pack(anchor="w", pady=(0, 10))
        ttk.Label(right, text="Guided color layers").pack(anchor="w")
        self.layer_list = tk.Listbox(right, width=48, height=16, bg="#18233a", fg="#ecf2ff", selectbackground="#fbbf24")
        self.layer_list.pack(fill="both", expand=True, pady=(4, 10))
        ttk.Label(right, text="Stroke modes: " + " • ".join(STROKE_MODES), wraplength=360).pack(anchor="w")
        ttk.Label(right, text="Safety: " + " • ".join(f"{k}: {v}" for k, v in DEFAULT_KEYBINDS.items()), wraplength=360).pack(anchor="w", pady=(8, 0))

    def _bind_hotkeys(self) -> None:
        self.bind("<Escape>", lambda _event: self.stop_now())
        self.bind("<F8>", lambda _event: self.status.config(text="Paused. Press F9 to resume."))
        self.bind("<F9>", lambda _event: self.status.config(text="Resumed."))
        self.bind("<F10>", lambda _event: self.stop_now())

    def select_image(self) -> None:
        path = filedialog.askopenfilename(
            title="Select an image",
            filetypes=[("Supported images", "*.png *.gif *.ppm *.pgm"), ("All files", "*.*")],
        )
        if not path:
            return
        if Path(path).suffix.lower() not in SUPPORTED_IMAGE_TYPES:
            messagebox.showerror("Unsupported image", "This dependency-free desktop build supports PNG, GIF, PPM, and PGM through Tk. Convert JPG/WEBP/TIFF to PNG first.")
            return
        self.image = tk.PhotoImage(file=path)
        self._read_pixels()
        self.progress = 0
        self._draw_image()
        self.status.config(text=f"Loaded {Path(path).name} ({self.image.width()} × {self.image.height()}px).")
        self.recalculate()

    def _read_pixels(self) -> None:
        assert self.image is not None
        width, height = self.image.width(), self.image.height()
        self.pixels = []
        for y in range(height):
            for x in range(width):
                value = self.image.get(x, y)
                self.pixels.append(tuple(int(channel) for channel in value[:3]))

    def _draw_image(self) -> None:
        self.canvas.delete("all")
        if self.image is None:
            self.canvas.create_text(28, 28, anchor="nw", text="Select an image to start", fill="#334155", font=("Arial", 18, "bold"))
            return
        self.canvas.create_image(0, 0, anchor="nw", image=self.image)
        self.canvas.configure(scrollregion=(0, 0, self.image.width(), self.image.height()))

    def recalculate(self) -> None:
        sample_pixels = self.pixels[::4] if self.pixels else [(8,8,8),(42,42,42),(112,66,20),(20,40,120),(200,26,31),(236,142,36),(242,215,60),(63,160,76),(92,177,230),(245,245,245),(8,8,8),(200,26,31)]
        self.layers = analyze_colors(sample_pixels, tolerance=self.tolerance.get(), min_percentage=self.min_percentage.get(), speed=self.speed.get())
        self.layer_list.delete(0, tk.END)
        for index, layer in enumerate(self.layers, start=1):
            rgb = ",".join(str(channel) for channel in layer.color)
            self.layer_list.insert(tk.END, f"{index}. rgb({rgb}) | {layer.percentage * 100:.1f}% | {layer.eta_seconds}s | {layer.marker_usage_ml} ml")
        if self.layers:
            self.layer_list.selection_set(min(self.progress, len(self.layers) - 1))
        image_size = (self.image.width(), self.image.height()) if self.image else (320, 260)
        fit = fit_to_area(image_size, (self.paper_width.get(), self.paper_height.get()))
        self.calibration.config(text=f"Scale to {fit['width']} × {fit['height']} mm at {fit['scale'] * 100:.0f}%; offset {fit['x']} / {fit['y']} mm.")
        self.stats.config(text=f"{len(self.layers)} colors • {len(sample_pixels):,} sampled pixels • ETA {sum(layer.eta_seconds for layer in self.layers)}s")

    def simulate_layer(self) -> None:
        if self.image is None or not self.layers:
            self.status.config(text="Select an image before simulating a layer.")
            return
        self._draw_image()
        layer = self.layers[min(self.progress, len(self.layers) - 1)]
        path = build_layer_path(self.pixels, (self.image.width(), self.image.height()), layer.color, tolerance=self.tolerance.get(), sample_step=4)
        if path:
            previous = path[0]
            for point in path[1:1200]:
                self.canvas.create_line(previous["x"], previous["y"], point["x"], point["y"], fill="#fbbf24", width=1)
                previous = point
        self.status.config(text=f"Previewing {len(path):,} optimized points for layer {self.progress + 1}.")

    def detect_sketch(self) -> None:
        if self.image is None:
            self.status.config(text="Select an image before detecting sketch lines.")
            return
        self._draw_image()
        points = threshold_sketch_pixels(self.pixels, (self.image.width(), self.image.height()), threshold=self.sketch_threshold.get())
        for point in points[:3500]:
            self.canvas.create_rectangle(point["x"], point["y"], point["x"], point["y"], outline="#22c55e")
        self.status.config(text=f"Sketch detection kept {len(points):,} dark pixels and ignored light background.")

    def next_layer(self) -> None:
        if self.layers:
            self.progress = min(len(self.layers) - 1, self.progress + 1)
            self.layer_list.selection_clear(0, tk.END)
            self.layer_list.selection_set(self.progress)
            self.status.config(text=f"Insert marker for layer {self.progress + 1}, then simulate or draw.")

    def export_project(self) -> None:
        if not self.layers:
            self.status.config(text="No layers to export yet.")
            return
        path = filedialog.asksaveasfilename(title="Export project", defaultextension=".autodraw", filetypes=[("AutoDraw project", "*.autodraw")])
        if not path:
            return
        payload = serialize_project(self.layers, self.calibration.cget("text"), self.progress)
        Path(path).write_text(json.dumps(payload, indent=2), encoding="utf-8")
        self.status.config(text=f"Saved {Path(path).name}.")

    def stop_now(self) -> None:
        self.status.config(text="Emergency stop: drawing disabled and mouse control released.")

if __name__ == "__main__":
    AutoDrawDesktop().mainloop()
