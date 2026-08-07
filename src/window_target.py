"""Best-effort target-window discovery for AutoDraw AI.

The app stays dependency-free. When optional operating-system tools are present, it can
read open window titles and bounds; otherwise it falls back to the full screen.
"""
from __future__ import annotations

import platform
import subprocess
from dataclasses import dataclass

@dataclass(frozen=True)
class TargetWindow:
    title: str
    x: int
    y: int
    width: int
    height: int

    @property
    def label(self) -> str:
        return f"{self.title} — {self.width}×{self.height} at {self.x},{self.y}"


def full_screen_target(width: int, height: int) -> TargetWindow:
    return TargetWindow("Full screen", 0, 0, width, height)


def discover_windows(screen_size: tuple[int, int]) -> list[TargetWindow]:
    system = platform.system().lower()
    if system == "linux":
        windows = _linux_windows()
    elif system == "darwin":
        windows = _mac_windows(screen_size)
    elif system == "windows":
        windows = _windows_titles(screen_size)
    else:
        windows = []
    fallback = full_screen_target(*screen_size)
    deduped = {window.label: window for window in [fallback, *windows] if window.width > 0 and window.height > 0}
    return list(deduped.values())


def _linux_windows() -> list[TargetWindow]:
    if not _command_exists("wmctrl"):
        return []
    output = subprocess.run(["wmctrl", "-lG"], text=True, capture_output=True, check=False).stdout
    windows: list[TargetWindow] = []
    for line in output.splitlines():
        parts = line.split(maxsplit=7)
        if len(parts) < 8:
            continue
        _window_id, _desktop, x, y, width, height, _host, title = parts
        windows.append(TargetWindow(title, int(x), int(y), int(width), int(height)))
    return windows


def _mac_windows(screen_size: tuple[int, int]) -> list[TargetWindow]:
    script = 'tell application "System Events" to get name of every process whose visible is true'
    output = subprocess.run(["osascript", "-e", script], text=True, capture_output=True, check=False).stdout
    width, height = screen_size
    return [TargetWindow(title.strip(), 0, 0, width, height) for title in output.split(",") if title.strip()]


def _windows_titles(screen_size: tuple[int, int]) -> list[TargetWindow]:
    command = "Get-Process | Where-Object {$_.MainWindowTitle} | Select-Object -ExpandProperty MainWindowTitle"
    output = subprocess.run(["powershell", "-NoProfile", "-Command", command], text=True, capture_output=True, check=False).stdout
    width, height = screen_size
    return [TargetWindow(title.strip(), 0, 0, width, height) for title in output.splitlines() if title.strip()]


def _command_exists(name: str) -> bool:
    return subprocess.run(["sh", "-lc", f"command -v {name}"], text=True, capture_output=True, check=False).returncode == 0
