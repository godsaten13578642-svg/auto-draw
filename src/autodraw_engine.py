"""Core image-to-stroke planning utilities for the AutoDraw AI desktop app."""
from __future__ import annotations

from dataclasses import dataclass, asdict
from math import ceil
from typing import Iterable, Sequence

SUPPORTED_IMAGE_TYPES = (".png", ".gif", ".ppm", ".pgm")
STROKE_MODES = (
    "Outline", "Fill", "Cross Hatch", "Sketch", "Single Line", "Double Line",
    "Spiral Fill", "Contour Fill", "Stippling", "Zigzag Fill", "Custom patterns",
)
DEFAULT_KEYBINDS = {"pause": "F8", "resume": "F9", "emergency_stop": "Escape", "abort_job": "F10"}
DEFAULT_BRUSH_SIZE = 3

@dataclass(frozen=True)
class ColorLayer:
    color: tuple[int, int, int]
    count: int
    percentage: float
    eta_seconds: int
    marker_usage_ml: float


def quantize_color(color: Sequence[int], tolerance: int = 32) -> tuple[int, int, int]:
    step = max(1, int(tolerance))
    return tuple(min(255, round(int(channel) / step) * step) for channel in color[:3])


def luminance(color: Sequence[int]) -> float:
    r, g, b = color[:3]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def analyze_colors(
    pixels: Iterable[Sequence[int]], *, tolerance: int = 32, min_percentage: float = 0, speed: float = 3, sort: str = "darkest"
) -> list[ColorLayer]:
    buckets: dict[tuple[int, int, int], int] = {}
    total = 0
    for pixel in pixels:
        key = quantize_color(pixel, tolerance)
        buckets[key] = buckets.get(key, 0) + 1
        total += 1
    total = max(1, total)
    layers = []
    for color, count in buckets.items():
        percentage = count / total
        if percentage * 100 < min_percentage:
            continue
        eta = ceil((count / max(0.1, speed)) * 0.02)
        layers.append(ColorLayer(color, count, percentage, eta, round(count * 0.00004, 2)))
    reverse = sort == "lightest"
    return sorted(layers, key=lambda layer: luminance(layer.color), reverse=reverse)


def fit_to_area(image_size: tuple[int, int], area_size: tuple[float, float], mode: str = "fit") -> dict[str, float]:
    image_width, image_height = image_size
    area_width, area_height = area_size
    scale_x = area_width / image_width
    scale_y = area_height / image_height
    scale = max(scale_x, scale_y) if mode == "fill" else min(scale_x, scale_y)
    width = round(image_width * scale, 2)
    height = round(image_height * scale, 2)
    return {"width": width, "height": height, "scale": scale, "x": round((area_width - width) / 2, 2), "y": round((area_height - height) / 2, 2)}


def nearest_neighbor_path(points: Sequence[dict[str, int]]) -> list[dict[str, int]]:
    remaining = list(points)
    if not remaining:
        return []
    current = remaining.pop(0)
    path = [current]
    while remaining:
        best_index = min(
            range(len(remaining)),
            key=lambda i: (remaining[i]["x"] - current["x"]) ** 2 + (remaining[i]["y"] - current["y"]) ** 2,
        )
        current = remaining.pop(best_index)
        path.append(current)
    return path


def build_layer_path(
    pixels: Sequence[Sequence[int]], image_size: tuple[int, int], target_color: Sequence[int], *, tolerance: int = 32, sample_step: int = 3, brush_size: int = DEFAULT_BRUSH_SIZE
) -> list[dict[str, int]]:
    width, height = image_size
    points: list[dict[str, int]] = []
    step = max(1, int(sample_step), int(brush_size))
    limit = max(1, int(tolerance))
    for y in range(0, height, step):
        for x in range(0, width, step):
            color = pixels[y * width + x]
            if max(abs(int(color[i]) - int(target_color[i])) for i in range(3)) <= limit:
                points.append({"x": x, "y": y})
    return nearest_neighbor_path(points)


def threshold_sketch_pixels(pixels: Sequence[Sequence[int]], image_size: tuple[int, int], *, threshold: int = 190) -> list[dict[str, int]]:
    width, height = image_size
    points: list[dict[str, int]] = []
    for y in range(height):
        for x in range(width):
            if luminance(pixels[y * width + x]) < threshold:
                points.append({"x": x, "y": y})
    return points


def drawing_area_from_target(target: object, margin: int = 0) -> dict[str, int]:
    x = int(getattr(target, "x", 0)) + margin
    y = int(getattr(target, "y", 0)) + margin
    width = max(1, int(getattr(target, "width", 1)) - margin * 2)
    height = max(1, int(getattr(target, "height", 1)) - margin * 2)
    return {"x": x, "y": y, "width": width, "height": height, "end_x": x + width, "end_y": y + height}


def serialize_project(layers: Sequence[ColorLayer], calibration: str, progress: int = 0, *, brush_size: int = DEFAULT_BRUSH_SIZE, target_area: dict | None = None) -> dict:
    return {
        "version": 1,
        "mode": "desktop",
        "progress": progress,
        "brush_size": brush_size,
        "target_area": target_area or {},
        "calibration": calibration,
        "keybinds": DEFAULT_KEYBINDS,
        "layers": [asdict(layer) for layer in layers],
    }
