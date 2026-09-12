export type Rect = { x: number; y: number; w: number; h: number };

type LabelPlacer = {
  place: (px: number, py: number, w: number, h: number, priority?: boolean) => Rect | null;
};

const clamp = (value: number, low: number, high: number) => Math.min(high, Math.max(low, value));

export function createLabelPlacer(bounds: Rect, obstacles: Rect[], gap = 8): LabelPlacer {
  const area = { ...bounds };
  const reserved = obstacles.map(rect => ({ ...rect }));
  const placed: Rect[] = [];
  const spacing = Math.max(0, gap);

  const overlaps = (candidate: Rect, blocker: Rect) =>
    candidate.x < blocker.x + blocker.w + spacing
    && candidate.x + candidate.w + spacing > blocker.x
    && candidate.y < blocker.y + blocker.h + spacing
    && candidate.y + candidate.h + spacing > blocker.y;

  const valid = (candidate: Rect) => [...reserved, ...placed].every(blocker => !overlaps(candidate, blocker));

  return {
    place(px, py, w, h, priority = false) {
      if (![area.x, area.y, area.w, area.h, px, py, w, h].every(Number.isFinite)
        || area.w < 0 || area.h < 0 || w < 0 || h < 0 || w > area.w || h > area.h) return null;

      const right = area.x + area.w - w;
      const bottom = area.y + area.h - h;
      const preferred = { x: clamp(px, area.x, right), y: clamp(py, area.y, bottom), w, h };
      if (valid(preferred)) {
        placed.push(preferred);
        return { ...preferred };
      }
      if (!priority) return null;

      const blockers = [...reserved, ...placed];
      const xs = [preferred.x, area.x, right];
      const ys = [preferred.y, area.y, bottom];
      for (const blocker of blockers) {
        xs.push(blocker.x - w - spacing, blocker.x + blocker.w + spacing);
        ys.push(blocker.y - h - spacing, blocker.y + blocker.h + spacing);
      }

      let best: Rect | null = null;
      let bestDistance = Infinity;
      const seen = new Set<string>();
      for (const x of xs) {
        if (x < area.x || x > right) continue;
        for (const y of ys) {
          if (y < area.y || y > bottom) continue;
          const key = `${x}\u0000${y}`;
          if (seen.has(key)) continue;
          seen.add(key);
          const candidate = { x, y, w, h };
          if (!valid(candidate)) continue;
          const distance = (x - px) ** 2 + (y - py) ** 2;
          if (distance < bestDistance) {
            best = candidate;
            bestDistance = distance;
          }
        }
      }

      if (!best) return null;
      placed.push(best);
      return { ...best };
    },
  };
}
