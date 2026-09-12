import type { Topic } from './models.ts';

export type Vec3 = [number, number, number];
export interface SceneTopic { topic: Topic; center: Vec3; radius: number; seed: number }
export interface CameraPose { position: Vec3; target: Vec3 }

function hash(value: string): number {
  let seed = 2166136261;
  for (let i = 0; i < value.length; i++) seed = Math.imul(seed ^ value.charCodeAt(i), 16777619);
  return seed >>> 0;
}

/** A zero-memory topic has no cloud; nonempty clouds grow gently, then stop. */
export function cloudRadius(count: number): number {
  if (!(count > 0)) return 0;
  return Math.min(10, 4 + Math.log2(Math.max(1, count)) * 0.6);
}

/** Per-topic density: the renderer can never exceed 64,000 total particles. */
export function particleBudget(topicCount: number): number {
  if (!Number.isFinite(topicCount) || topicCount <= 0) return 0;
  return Math.min(128, Math.floor(64000 / Math.ceil(topicCount)));
}

/** Uniform volume in an ellipsoid with axes 1 : .72 : .86, independent of count. */
export function cloudParticles(id: string, count: number): Float32Array {
  const length = Number.isFinite(count) ? Math.min(64000, Math.max(0, Math.floor(count))) : 0;
  const points = new Float32Array(length * 3);
  let seed = hash(id);
  const random = () => {
    seed = (seed + 0x6d2b79f5) >>> 0;
    let value = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    value ^= value + Math.imul(value ^ (value >>> 7), 61 | value);
    return ((value ^ (value >>> 14)) >>> 0) / 4294967296;
  };
  for (let i = 0; i < length; i++) {
    const vertical = random() * 2 - 1;
    const angle = random() * Math.PI * 2;
    const radius = Math.cbrt(random());
    const horizontal = Math.sqrt(1 - vertical * vertical);
    points[i * 3] = radius * horizontal * Math.cos(angle);
    points[i * 3 + 1] = radius * vertical * 0.72;
    points[i * 3 + 2] = radius * horizontal * Math.sin(angle) * 0.86;
  }
  return points;
}

// Enumerate a half-plane lattice in compact shells. Every slot is 24 units apart;
// opposing half-planes and 72-unit category bands leave room for future additions.
function latticeSlot(index: number): [number, number] {
  if (index === 0) return [0, 0];
  let remainder = index - 1;
  let shell = 1;
  while (remainder >= 2 * shell + 1) remainder -= 2 * shell++ + 1;
  if (remainder === 0) return [shell, 0];
  const offset = Math.ceil(remainder / 2);
  return [shell - offset, offset * (remainder % 2 ? 1 : -1)];
}

export function createSceneRegistry() {
  const categories = new Map<string, { index: number; nextSlot: number }>();
  const occupiedCategories = new Set<number>();
  const centers = new Map<string, Vec3>();
  let nextCategory = 2;

  return {
    register(topics: Topic[]): SceneTopic[] {
      // Sorting only unseen IDs makes a batch independent of its source ordering.
      const unseen = [...topics].filter(topic => !centers.has(topic.id))
        .sort((a, b) => a.categoryId.localeCompare(b.categoryId) || a.id.localeCompare(b.id));
      for (const topic of unseen) {
        if (centers.has(topic.id)) continue;
        let category = categories.get(topic.categoryId);
        if (!category) {
          const label = topic.category.toLowerCase();
          const preferred = topic.categoryId.toLowerCase() === 'product' || label === 'product' ? 0
            : topic.categoryId.toLowerCase() === 'personal' || label === 'personal' ? 1 : -1;
          const index = preferred >= 0 && !occupiedCategories.has(preferred) ? preferred : nextCategory++;
          category = { index, nextSlot: 0 };
          categories.set(topic.categoryId, category);
          occupiedCategories.add(index);
        }
        const [column, depth] = latticeSlot(category.nextSlot++);
        const right = category.index % 2 === 1;
        const row = Math.floor(category.index / 2);
        centers.set(topic.id, [
          (right ? 22 : -22) + column * (right ? 24 : -24),
          (right ? -12 : 8) + row * 72 + (column === 0 && depth === 0 ? 0 : Math.sin(hash(topic.id)) * 3),
          (right ? -10 : 0) + depth * 24 + column * 5,
        ]);
      }
      return topics.map(topic => ({
        topic, center: [...centers.get(topic.id)!] as Vec3,
        radius: cloudRadius(topic.memoryCount), seed: hash(topic.id),
      }));
    },
  };
}

function copyPose(pose: CameraPose): CameraPose {
  return { position: [...pose.position], target: [...pose.target] };
}

export function createCameraTransition() {
  let active: { from: CameraPose; to: CameraPose; start: number; duration: number } | null = null;
  return {
    begin(from: CameraPose, to: CameraPose, now: number, duration: number): void {
      active = { from: copyPose(from), to: copyPose(to), start: now, duration: Math.max(0, duration) };
    },
    sample(now: number): (CameraPose & { done: boolean }) | null {
      if (!active) return null;
      const { from, to, start, duration } = active;
      const progress = duration === 0 ? 1 : Math.max(0, Math.min(1, (now - start) / duration));
      const eased = progress * progress * (3 - 2 * progress);
      const interpolate = (a: Vec3, b: Vec3): Vec3 => a.map((value, index) => value + (b[index] - value) * eased) as Vec3;
      const sample = { position: interpolate(from.position, to.position), target: interpolate(from.target, to.target), done: progress === 1 };
      if (sample.done) active = null;
      return sample;
    },
    cancel(): void { active = null; },
  };
}
