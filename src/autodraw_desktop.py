"""AutoDraw AI desktop prototype: no browser required."""
from __future__ import annotations

import json
import math
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from autodraw_engine import (
    DEFAULT_BRUSH_SIZE,
    DEFAULT_KEYBINDS,
    STROKE_MODES,
    SUPPORTED_IMAGE_TYPES,
    analyze_colors,
    build_layer_path,
    drawing_area_from_target,
    fit_to_area,
    serialize_project,
    threshold_sketch_pixels,
)
from mouse_control import MouseController, map_path_to_target
from window_target import TargetWindow, discover_windows, full_screen_target

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
        self.display_scale = 1.0
        self.display_image: tk.PhotoImage | None = None
        self.targets: list[TargetWindow] = []
        self.selected_target: TargetWindow | None = None
        self.mouse = MouseController()
        self.drawing_active = False
        self.draw_path = []
        self.draw_index = 0
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
            ("Select image", self.select_image), ("Refresh windows", self.refresh_windows),
            ("Use selected window", self.use_selected_window), ("Simulate current layer", self.simulate_layer),
            ("Start drawing", self.start_drawing), ("Detect sketch lines", self.detect_sketch),
            ("Continue to next color", self.next_layer), ("Export .autodraw", self.export_project),
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
        self.stroke_delay = tk.IntVar(value=5)
        self.sketch_threshold = tk.IntVar(value=190)
        self.brush_size = tk.IntVar(value=DEFAULT_BRUSH_SIZE)
        self.target_margin = tk.IntVar(value=0)
        self.paper_width = tk.DoubleVar(value=250)
        self.paper_height = tk.DoubleVar(value=200)
        for label, variable, start, end in (
            ("Color tolerance", self.tolerance, 8, 96), ("Ignore tiny colors (%)", self.min_percentage, 0, 10),
            ("Drawing speed", self.speed, 1, 5), ("Stroke delay (ms)", self.stroke_delay, 1, 40),
            ("Brush size / stroke width (px)", self.brush_size, 1, 40),
            ("Sketch darkness threshold", self.sketch_threshold, 60, 245), ("Target window margin (px)", self.target_margin, 0, 80),
        ):
            ttk.Label(right, text=label).pack(anchor="w")
            ttk.Scale(right, from_=start, to=end, variable=variable, command=lambda _value: self.recalculate()).pack(fill="x", pady=(0, 10))

        size_frame = ttk.Frame(right, style="Card.TFrame")
        size_frame.pack(fill="x", pady=(8, 10))
        ttk.Label(size_frame, text="Target width (px)").grid(row=0, column=0, sticky="w")
        ttk.Entry(size_frame, textvariable=self.paper_width, width=8).grid(row=0, column=1, padx=4)
        ttk.Label(size_frame, text="height (px)").grid(row=0, column=2, sticky="w")
        ttk.Entry(size_frame, textvariable=self.paper_height, width=8).grid(row=0, column=3, padx=4)
        ttk.Button(size_frame, text="Apply", command=self.recalculate).grid(row=0, column=4, padx=4)

        ttk.Label(right, text="Draw inside selected window").pack(anchor="w")
        self.window_choice = ttk.Combobox(right, state="readonly", width=48)
        self.window_choice.pack(fill="x", pady=(0, 10))
        self.target_label = ttk.Label(right, text="")
        self.target_label.pack(anchor="w", pady=(0, 10))
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
        self.refresh_windows()


    def refresh_windows(self) -> None:
        self.targets = discover_windows((self.winfo_screenwidth(), self.winfo_screenheight()))
        self.window_choice["values"] = [target.label for target in self.targets]
        if self.targets and not self.window_choice.get():
            self.window_choice.current(0)
            self.selected_target = self.targets[0]
        backend = self.mouse.reason if self.mouse.available else self.mouse.reason
        self.status.config(text=f"Found {len(self.targets)} drawable target option(s). Mouse backend: {backend}. Choose one, then click Use selected window.")

    def use_selected_window(self) -> None:
        index = self.window_choice.current()
        if index < 0 or index >= len(self.targets):
            self.status.config(text="No target window selected; using full screen.")
            self.selected_target = full_screen_target(self.winfo_screenwidth(), self.winfo_screenheight())
        else:
            self.selected_target = self.targets[index]
            self.status.config(text=f"Target set to {self.selected_target.label}.")
        self.recalculate()

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
        max_width, max_height = 760, 520
        divisor = max(1, math.ceil(max(self.image.width() / max_width, self.image.height() / max_height, 1)))
        self.display_image = self.image.subsample(divisor, divisor)
        self.display_scale = 1 / divisor
        self.canvas.create_image(0, 0, anchor="nw", image=self.display_image)
        self.canvas.configure(scrollregion=(0, 0, self.display_image.width(), self.display_image.height()))

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
        target_area = self._current_target_area()
        self.paper_width.set(target_area["width"])
        self.paper_height.set(target_area["height"])
        fit = fit_to_area(image_size, (target_area["width"], target_area["height"]))
        self.target_label.config(text=f"Draw from {target_area['x']},{target_area['y']} to {target_area['end_x']},{target_area['end_y']} in {self.selected_target.title if self.selected_target else 'Full screen'}.")
        self.calibration.config(text=f"Image fit: {fit['width']} × {fit['height']} px at {fit['scale'] * 100:.0f}%; offset {fit['x']} / {fit['y']} px inside target.")
        self.stats.config(text=f"{len(self.layers)} colors • brush {self.brush_size.get()}px • {len(sample_pixels):,} sampled pixels • ETA {sum(layer.eta_seconds for layer in self.layers)}s")


    def _current_target_area(self) -> dict[str, int]:
        return drawing_area_from_target(self.selected_target or full_screen_target(self.winfo_screenwidth(), self.winfo_screenheight()), self.target_margin.get())

    def _current_layer_path(self) -> list[dict[str, int]]:
        if self.image is None or not self.layers:
            return []
        layer = self.layers[min(self.progress, len(self.layers) - 1)]
        return build_layer_path(self.pixels, (self.image.width(), self.image.height()), layer.color, tolerance=self.tolerance.get(), sample_step=4, brush_size=self.brush_size.get())

    def start_drawing(self) -> None:
        if self.image is None or not self.layers:
            self.status.config(text="Select an image and target window before starting drawing.")
            return
        if not self.mouse.available:
            self.status.config(text=f"Cannot start real drawing: {self.mouse.reason}")
            return
        target_area = self._current_target_area()
        local_path = self._current_layer_path()
        self.draw_path = map_path_to_target(local_path, (self.image.width(), self.image.height()), target_area)
        if not self.draw_path:
            self.status.config(text="No drawable points found for the selected layer.")
            return
        self.drawing_active = True
        self.draw_index = 0
        self.mouse.move_to(self.draw_path[0])
        self.mouse.mouse_down()
        self.status.config(text=f"Drawing layer {self.progress + 1} inside target from {target_area['x']},{target_area['y']} to {target_area['end_x']},{target_area['end_y']}. Press Escape to stop.")
        self.after(self.stroke_delay.get(), self._draw_next_point)

    def _draw_next_point(self) -> None:
        if not self.drawing_active or self.draw_index >= len(self.draw_path):
            self.mouse.mouse_up() if self.mouse.available else None
            self.drawing_active = False
            self.status.config(text=f"Finished drawing layer {self.progress + 1}. Change marker, then continue to the next color.")
            return
        self.mouse.move_to(self.draw_path[self.draw_index])
        self.draw_index += 1
        self.after(max(1, self.stroke_delay.get()), self._draw_next_point)

    def simulate_layer(self) -> None:
        if self.image is None or not self.layers:
            self.status.config(text="Select an image before simulating a layer.")
            return
        self._draw_image()
        path = self._current_layer_path()
        if path:
            previous = path[0]
            for point in path[1:1200]:
                self.canvas.create_line(previous["x"] * self.display_scale, previous["y"] * self.display_scale, point["x"] * self.display_scale, point["y"] * self.display_scale, fill="#fbbf24", width=max(1, self.brush_size.get() * self.display_scale))
                previous = point
        self.status.config(text=f"Previewing {len(path):,} optimized points for layer {self.progress + 1}.")

    def detect_sketch(self) -> None:
        if self.image is None:
            self.status.config(text="Select an image before detecting sketch lines.")
            return
        self._draw_image()
        points = threshold_sketch_pixels(self.pixels, (self.image.width(), self.image.height()), threshold=self.sketch_threshold.get())
        for point in points[:3500]:
            x, y = point["x"] * self.display_scale, point["y"] * self.display_scale
            self.canvas.create_rectangle(x, y, x + max(1, self.display_scale), y + max(1, self.display_scale), outline="#22c55e")
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
        target_area = self._current_target_area()
        payload = serialize_project(self.layers, self.calibration.cget("text"), self.progress, brush_size=self.brush_size.get(), target_area=target_area)
        Path(path).write_text(json.dumps(payload, indent=2), encoding="utf-8")
        self.status.config(text=f"Saved {Path(path).name}.")

    def stop_now(self) -> None:
        self.drawing_active = False
        self.mouse.mouse_up() if self.mouse.available else None
        self.status.config(text="Emergency stop: drawing disabled and mouse control released.")

if __name__ == "__main__":
    AutoDrawDesktop().mainloop()
