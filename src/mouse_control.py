"""Best-effort desktop mouse drawing backend for AutoDraw AI."""
from __future__ import annotations

import ctypes
import platform
import subprocess
from dataclasses import dataclass
from typing import Sequence

@dataclass(frozen=True)
class DrawPoint:
    x: int
    y: int

class MouseController:
    def __init__(self) -> None:
        self.system = platform.system().lower()
        self.available, self.reason = self._detect()

    def _detect(self) -> tuple[bool, str]:
        if self.system == "windows":
            return True, "Windows cursor API"
        if self.system == "linux":
            ok = subprocess.run(["sh", "-lc", "command -v xdotool"], text=True, capture_output=True, check=False).returncode == 0
            return (ok, "xdotool") if ok else (False, "Install xdotool to enable real mouse drawing on Linux.")
        if self.system == "darwin":
            ok = subprocess.run(["sh", "-lc", "command -v cliclick"], text=True, capture_output=True, check=False).returncode == 0
            return (ok, "cliclick") if ok else (False, "Install cliclick to enable real mouse drawing on macOS.")
        return False, f"Mouse drawing is not implemented for {self.system}."

    def move_to(self, point: DrawPoint) -> None:
        if self.system == "windows":
            ctypes.windll.user32.SetCursorPos(point.x, point.y)
        elif self.system == "linux":
            subprocess.run(["xdotool", "mousemove", str(point.x), str(point.y)], check=False)
        elif self.system == "darwin":
            subprocess.run(["cliclick", f"m:{point.x},{point.y}"], check=False)

    def mouse_down(self) -> None:
        if self.system == "windows":
            ctypes.windll.user32.mouse_event(0x0002, 0, 0, 0, 0)
        elif self.system == "linux":
            subprocess.run(["xdotool", "mousedown", "1"], check=False)
        elif self.system == "darwin":
            subprocess.run(["cliclick", "dd:."], check=False)

    def mouse_up(self) -> None:
        if self.system == "windows":
            ctypes.windll.user32.mouse_event(0x0004, 0, 0, 0, 0)
        elif self.system == "linux":
            subprocess.run(["xdotool", "mouseup", "1"], check=False)
        elif self.system == "darwin":
            subprocess.run(["cliclick", "du:."], check=False)


def map_path_to_target(path: Sequence[dict[str, int]], image_size: tuple[int, int], target_area: dict[str, int]) -> list[DrawPoint]:
    image_width, image_height = image_size
    scale = min(target_area["width"] / image_width, target_area["height"] / image_height)
    drawn_width = image_width * scale
    drawn_height = image_height * scale
    offset_x = target_area["x"] + (target_area["width"] - drawn_width) / 2
    offset_y = target_area["y"] + (target_area["height"] - drawn_height) / 2
    return [DrawPoint(round(offset_x + point["x"] * scale), round(offset_y + point["y"] * scale)) for point in path]
