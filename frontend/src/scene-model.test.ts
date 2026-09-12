import test from 'node:test';
import assert from 'node:assert/strict';
import { cloudParticles, cloudRadius, createCameraTransition, createSceneRegistry, particleBudget } from './scene-model.ts';
import type { CameraPose, Vec3 } from './scene-model.ts';
import type { Topic } from './models.ts';

const topic = (id: string, category = 'Product', memoryCount = 8): Topic => ({
  id, name: id, description: '', categoryId: category.toLowerCase(), category, memoryCount,
});
const distance = (a: Vec3, b: Vec3) => Math.hypot(...a.map((value, index) => value - b[index]));

test('cloud particles fill a deterministic ellipsoid volume and preserve prefixes', () => {
  const points = cloudParticles('atlas', 12000);
  assert.deepEqual(cloudParticles('atlas', 128), points.slice(0, 384));
  assert.notDeepEqual(cloudParticles('camping', 128), points.slice(0, 384));
  let interior = 0;
  let positiveDepth = 0;
  let negativeDepth = 0;
  const sum = [0, 0, 0];
  for (let i = 0; i < points.length; i += 3) {
    const radius = Math.hypot(points[i], points[i + 1] / 0.72, points[i + 2] / 0.86);
    assert.ok(radius <= 1.000001);
    if (radius < 0.5) interior++;
    if (points[i + 2] > 0.3) positiveDepth++;
    if (points[i + 2] < -0.3) negativeDepth++;
    for (let axis = 0; axis < 3; axis++) sum[axis] += points[i + axis];
  }
  // A uniform volume puts one eighth of its particles inside half its radius.
  assert.ok(interior / 12000 > 0.11 && interior / 12000 < 0.14);
  assert.ok(positiveDepth > 2000 && negativeDepth > 2000);
  assert.ok(sum.every(value => Math.abs(value / 12000) < 0.02));
  assert.equal(cloudParticles('empty', 0).length, 0);
});

test('cloud radii grow logarithmically and the global particle cap covers large datasets', () => {
  assert.equal(cloudRadius(0), 0);
  assert.equal(cloudRadius(1), 4);
  assert.ok(cloudRadius(100) > cloudRadius(10));
  assert.equal(cloudRadius(1e12), 10);
  assert.ok(cloudRadius(100) - cloudRadius(10) < cloudRadius(10) - cloudRadius(1) + 0.001);
  for (const count of [0, 1, 3, 100, 500, 501, 1000, 64000, 64001, 1000000]) {
    const budget = particleBudget(count);
    assert.ok(Number.isInteger(budget) && budget >= 0 && budget <= 128);
    assert.ok(budget * count <= 64000);
  }
});

test('append-only ID centers survive filters, reorders, counts, additions and category changes', () => {
  const registry = createSceneRegistry();
  const initial = [topic('atlas'), topic('pricing'), topic('camping', 'Personal')];
  const before = registry.register(initial);
  const expected = new Map(before.map(item => [item.topic.id, item.center]));
  const after = registry.register([topic('new'), ...[...initial].reverse().map(item => ({ ...item, memoryCount: 100 }))]);
  for (const item of after.slice(1)) assert.deepEqual(item.center, expected.get(item.topic.id));
  assert.deepEqual(registry.register([topic('pricing', 'Renamed')])[0].center, expected.get('pricing'));
  assert.deepEqual(registry.register(initial).map(item => item.center), before.map(item => item.center));
  assert.ok(after[1].radius > before.find(item => item.topic.id === after[1].topic.id)!.radius);
  assert.deepEqual(createSceneRegistry().register([...initial].reverse()).reverse(), before);
  before[0].center[0] = 999;
  assert.notEqual(registry.register(initial)[0].center[0], 999, 'returned positions cannot mutate registry state');
});

test('category anchors remain recognizable and all future topic slots remain separated', () => {
  const registry = createSceneRegistry();
  const initial = registry.register([topic('atlas'), topic('pricing'), topic('camping', 'Personal')]);
  assert.deepEqual(initial[0].center, [-22, 8, 0]);
  assert.deepEqual(initial[2].center, [22, -12, -10]);
  assert.ok(initial.every(item => Math.hypot(...item.center) < 55));
  const many = ['Product', 'Personal', 'Research', 'Travel', 'Work', 'Learning'].flatMap(category =>
    Array.from({ length: 40 }, (_, index) => topic(`${category}-${index}`, category)));
  const result = [...initial, ...registry.register(many)];
  for (let i = 0; i < result.length; i++) {
    for (let j = i + 1; j < result.length; j++) {
      assert.ok(distance(result[i].center, result[j].center) >= 22, `${result[i].topic.id} overlaps ${result[j].topic.id}`);
    }
  }
});

test('camera transitions interpolate both pose fields and finish at the exact destination', () => {
  const camera = createCameraTransition();
  const from: CameraPose = { position: [0, 0, 100], target: [0, 0, 0] };
  const to: CameraPose = { position: [20, 10, 50], target: [20, 10, 0] };
  assert.equal(camera.sample(0), null);
  camera.begin(from, to, 100, 1000);
  assert.deepEqual(camera.sample(0), { ...from, done: false });
  assert.deepEqual(camera.sample(600), { position: [10, 5, 75], target: [10, 5, 0], done: false });
  assert.deepEqual(camera.sample(1100), { ...to, done: true });
  assert.equal(camera.sample(1200), null);
  camera.begin(from, to, 2000, 0);
  assert.deepEqual(camera.sample(2000), { ...to, done: true });
});

test('cancelled camera transitions never resume and a new transition replaces old motion', () => {
  const camera = createCameraTransition();
  const from: CameraPose = { position: [0, 0, 100], target: [0, 0, 0] };
  const oldDestination: CameraPose = { position: [80, 0, 30], target: [80, 0, 0] };
  const newDestination: CameraPose = { position: [-30, 0, 30], target: [-30, 0, 0] };
  camera.begin(from, oldDestination, 0, 1000);
  const interrupted = camera.sample(200)!;
  camera.cancel();
  assert.equal(camera.sample(300), null);
  assert.equal(camera.sample(5000), null);
  camera.begin(interrupted, newDestination, 200, 100);
  newDestination.position[0] = 999;
  assert.equal(camera.sample(300)!.position[0], -30, 'begin snapshots mutable camera vectors');
  assert.equal(camera.sample(1000), null);
  camera.begin(from, oldDestination, 0, 1000);
  camera.begin(from, { position: [-10, 0, 20], target: [-10, 0, 0] }, 50, 50);
  assert.equal(camera.sample(100)!.position[0], -10);
});
