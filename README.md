# AutoDraw AI

AutoDraw AI is a desktop-oriented drawing workflow prototype for turning images or sketches into real pen, pencil, or marker strokes by controlling the mouse inside a calibrated drawing area.

## What works now

- Image selector for PNG, JPG, BMP, WEBP, TIFF, and SVG files.
- Canvas preview of the selected image, scaled down for responsive analysis.
- Full-color layer analysis with adjustable color tolerance and insignificant-color filtering.
- Guided layer list with active color highlighting, image percentage, time estimates, and marker usage estimates.
- Paper calibration inputs that scale source artwork into a physical drawing area while preserving aspect ratio.
- Current-layer path simulation using nearest-neighbor travel optimization.
- Sketch-line detection preview that ignores light paper/background pixels and highlights darker marks.
- Export of a `.autodraw` JSON project containing mode, progress, layer data, calibration, and keybinds.
- Stroke-generation and safety-keybind capability catalog for the planned desktop app.
- Pure JavaScript core utilities for color quantization, drawing-time estimates, area fitting, sketch filtering, and path optimization.

## How to use the prototype

1. Open `index.html` in a modern browser.
2. Click **Choose File** and select an image or scanned sketch.
3. Adjust **Color tolerance** to merge similar colors and reduce marker changes.
4. Adjust **Ignore tiny colors** to remove dust, speckles, or colors too small to draw.
5. Enter the paper/canvas width and height in millimeters to preview automatic scaling.
6. Click **Simulate current layer** to overlay the optimized mouse path for the highlighted color.
7. Click **Detect sketch lines** when using pencil, ink, charcoal, or notebook scans.
8. Use **Continue to next color** after changing pens/markers.
9. Click **Export .autodraw** to save the current project state for later work.

## Desktop features still planned

The browser prototype does not move the mouse yet. The next desktop build should add OS-level mouse control, emergency-stop listeners, pause/resume hotkeys, saved calibration presets, multi-monitor selection, live drawing progress, resumeable stroke checkpoints, and import/export of processed images, line art, separated layers, stroke paths, previews, and time reports.

## Development

```bash
npm test
npm run check
```
