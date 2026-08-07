export const STROKE_MODES = [
  'Outline','Fill','Cross Hatch','Sketch','Single Line','Double Line','Spiral Fill','Contour Fill','Stippling','Zigzag Fill','Custom patterns'
];
export const DEFAULT_KEYBINDS = { start:'Ctrl+Enter', pause:'F8', resume:'F9', emergencyStop:'ESC', abortJob:'F10' };
export const SUPPORTED_IMAGE_TYPES = ['image/png','image/jpeg','image/bmp','image/webp','image/tiff','image/svg+xml'];

export function quantizeColor([r,g,b], tolerance = 32) {
  const step = Math.max(1, Number(tolerance));
  return [r,g,b].map(v => Math.min(255, Math.round(v / step) * step));
}

export function luminance([r,g,b]) {
  return 0.2126*r + 0.7152*g + 0.0722*b;
}

export function analyzeColors(pixels, { tolerance = 32, minPercentage = 0, sort = 'darkest' } = {}) {
  const buckets = new Map();
  for (const pixel of pixels) {
    const key = quantizeColor(pixel, tolerance).join(',');
    buckets.set(key, (buckets.get(key) || 0) + 1);
  }
  const total = Math.max(1, pixels.length);
  return [...buckets.entries()]
    .map(([key, count]) => ({ color: key.split(',').map(Number), count, percentage: count / total }))
    .filter(layer => layer.percentage * 100 >= minPercentage)
    .sort((a,b) => sort === 'lightest' ? luminance(b.color)-luminance(a.color) : luminance(a.color)-luminance(b.color));
}

export function estimateLayer(layer, speed = 1) {
  const pixels = layer.count ?? 0;
  const drawingSeconds = Math.ceil((pixels / Math.max(0.1, speed)) * 0.02);
  return { ...layer, etaSeconds: drawingSeconds, markerUsage: +(pixels * 0.00004).toFixed(2) };
}

export function fitToArea(image, area, mode = 'fit') {
  const scaleX = area.width / image.width;
  const scaleY = area.height / image.height;
  const scale = mode === 'fill' ? Math.max(scaleX, scaleY) : Math.min(scaleX, scaleY);
  const width = +(image.width * scale).toFixed(2);
  const height = +(image.height * scale).toFixed(2);
  return { width, height, scale, x: +((area.width - width)/2).toFixed(2), y: +((area.height - height)/2).toFixed(2) };
}

export function buildNearestNeighborPath(points) {
  const remaining = points.map((point, index) => ({ point, index }));
  const path = [];
  let current = remaining.shift();
  if (!current) return path;
  path.push(current.point);
  while (remaining.length) {
    let best = 0;
    let bestDistance = Infinity;
    for (let i = 0; i < remaining.length; i += 1) {
      const dx = remaining[i].point.x - current.point.x;
      const dy = remaining[i].point.y - current.point.y;
      const distance = dx*dx + dy*dy;
      if (distance < bestDistance) { bestDistance = distance; best = i; }
    }
    current = remaining.splice(best, 1)[0];
    path.push(current.point);
  }
  return path;
}

export function pixelsFromImageData(imageData, { sampleStep = 1, alphaThreshold = 8 } = {}) {
  const pixels = [];
  const step = Math.max(1, Number(sampleStep));
  for (let y = 0; y < imageData.height; y += step) {
    for (let x = 0; x < imageData.width; x += step) {
      const index = (y * imageData.width + x) * 4;
      const alpha = imageData.data[index + 3];
      if (alpha >= alphaThreshold) pixels.push([imageData.data[index], imageData.data[index + 1], imageData.data[index + 2]]);
    }
  }
  return pixels;
}

export function buildLayerPath(imageData, targetColor, { tolerance = 32, sampleStep = 2 } = {}) {
  const points = [];
  const step = Math.max(1, Number(sampleStep));
  const limit = Math.max(1, Number(tolerance));
  for (let y = 0; y < imageData.height; y += step) {
    for (let x = 0; x < imageData.width; x += step) {
      const index = (y * imageData.width + x) * 4;
      const color = [imageData.data[index], imageData.data[index + 1], imageData.data[index + 2]];
      const distance = Math.max(...color.map((channel, i) => Math.abs(channel - targetColor[i])));
      if (distance <= limit) points.push({ x, y });
    }
  }
  return buildNearestNeighborPath(points);
}

export function thresholdSketchPixels(imageData, { threshold = 190 } = {}) {
  const points = [];
  for (let y = 0; y < imageData.height; y += 1) {
    for (let x = 0; x < imageData.width; x += 1) {
      const index = (y * imageData.width + x) * 4;
      const brightness = luminance([imageData.data[index], imageData.data[index + 1], imageData.data[index + 2]]);
      if (brightness < threshold && imageData.data[index + 3] > 8) points.push({ x, y });
    }
  }
  return points;
}
