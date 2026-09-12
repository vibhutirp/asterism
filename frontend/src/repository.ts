import type { ApiTopic, ApiTopicDetail, Repository } from './models.ts';
import { adaptDetail, adaptTopic } from './knowledge.ts';
import { sampleDetails, scenarioTopics } from './fixtures.ts';

async function readJson<T>(path: string, signal: AbortSignal): Promise<T> {
  const response = await fetch(path, { method: 'GET', signal, headers: { Accept: 'application/json' } });
  if (!response.ok) throw new Error(response.status === 404 ? 'This topic is no longer available.' : 'Stored context could not be loaded. Please try again.');
  return response.json() as Promise<T>;
}
function wait(ms: number, signal: AbortSignal): Promise<void> {
  return new Promise((resolve, reject) => {
    if (signal.aborted) { reject(new DOMException('Aborted', 'AbortError')); return; }
    const abort = () => { clearTimeout(timer); reject(new DOMException('Aborted', 'AbortError')); };
    const timer = setTimeout(() => { signal.removeEventListener('abort', abort); resolve(); }, ms);
    signal.addEventListener('abort', abort, { once: true });
  });
}
export function makeRepository(mode: 'fixture' | 'api', workspace: string, scenario = ''): Repository {
  const query = `workspaceId=${encodeURIComponent(workspace)}`;
  let listReads = 0;
  return mode === 'api' ? {
    mode,
    async list(signal) {
      const raw = await readJson<{ topics: ApiTopic[] }>(`/api/topics?${query}`, signal);
      if (!Array.isArray(raw.topics)) throw new Error('The topic response is incomplete.');
      return raw.topics.map(adaptTopic);
    },
    async detail(id, signal) {
      return adaptDetail(await readJson<ApiTopicDetail>(`/api/topics/${encodeURIComponent(id)}?${query}`, signal));
    },
  } : {
    mode,
    async list(signal) {
      await wait(scenario === 'loading' ? 2500 : 220, signal);
      listReads++;
      if (scenario === 'error' || (scenario === 'stale' && listReads > 1)) throw new Error('Stored context could not be loaded. Please try again.');
      return structuredClone(scenarioTopics(scenario));
    },
    async detail(id, signal) {
      await wait(180, signal);
      if (scenario === 'detail-error') throw new Error('This topic could not be loaded. Please try again.');
      const topic = scenarioTopics(scenario).find(t => t.id === id);
      if (!topic) throw new Error('This topic is no longer available.');
      const detail = sampleDetails(id, topic);
      if (scenario === 'missing-source') for (const m of detail.memories) { m.source.originalText = undefined; m.source.author = undefined; m.source.channel = undefined; }
      if (scenario === 'long') {
        detail.memories[0].source.originalText = `${detail.memories[0].source.originalText}\n\n${'We should preserve the original context, including qualifications and open questions, when we review the onboarding experience. '.repeat(35)}`;
      }
      return detail;
    },
  };
}
