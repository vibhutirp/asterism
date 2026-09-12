import type { ApiTopic, ApiTopicDetail, Memory, Topic, TopicDetail, Update } from './models.ts';

export function adaptTopic(raw: ApiTopic): Topic {
  if (!raw || typeof raw.id !== 'string' || typeof raw.name !== 'string' || !raw.galaxy ||
      typeof raw.galaxy.id !== 'string' || typeof raw.galaxy.name !== 'string' ||
      !Number.isInteger(raw.memoryCount) || raw.memoryCount < 0) throw new Error('The topic response is incomplete.');
  return { id: raw.id, name: raw.name, description: raw.description || '', categoryId: raw.galaxy.id,
    category: raw.galaxy.name, memoryCount: raw.memoryCount };
}
export function safeSourceUrl(value: string | null | undefined): string | undefined {
  if (!value) return undefined;
  try { const u = new URL(value); return ['https:', 'http:'].includes(u.protocol) ? u.href : undefined; }
  catch { return undefined; }
}
export function adaptDetail(raw: ApiTopicDetail): TopicDetail {
  const topic = adaptTopic(raw.topic);
  if (!Array.isArray(raw.memories) || !Number.isInteger(raw.memoryCount) || raw.memoryCount < 0) throw new Error('The memory response is incomplete.');
  const memories: Memory[] = raw.memories.map(m => {
    if (!m || typeof m.id !== 'string' || typeof m.content !== 'string' || !m.source || typeof m.source.source !== 'string' || typeof m.source.messageId !== 'string') throw new Error('A memory is missing source metadata.');
    return { id: m.id, text: m.content, type: m.memoryType || 'statement', source: {
      messageId: m.source.messageId, service: m.source.source,
      url: safeSourceUrl(m.source.sourceUrl), receivedAt: m.source.timestamp, sample: false,
    }};
  });
  return { topic: { ...topic, memoryCount: raw.memoryCount }, summary: raw.overview || topic.description,
    summaryKind: 'Topic description', memories };
}
export function memoryTypeLabel(type: string): string {
  if (type === 'fact') return 'Statement';
  return type ? type[0].toUpperCase() + type.slice(1) : 'Statement';
}
export function filterTopics(topics: Topic[], query: string): Topic[] {
  const q = query.trim().toLocaleLowerCase();
  return q ? topics.filter(t => t.name.toLocaleLowerCase().includes(q)) : topics;
}
export function coreDiameter(count: number): number { return Math.min(20, 8 + 2 * Math.log2(Math.max(0, count) + 1)); }

// Append-only registries: counts, response ordering and filters cannot move existing topics.
export function createLayoutRegistry() {
  const categories = new Map<string, number>();
  const slots = new Map<string, { categoryId: string; index: number }>();
  const counts = new Map<string, number>();
  return {
    register(topics: Topic[]) {
      for (const topic of topics) {
        if (!categories.has(topic.categoryId)) categories.set(topic.categoryId, categories.size);
        const existing = slots.get(topic.id);
        if (!existing || existing.categoryId !== topic.categoryId) {
          const index = counts.get(topic.categoryId) || 0;
          slots.set(topic.id, { categoryId: topic.categoryId, index }); counts.set(topic.categoryId, index + 1);
        }
      }
    },
    slot(id: string) { return slots.get(id); },
    categoryIndex(id: string) { return categories.get(id) ?? 0; },
  };
}
export function observedUpdates(previous: Topic[], next: Topic[]): Update[] {
  const byId = new Map(previous.map(t => [t.id, t]));
  return next.flatMap(t => {
    const old = byId.get(t.id);
    if (old && old.memoryCount === t.memoryCount && old.description === t.description && old.name === t.name) return [];
    return [{ topicId: t.id, topicName: t.name, label: old ? 'Updated' : 'New',
      note: 'Observed during this session', sample: false }];
  });
}
// Aborts superseded work and also guards against transports which ignore abort.
export function createRequestGate() {
  let generation = 0;
  let controller: AbortController | undefined;
  return {
    begin() {
      controller?.abort(); controller = new AbortController();
      const current = ++generation;
      return { signal: controller.signal, isCurrent: () => current === generation && !controller?.signal.aborted };
    },
    cancel() { generation++; controller?.abort(); },
  };
}
export function formatReceived(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.valueOf()) ? 'Time unavailable' : new Intl.DateTimeFormat('en-US', {
    month: 'short', day: 'numeric', year: 'numeric', hour: 'numeric', minute: '2-digit',
  }).format(date);
}
