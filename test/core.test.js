import test from 'node:test';
import assert from 'node:assert/strict';
import { analyzeColors, fitToArea, buildNearestNeighborPath } from '../src/core.js';

test('analyzeColors groups similar colors and sorts darkest first', () => {
  const layers = analyzeColors([[1,1,1],[2,2,2],[250,250,250]], { tolerance: 16 });
  assert.equal(layers.length, 2);
  assert.deepEqual(layers[0].color, [0,0,0]);
  assert.equal(layers[0].count, 2);
});

test('fitToArea preserves aspect ratio', () => {
  const fit = fitToArea({ width: 320, height: 260 }, { width: 250, height: 200 });
  assert.equal(fit.height, 200);
  assert.equal(fit.width, 246.15);
});

test('buildNearestNeighborPath reduces travel by visiting nearest point', () => {
  const path = buildNearestNeighborPath([{x:0,y:0},{x:10,y:0},{x:1,y:0}]);
  assert.deepEqual(path.map(p => p.x), [0,1,10]);
});
