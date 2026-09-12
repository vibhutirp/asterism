import test from 'node:test';
import assert from 'node:assert/strict';
import { aggregateParticles, createDetailTransition, createGalaxyRegistry, galaxyDetail, glowBrightness } from './galaxy-model.ts';
import type { SceneTopic, Vec3 } from './scene-model.ts';

const sceneTopic = (id: string, center: Vec3, memoryCount = 4, categoryId = 'work', category = 'Work'): SceneTopic => ({
  topic: { id, name: id, description: '', categoryId, category, memoryCount }, center, radius: 1, seed: 1,
});

test('galaxy geometry is deterministic, bounded, volumetric, prefix stable, and capped', () => {
  const points = aggregateParticles('atlas', 12000, 20);
  assert.deepEqual(aggregateParticles('atlas', 128, 20), points.slice(0, 384));
  assert.notDeepEqual(aggregateParticles('other', 128, 20), points.slice(0, 384));
  let interior = 0;
  for (let index = 0; index < points.length; index += 3) {
    const normalized = Math.hypot(points[index] / 11.6, points[index + 1] / (11.6 * 0.72), points[index + 2] / (11.6 * 0.86));
    assert.ok(normalized <= 1.000001);
    if (normalized < 0.5) interior++;
  }
  assert.ok(interior / 12000 > 0.11 && interior / 12000 < 0.14);
  assert.equal(aggregateParticles('large', 100000, 20).length, 64000 * 3);
});

test('galaxy centers stay fixed and radii only grow for newly observed topic IDs', () => {
  const registry = createGalaxyRegistry();
  const initial = [sceneTopic('a', [-10, 0, 0]), sceneTopic('b', [10, 4, 0])];
  const before = registry.register(initial, new Set(['a', 'b']))[0];
  assert.deepEqual(before.center, [0, 2, 0]);
  assert.ok(before.radius >= Math.hypot(10, 2) + 10);

  const filtered = registry.register([...initial].reverse().map(topic => ({
    ...topic, center: [999, 999, 999] as Vec3,
    topic: { ...topic.topic, memoryCount: 500 },
  })), new Set(['a']))[0];
  assert.deepEqual(filtered.center, before.center);
  assert.equal(filtered.radius, before.radius);

  const added = registry.register([...initial, sceneTopic('c', [60, 2, 0])], new Set(['a', 'b', 'c']))[0];
  assert.deepEqual(added.center, before.center);
  assert.equal(added.radius, 70);
  const removedAgain = registry.register(initial, new Set())[0];
  assert.equal(removedAgain.radius, 70);
  before.center[0] = 1234;
  assert.deepEqual(registry.register(initial, new Set())[0].center, [0, 2, 0]);
});

test('totals use the current scene while matching data uses the visible filter', () => {
  const registry = createGalaxyRegistry();
  const result = registry.register([
    sceneTopic('a', [0, 0, 0], 3), sceneTopic('b', [10, 0, 0], 8),
    sceneTopic('p', [0, 20, 0], 5, 'personal', 'Personal'),
  ], new Set(['b']));
  assert.deepEqual(result.map(galaxy => galaxy.id), ['personal', 'work']);
  const work = result[1];
  assert.equal(work.topicCount, 2);
  assert.equal(work.memoryCount, 11);
  assert.equal(work.matchingTopics, 1);
  assert.equal(work.matchingMemories, 8);
  assert.deepEqual(work.topics.map(topic => topic.topic.id), ['b']);
  assert.equal(result[0].matchingTopics, 0, 'no-match groups remain available to the caller');
  assert.deepEqual(result[0].topics, []);
});

test('galaxy detail uses a smoothstep between five and three radii', () => {
  assert.equal(galaxyDetail(50, 10), 0);
  assert.equal(galaxyDetail(40, 10), 0.5);
  assert.equal(galaxyDetail(30, 10), 1);
  assert.equal(galaxyDetail(10, 10), 1);
});

test('detail transition interpolates, reverses continuously, settles exactly, and jumps immediately', () => {
  const transition = createDetailTransition();
  assert.equal(transition.settled, true);
  assert.equal(transition.update(1, 100), 0);
  assert.equal(transition.settled, false);
  assert.equal(transition.update(1, 325), 0.5);
  assert.equal(transition.update(0, 325), 0.5);
  assert.ok(transition.update(0, 550) > 0 && transition.update(0, 550) < 0.5);
  assert.equal(transition.update(0, 775), 0);
  assert.equal(transition.settled, true);
  assert.equal(transition.update(1, 800, true), 1);
  assert.equal(transition.settled, true);
});

test('glow brightness stays bounded, repeats every eight seconds, and uses seed phase', () => {
  for (let time = 0; time <= 8000; time += 125) {
    const value = glowBrightness(time, 123456789);
    assert.ok(value >= 0.9 && value <= 1);
    assert.ok(Math.abs(value - glowBrightness(time + 8000, 123456789)) < 1e-12);
  }
  assert.notEqual(glowBrightness(0, 1), glowBrightness(0, 2));
});
