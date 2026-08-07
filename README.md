# AutoDraw AI Desktop

AutoDraw AI is a local desktop prototype for turning images or sketches into guided pen, pencil, or marker stroke plans. It does **not** run in a browser and does **not** upload images anywhere.

## What works now

- Native desktop window built with Python `tkinter`.
- Local image selector for PNG, GIF, PPM, and PGM files supported by the dependency-free Tk image loader.
- Canvas preview of the selected image.
- Full-color layer analysis with adjustable color tolerance and insignificant-color filtering.
- Guided layer list with active color highlighting, image percentage, time estimates, and marker usage estimates.
- Target-window selector that can discover drawable windows when OS tooling is available and falls back to the full screen.
- Snipping-tool-style area selector for dragging a custom screen rectangle and making that rectangle the drawing target.
- Automatic from/to drawing coordinates based on the selected target window or selected screen area, including an optional margin.
- Brush size / stroke width setting used in path planning and preview thickness.
- Automatic image preview fitting so large images scale down inside the desktop display area while preserving aspect ratio.
- Target-area calibration that scales source artwork into the selected window while preserving aspect ratio.
- Real **Start drawing** action that activates the selected target window, maps the current layer into the selected window/area, and moves the mouse there when a supported mouse backend is available.
- Current-layer path simulation using nearest-neighbor travel optimization.
- Sketch-line detection preview that ignores light paper/background pixels and highlights darker marks.
- Export of a `.autodraw` JSON project containing mode, progress, layer data, calibration, and keybinds.
- Built-in safety hotkeys for pause, resume, emergency stop, and abort-job flows.

## How to run

Requires Python 3 with Tk support installed on your computer.

```bash
python3 src/autodraw_desktop.py
```

If Tk is missing on Linux, install your platform package first, for example `python3-tk` on Debian/Ubuntu.

## How to use the desktop app

1. Run `python3 src/autodraw_desktop.py`.
2. Click **Select image** and choose a local PNG/GIF/PPM/PGM image. Convert JPG, WEBP, TIFF, or PSD files to PNG first for this no-dependency build.
3. Click **Refresh windows**, choose the drawing program/window from **Draw inside selected window**, then click **Use selected window**. On Linux, install `wmctrl` for real window bounds; otherwise AutoDraw uses a full-screen fallback.
4. Or click **Select screen area** and drag a snipping-tool-style rectangle around exactly where the drawing should go.
5. Adjust **Target window margin** if you want to draw inside the selected window/area instead of all the way to its edges. The app displays the exact from/to coordinates it will use.
6. Adjust **Brush size / stroke width** to match your pen, pencil, marker, or digital brush size. Larger brush sizes reduce point density and draw thicker preview paths.
7. Adjust **Color tolerance** to merge similar colors and reduce marker changes.
8. Adjust **Ignore tiny colors** to remove dust, speckles, or colors too small to draw.
9. Click **Simulate current layer** to overlay the optimized travel path for the highlighted color.
10. Click **Start drawing** to activate the target app/window and draw that layer inside the selected window or selected area.
11. Click **Detect sketch lines** for pencil, ink, charcoal, marker, or notebook scans.
12. Use **Continue to next color** after changing pens or markers.
13. Press **Escape** or **F10** for emergency stop/abort, **F8** to pause, and **F9** to resume.
14. Click **Export .autodraw** to save the current local project state, including target window coordinates and brush size.

## Next desktop milestones

The current desktop app plans strokes, detects target-window coordinates, previews paths, and can run real mouse drawing when a platform backend is available. Windows uses the native cursor API, Linux uses `xdotool`, and macOS uses `cliclick`. Next milestones include richer calibration preset saving, multi-monitor selection, persistent progress checkpoints, custom palettes, and export of processed images, separated layers, stroke paths, previews, and time reports.

## Development

```bash
python3 -m unittest discover -s test
python3 -m py_compile src/autodraw_engine.py src/autodraw_desktop.py src/window_target.py src/mouse_control.py
```
