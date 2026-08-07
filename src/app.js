import { STROKE_MODES, DEFAULT_KEYBINDS, analyzeColors, estimateLayer, fitToArea } from './core.js';

const state = { layers: [], progress: 0, mode: 'Full Color', preset: 'Letter' };
const samplePixels = [[8,8,8],[42,42,42],[112,66,20],[20,40,120],[200,26,31],[236,142,36],[242,215,60],[63,160,76],[92,177,230],[245,245,245],[8,8,8],[200,26,31]];

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

function updatePlanner() {
  const tolerance = Number(document.querySelector('#tolerance').value);
  const minPercentage = Number(document.querySelector('#minPercentage').value);
  const speed = Number(document.querySelector('#speed').value);
  state.layers = analyzeColors(samplePixels, { tolerance, minPercentage }).map(layer => estimateLayer(layer, speed));
  renderLayers();
  const fit = fitToArea({ width: 320, height: 260 }, { width: 250, height: 200 });
  document.querySelector('#calibration').textContent = `Scaled to ${fit.width} × ${fit.height} mm at ${(fit.scale*100).toFixed(0)}%, centered ${fit.x} mm / ${fit.y} mm.`;
}

function renderCapabilities() {
  document.querySelector('#strokes').textContent = STROKE_MODES.join(' • ');
  document.querySelector('#keybinds').textContent = Object.entries(DEFAULT_KEYBINDS).map(([action,key]) => `${action}: ${key}`).join(' • ');
}

document.querySelectorAll('input').forEach(input => input.addEventListener('input', updatePlanner));
document.querySelector('#continue').addEventListener('click', () => { state.progress = Math.min(state.layers.length - 1, state.progress + 1); renderLayers(); });
document.querySelector('#pause').addEventListener('click', () => document.body.classList.toggle('paused'));

renderCapabilities();
updatePlanner();
