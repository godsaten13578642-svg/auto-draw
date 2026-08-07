import { STROKE_MODES, DEFAULT_KEYBINDS, SUPPORTED_IMAGE_TYPES, analyzeColors, buildLayerPath, estimateLayer, fitToArea, pixelsFromImageData, thresholdSketchPixels } from './core.js';

const state = { layers: [], progress: 0, mode: 'Full Color', preset: 'Letter', imageData: null, imageSize: { width: 320, height: 260 } };
const fallbackPixels = [[8,8,8],[42,42,42],[112,66,20],[20,40,120],[200,26,31],[236,142,36],[242,215,60],[63,160,76],[92,177,230],[245,245,245],[8,8,8],[200,26,31]];
const canvas = document.querySelector('#previewCanvas');
const context = canvas.getContext('2d', { willReadFrequently: true });

function renderLayers() {
  const list = document.querySelector('#layers');
  list.innerHTML = '';
  state.layers.forEach((layer, index) => {
    const item = document.createElement('li');
    item.className = index === state.progress ? 'active' : '';
    const [r,g,b] = layer.color;
    item.innerHTML = `<span class="swatch" style="background: rgb(${r}, ${g}, ${b})"></span><strong>Layer ${index + 1}</strong><span>${(layer.percentage*100).toFixed(1)}%</span><span>${layer.etaSeconds}s</span><span>${layer.markerUsage} ml</span>`;
    list.append(item);
  });
}

function renderOverlay(path = []) {
  if (!path.length) return;
  context.save();
  context.strokeStyle = '#fbbf24';
  context.lineWidth = 1;
  context.beginPath();
  path.slice(0, 1200).forEach((point, index) => index === 0 ? context.moveTo(point.x, point.y) : context.lineTo(point.x, point.y));
  context.stroke();
  context.restore();
}

function updatePlanner() {
  const tolerance = Number(document.querySelector('#tolerance').value);
  const minPercentage = Number(document.querySelector('#minPercentage').value);
  const speed = Number(document.querySelector('#speed').value);
  const pixels = state.imageData ? pixelsFromImageData(state.imageData, { sampleStep: 2 }) : fallbackPixels;
  state.layers = analyzeColors(pixels, { tolerance, minPercentage }).map(layer => estimateLayer(layer, speed));
  renderLayers();
  const fit = fitToArea(state.imageSize, { width: Number(document.querySelector('#paperWidth').value), height: Number(document.querySelector('#paperHeight').value) });
  document.querySelector('#calibration').textContent = `Scaled to ${fit.width} × ${fit.height} mm at ${(fit.scale*100).toFixed(0)}%, centered ${fit.x} mm / ${fit.y} mm.`;
  document.querySelector('#stats').textContent = `${state.layers.length} colors • ${pixels.length.toLocaleString()} sampled pixels • ETA ${state.layers.reduce((sum, layer) => sum + layer.etaSeconds, 0)}s`;
}

function loadImage(file) {
  if (!SUPPORTED_IMAGE_TYPES.includes(file.type)) {
    document.querySelector('#status').textContent = 'Unsupported file type. Choose PNG, JPG, BMP, WEBP, TIFF, or SVG.';
    return;
  }
  const reader = new FileReader();
  reader.addEventListener('load', () => {
    const image = new Image();
    image.addEventListener('load', () => {
      const maxSide = 640;
      const scale = Math.min(1, maxSide / Math.max(image.width, image.height));
      canvas.width = Math.max(1, Math.round(image.width * scale));
      canvas.height = Math.max(1, Math.round(image.height * scale));
      context.clearRect(0, 0, canvas.width, canvas.height);
      context.drawImage(image, 0, 0, canvas.width, canvas.height);
      state.imageSize = { width: canvas.width, height: canvas.height };
      state.imageData = context.getImageData(0, 0, canvas.width, canvas.height);
      state.progress = 0;
      document.querySelector('#status').textContent = `Loaded ${file.name} (${canvas.width} × ${canvas.height}px).`;
      updatePlanner();
    });
    image.src = reader.result;
  });
  reader.readAsDataURL(file);
}

function simulateCurrentLayer() {
  if (!state.imageData || !state.layers[state.progress]) return;
  context.putImageData(state.imageData, 0, 0);
  const tolerance = Number(document.querySelector('#tolerance').value);
  const path = buildLayerPath(state.imageData, state.layers[state.progress].color, { tolerance, sampleStep: 3 });
  renderOverlay(path);
  document.querySelector('#status').textContent = `Previewing ${path.length.toLocaleString()} optimized points for layer ${state.progress + 1}.`;
}

function renderSketchMask() {
  if (!state.imageData) return;
  const points = thresholdSketchPixels(state.imageData, { threshold: Number(document.querySelector('#sketchThreshold').value) });
  context.putImageData(state.imageData, 0, 0);
  context.fillStyle = '#22c55e';
  points.slice(0, 3500).forEach(point => context.fillRect(point.x, point.y, 1, 1));
  document.querySelector('#status').textContent = `Sketch detection kept ${points.length.toLocaleString()} dark pixels and ignored light paper/background.`;
}

function exportProject() {
  const payload = { version: 1, mode: state.mode, preset: state.preset, progress: state.progress, layers: state.layers, calibration: document.querySelector('#calibration').textContent, keybinds: DEFAULT_KEYBINDS };
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
  const anchor = document.createElement('a');
  anchor.href = URL.createObjectURL(blob);
  anchor.download = 'project.autodraw';
  anchor.click();
  URL.revokeObjectURL(anchor.href);
}

function renderCapabilities() {
  document.querySelector('#strokes').textContent = STROKE_MODES.join(' • ');
  document.querySelector('#keybinds').textContent = Object.entries(DEFAULT_KEYBINDS).map(([action,key]) => `${action}: ${key}`).join(' • ');
}

document.querySelectorAll('input').forEach(input => input.addEventListener('input', updatePlanner));
document.querySelector('#imageFile').addEventListener('change', event => event.target.files[0] && loadImage(event.target.files[0]));
document.querySelector('#continue').addEventListener('click', () => { state.progress = Math.min(state.layers.length - 1, state.progress + 1); renderLayers(); });
document.querySelector('#pause').addEventListener('click', () => document.body.classList.toggle('paused'));
document.querySelector('#simulate').addEventListener('click', simulateCurrentLayer);
document.querySelector('#sketch').addEventListener('click', renderSketchMask);
document.querySelector('#export').addEventListener('click', exportProject);

renderCapabilities();
updatePlanner();
