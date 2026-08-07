# AutoDraw AI Desktop

AutoDraw AI is a local desktop prototype for turning images or sketches into guided pen, pencil, or marker stroke plans. It does **not** run in a browser and does **not** upload images anywhere.

## What works now

- Native desktop window built with Python `tkinter`.
- Local image selector for PNG, GIF, PPM, and PGM files supported by the dependency-free Tk image loader.
- Canvas preview of the selected image.
- Full-color layer analysis with adjustable color tolerance and insignificant-color filtering.
- Guided layer list with active color highlighting, image percentage, time estimates, and marker usage estimates.
- Paper calibration inputs that scale source artwork into a physical drawing area while preserving aspect ratio.
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
3. Adjust **Color tolerance** to merge similar colors and reduce marker changes.
4. Adjust **Ignore tiny colors** to remove dust, speckles, or colors too small to draw.
5. Enter the paper/canvas width and height in millimeters, then click **Apply**.
6. Click **Simulate current layer** to overlay the optimized travel path for the highlighted color.
7. Click **Detect sketch lines** for pencil, ink, charcoal, marker, or notebook scans.
8. Use **Continue to next color** after changing pens or markers.
9. Press **Escape** or **F10** for emergency stop/abort, **F8** to pause, and **F9** to resume.
10. Click **Export .autodraw** to save the current local project state.

## Next desktop milestones

The current desktop app plans strokes and previews paths; it intentionally does not move the mouse yet. The next implementation should add OS-level mouse control, calibration preset saving, multi-monitor selection, persistent progress checkpoints, real drawing execution, custom palettes, and export of processed images, separated layers, stroke paths, previews, and time reports.

## Development

```bash
python3 -m unittest discover -s test
python3 -m py_compile src/autodraw_engine.py src/autodraw_desktop.py
```
