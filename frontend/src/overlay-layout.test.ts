import test from 'node:test';
import assert from 'node:assert/strict';
import { createLabelPlacer } from './overlay-layout.ts';
import type { Rect } from './overlay-layout.ts';

const separated = (a: Rect, b: Rect, gap = 8) =>
  a.x + a.w + gap <= b.x || b.x + b.w + gap <= a.x
  || a.y + a.h + gap <= b.y || b.y + b.h + gap <= a.y;

test('uses the expanded scene below controls and the freed former top and bottom bands', () => {
  const placer = createLabelPlacer({ x: 16, y: 16, w: 768, h: 868 }, []);
  assert.deepEqual(placer.place(300, 30, 184, 60), { x: 300, y: 30, w: 184, h: 60 });
  assert.deepEqual(placer.place(300, 810, 184, 60), { x: 300, y: 810, w: 184, h: 60 });
  assert.deepEqual(placer.place(20, 700, 184, 60), { x: 20, y: 700, w: 184, h: 60 });
});

test('top-center toggle and bottom-left stack exclude only their actual rectangles', () => {
  const controls = [
    { x: 330, y: 20, w: 140, h: 44 },
    { x: 20, y: 500, w: 190, h: 80 },
  ];
  const placer = createLabelPlacer({ x: 0, y: 0, w: 800, h: 600 }, controls);
  assert.equal(placer.place(340, 22, 100, 30), null);
  assert.equal(placer.place(24, 510, 100, 30), null);
  assert.deepEqual(placer.place(24, 80, 100, 30), { x: 24, y: 80, w: 100, h: 30 });
  assert.deepEqual(placer.place(600, 510, 100, 30), { x: 600, y: 510, w: 100, h: 30 });
});

test('popover and inspector rectangles are respected without mutating inputs', () => {
  const bounds = { x: 12, y: 12, w: 976, h: 676 };
  const obstacles = [{ x: 700, y: 12, w: 288, h: 676 }, { x: 420, y: 220, w: 240, h: 180 }];
  const original = structuredClone({ bounds, obstacles });
  const placer = createLabelPlacer(bounds, obstacles);
  assert.equal(placer.place(760, 100, 184, 60), null);
  assert.equal(placer.place(450, 250, 184, 60), null);
  assert.deepEqual({ bounds, obstacles }, original);
});

test('priority fallback can use the exact right edge beside a label', () => {
  const placer = createLabelPlacer({ x: 0, y: 100, w: 576, h: 60 }, [{ x: 196, y: 100, w: 184, h: 60 }]);
  assert.deepEqual(placer.place(204, 100, 184, 60, true), { x: 388, y: 100, w: 184, h: 60 });
});

test('returns null when no physical or unreserved space can fit', () => {
  assert.equal(createLabelPlacer({ x: 0, y: 0, w: 100, h: 80 }, []).place(0, 0, 101, 20, true), null);
  assert.equal(createLabelPlacer({ x: 0, y: 0, w: 100, h: 80 }, [{ x: 0, y: 0, w: 100, h: 80 }])
    .place(0, 0, 20, 20, true), null);
});

test('accepted labels reserve space and priority labels find distinct nearest slots', () => {
  const placer = createLabelPlacer({ x: 0, y: 0, w: 420, h: 220 }, []);
  const labels = [
    placer.place(100, 80, 100, 40),
    placer.place(100, 80, 100, 40),
    placer.place(100, 80, 100, 40, true),
    placer.place(100, 80, 100, 40, true),
  ];
  assert.equal(labels[1], null);
  const accepted = labels.filter((rect): rect is Rect => rect !== null);
  assert.equal(accepted.length, 3);
  for (let i = 0; i < accepted.length; i++) {
    for (let j = i + 1; j < accepted.length; j++) assert.ok(separated(accepted[i], accepted[j]));
  }
});

test('identical inputs and calls produce stable priority placement', () => {
  const run = () => {
    const placer = createLabelPlacer(
      { x: 0, y: 0, w: 500, h: 300 },
      [{ x: 180, y: 90, w: 140, h: 80 }, { x: 20, y: 20, w: 80, h: 60 }],
    );
    return [placer.place(200, 100, 100, 50, true), placer.place(200, 100, 100, 50, true)];
  };
  assert.deepEqual(run(), run());
});
