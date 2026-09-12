import { cloudParticles } from './scene-model.ts';
import type { SceneTopic, Vec3 } from './scene-model.ts';

export interface SceneGalaxy {
  id: string;
  name: string;
  center: Vec3;
  radius: number;
  topics: SceneTopic[];
  topicCount: number;
  memoryCount: number;
  matchingTopics: number;
  matchingMemories: number;
}

interface GalaxyGeometry {
  center: Vec3;
  radius: number;
  observedTopicIds: Set<string>;
}

const distance = (left: Vec3, right: Vec3): number => Math.hypot(
  left[0] - right[0], left[1] - right[1], left[2] - right[2],
);

function boundsCenter(topics: SceneTopic[]): Vec3 {
  const low: Vec3 = [...topics[0].center];
  const high: Vec3 = [...topics[0].center];
  for (const { center } of topics.slice(1)) {
    for (let axis = 0; axis < 3; axis++) {
      low[axis] = Math.min(low[axis], center[axis]);
      high[axis] = Math.max(high[axis], center[axis]);
    }
  }
  return low.map((value, axis) => (value + high[axis]) / 2) as Vec3;
}

function requiredRadius(center: Vec3, topic: SceneTopic): number {
  // Ten is the scene model's fixed maximum topic-cloud extent. Galaxy geometry
  // therefore does not breathe as a topic's current memory count changes.
  return distance(center, topic.center) + 10;
}

export function createGalaxyRegistry() {
  const geometry = new Map<string, GalaxyGeometry>();

  return {
    register(scene: SceneTopic[], visibleIds: Set<string>): SceneGalaxy[] {
      const current = new Map<string, SceneTopic[]>();
      for (const topic of scene) {
        const list = current.get(topic.topic.categoryId) ?? [];
        list.push(topic);
        current.set(topic.topic.categoryId, list);
      }

      return [...current.entries()]
        .sort(([left], [right]) => left.localeCompare(right))
        .map(([id, allTopics]) => {
          let stored = geometry.get(id);
          if (!stored) {
            const center = boundsCenter(allTopics);
            stored = {
              center,
              radius: Math.max(18, ...allTopics.map(topic => requiredRadius(center, topic))),
              observedTopicIds: new Set(allTopics.map(topic => topic.topic.id)),
            };
            geometry.set(id, stored);
          } else {
            for (const topic of allTopics) {
              if (stored.observedTopicIds.has(topic.topic.id)) continue;
              stored.observedTopicIds.add(topic.topic.id);
              stored.radius = Math.max(stored.radius, requiredRadius(stored.center, topic));
            }
          }

          const topics = allTopics.filter(topic => visibleIds.has(topic.topic.id));
          return {
            id,
            name: allTopics[0].topic.category,
            center: [...stored.center] as Vec3,
            radius: stored.radius,
            topics,
            topicCount: allTopics.length,
            memoryCount: allTopics.reduce((sum, topic) => sum + topic.topic.memoryCount, 0),
            matchingTopics: topics.length,
            matchingMemories: topics.reduce((sum, topic) => sum + topic.topic.memoryCount, 0),
          };
        });
    },
  };
}

export function galaxyDetail(distanceFromCenter: number, radius: number): number {
  if (!(radius > 0)) return distanceFromCenter <= 0 ? 1 : 0;
  const progress = Math.max(0, Math.min(1, (5 * radius - distanceFromCenter) / (2 * radius)));
  return progress * progress * (3 - 2 * progress);
}

export function aggregateParticles(topicId: string, count: number, galaxyRadius: number): Float32Array {
  const points = cloudParticles(`galaxy:${topicId}`, count);
  const scale = Math.max(0, galaxyRadius) * 0.58;
  for (let index = 0; index < points.length; index++) points[index] *= scale;
  return points;
}

export function createDetailTransition(initial = 0) {
  let from = initial;
  let value = initial;
  let target = initial;
  let startedAt = 0;
  let isSettled = true;

  const sample = (now: number): number => {
    if (isSettled) return value;
    const progress = Math.max(0, Math.min(1, (now - startedAt) / 450));
    const eased = progress * progress * (3 - 2 * progress);
    value = from + (target - from) * eased;
    if (progress === 1) {
      value = target;
      isSettled = true;
    }
    return value;
  };

  return {
    update(nextTarget: number, now: number, immediate = false): number {
      const current = sample(now);
      if (immediate) {
        from = nextTarget;
        value = nextTarget;
        target = nextTarget;
        startedAt = now;
        isSettled = true;
      } else if (Math.abs(nextTarget - target) > 0.001) {
        from = current;
        value = current;
        target = nextTarget;
        startedAt = now;
        isSettled = Math.abs(target - from) <= Number.EPSILON;
        if (isSettled) value = target;
      }
      return value;
    },
    get settled(): boolean { return isSettled; },
  };
}

export function glowBrightness(elapsedMs: number, seed: number): number {
  let mixed = Number.isFinite(seed) ? Math.floor(seed) >>> 0 : 0;
  mixed = Math.imul(mixed ^ (mixed >>> 16), 0x21f0aaad);
  mixed = Math.imul(mixed ^ (mixed >>> 15), 0x735a2d97);
  const phase = ((mixed ^ (mixed >>> 15)) >>> 0) / 4294967296 * Math.PI * 2;
  return 0.95 + Math.sin((elapsedMs / 8000) * Math.PI * 2 + phase) * 0.05;
}
