# AutoDraw AI

AutoDraw AI is a desktop-oriented drawing workflow prototype for turning images or sketches into real pen, pencil, or marker strokes by controlling the mouse inside a calibrated drawing area.

## Implemented prototype

- Full-color layer analysis with adjustable color tolerance and insignificant-color filtering.
- Guided layer list with active color highlighting, image percentage, time estimates, and marker usage estimates.
- Paper calibration preview that scales source artwork into a physical drawing area while preserving aspect ratio.
- Stroke-generation and safety-keybind capability catalog for the planned desktop app.
- Pure JavaScript core utilities for color quantization, drawing-time estimates, area fitting, and nearest-neighbor path optimization.

## Planned feature coverage

The UI is organized around the complete product plan: sketch cleanup and edge detection, resize/rotate/flip tools, live preview and simulation, mouse calibration, emergency stop/pause/resume keybinds, project progress saving to `.autodraw`, statistics, accessibility, export options, and future AI simplification/plugin workflows.

## Development

```bash
npm test
npm run check
```

Open `index.html` in a browser to view the prototype.
