import test from 'node:test';
import assert from 'node:assert/strict';
import { adaptDetail, adaptTopic, coreDiameter, createLayoutRegistry, createRequestGate, filterTopics, memoryTypeLabel, observedUpdates, safeSourceUrl } from './knowledge.ts';
import { fixtureTopics, fixtureUpdates, sampleDetails, scenarioTopics } from './fixtures.ts';
import { makeRepository } from './repository.ts';
import type { ApiTopic, ApiTopicDetail } from './models.ts';

const topic: ApiTopic = { id: 'atlas', name: 'Atlas onboarding', description: 'First-run improvements.', galaxy: { id: 'product', name: 'Product' }, memoryCount: 1 };
const detail: ApiTopicDetail = { topic, galaxy: topic.galaxy, memoryCount: 1, overview: topic.description, memories: [{
  id: 'm1', topicId: 'atlas', topicName: topic.name, content: 'Could we try a checklist?', memoryType: 'question',
  confidence: 0.99, approximateTokenCount: 9, createdAt: '2026-09-12T21:10:00Z',
  source: { messageId: 's1', source: 'slack', sourceUrl: null, timestamp: '2026-09-12T21:10:00Z' },
}] };

test('name filtering is case-insensitive, trimmed, and does not search memory content', () => {
  assert.deepEqual(filterTopics(fixtureTopics, ' ATLAS ').map(t => t.id), ['atlas-onboarding', 'atlas-pricing']);
  assert.deepEqual(filterTopics(fixtureTopics, 'Maya'), []);
  assert.equal(filterTopics(fixtureTopics, '  '), fixtureTopics);
  assert.deepEqual(filterTopics(fixtureTopics, 'not a topic'), []);
});
test('adaptation preserves types, persisted counts, and missing provenance without invented quotes', () => {
  const adapted = adaptDetail(detail);
  assert.equal(adapted.summaryKind, 'Topic description');
  assert.equal(adapted.topic.memoryCount, 1);
  assert.equal(adapted.memories[0].type, 'question');
  assert.equal(adapted.memories[0].source.originalText, undefined);
  assert.equal(adapted.memories[0].source.author, undefined);
  assert.equal(adapted.memories[0].source.channel, undefined);
  assert.equal(adapted.memories[0].source.receivedAt, detail.memories[0].source.timestamp);
  assert.equal(adapted.memories[0].source.sample, false);
  assert.ok(!('confidence' in adapted.memories[0]));
  assert.ok(!('approximateTokenCount' in adapted.memories[0]));
  assert.equal(memoryTypeLabel('fact'), 'Statement');
  assert.equal(memoryTypeLabel('decision'), 'Decision');
  assert.equal(memoryTypeLabel('idea'), 'Idea');
});
test('malformed counts and source metadata fail visibly at the adapter boundary', () => {
  assert.throws(() => adaptTopic({ ...topic, memoryCount: -1 }), /incomplete/);
  assert.throws(() => adaptDetail({ ...detail, memories: [{ ...detail.memories[0], source: null! }] }), /source metadata/);
});
test('only genuine HTTP source links are exposed', () => {
  assert.equal(safeSourceUrl('https://example.com/source'), 'https://example.com/source');
  for (const value of ['javascript:alert(1)', 'data:text/html,test', '/guessed/slack', null]) assert.equal(safeSourceUrl(value), undefined);
});
test('stable ID slots survive reordered responses, changed counts, filtering and insertion', () => {
  const registry = createLayoutRegistry(); registry.register(fixtureTopics);
  const before = fixtureTopics.map(t => registry.slot(t.id));
  registry.register([...fixtureTopics].reverse().map(t => ({ ...t, memoryCount: 50 })));
  registry.register(filterTopics(fixtureTopics, 'pricing'));
  registry.register([{ ...fixtureTopics[0], id: 'new-topic' }, ...fixtureTopics]);
  assert.deepEqual(fixtureTopics.map(t => registry.slot(t.id)), before);
  assert.equal(registry.slot('new-topic')?.index, fixtureTopics.filter(t => t.categoryId === fixtureTopics[0].categoryId).length);
  assert.equal(coreDiameter(3), 12);
  assert.equal(coreDiameter(100000), 20);
});
test('update notices describe observed changes without fabricating historical events', () => {
  assert.deepEqual(observedUpdates(fixtureTopics, [...fixtureTopics].reverse()), []);
  const updates = observedUpdates(fixtureTopics, [{ ...fixtureTopics[0], memoryCount: 3 }, { ...fixtureTopics[1], id: 'new' }]);
  assert.deepEqual(updates.map(u => u.label), ['Updated', 'New']);
  assert.ok(updates.every(u => u.note === 'Observed during this session' && !u.sample));
});
test('late responses cannot overwrite a newer selection even if transport ignores abort', async () => {
  const gate = createRequestGate(); const first = gate.begin(); let displayed = '';
  let finishFirst!: () => void;
  const late = new Promise<void>(resolve => { finishFirst = resolve; }).then(() => { if (first.isCurrent()) displayed = 'old'; });
  const second = gate.begin();
  assert.equal(first.signal.aborted, true);
  if (second.isCurrent()) displayed = 'new';
  finishFirst(); await late;
  assert.equal(displayed, 'new');
  gate.cancel(); assert.equal(second.isCurrent(), false);
});
test('API repository uses only relative read endpoints and never falls back on errors', async () => {
  const originalFetch = globalThis.fetch;
  const calls: { url: string; method?: string }[] = [];
  try {
    globalThis.fetch = async (url, init) => {
      calls.push({ url: String(url), method: init?.method });
      return new Response(JSON.stringify(String(url).includes('/atlas?') ? detail : { topics: [topic] }), { status: 200 });
    };
    const repository = makeRepository('api', 'demo'); const signal = new AbortController().signal;
    assert.equal((await repository.list(signal))[0].id, 'atlas');
    assert.equal((await repository.detail('atlas', signal)).memories[0].type, 'question');
    assert.deepEqual(calls, [{ url: '/api/topics?workspaceId=demo', method: 'GET' }, { url: '/api/topics/atlas?workspaceId=demo', method: 'GET' }]);
    globalThis.fetch = async () => new Response('Unavailable', { status: 503 });
    await assert.rejects(repository.list(signal), /could not be loaded/);
    await assert.rejects(repository.detail('atlas', signal), /could not be loaded/);
  } finally { globalThis.fetch = originalFetch; }
});
test('fixtures retain a complete multi-topic source, typed memories, and sample identity', async () => {
  const repo = makeRepository('fixture', 'demo'); const signal = new AbortController().signal;
  const onboarding = await repo.detail('atlas-onboarding', signal);
  const camping = await repo.detail('camping-trip', signal);
  assert.equal(onboarding.memories[0].source.originalText, camping.memories[0].source.originalText);
  assert.ok(camping.memories[0].source.originalText?.includes('Atlas onboarding'));
  assert.deepEqual(onboarding.memories.slice(0, 2).map(m => m.type), ['idea', 'decision']);
  assert.equal(camping.memories[0].type, 'question');
  assert.ok(camping.memories[0].source.sample);
});

test('demo records have consistent counts, unique memory IDs, and coherent shared provenance', () => {
  const memoryIds = new Set<string>();
  const sources = new Map<string, unknown>();
  assert.equal(new Set(fixtureTopics.map(t => t.id)).size, fixtureTopics.length);
  for (const topic of scenarioTopics('crowded')) {
    const detail = sampleDetails(topic.id, topic);
    assert.equal(detail.memories.length, topic.memoryCount, topic.id);
    for (const memory of detail.memories) {
      assert.ok(!memoryIds.has(memory.id), `Duplicate memory: ${memory.id}`);
      memoryIds.add(memory.id);
      const source = memory.source;
      assert.equal(source.sample, true);
      assert.equal(source.url, undefined);
      assert.ok(source.author && source.channel && source.originalText);
      assert.ok(Number.isFinite(Date.parse(source.receivedAt)));
      assert.ok(Date.parse(source.receivedAt) <= Date.parse('2026-09-12T23:59:59Z'));
      if (sources.has(source.messageId)) assert.deepEqual(source, sources.get(source.messageId));
      sources.set(source.messageId, source);
    }
  }
  for (const update of fixtureUpdates) {
    assert.equal(update.sample, true);
    assert.equal(update.topicName, fixtureTopics.find(t => t.id === update.topicId)?.name);
  }
  const selected = fixtureTopics[0];
  const copy = sampleDetails(selected.id, selected);
  copy.memories[0].source.originalText = 'Changed by a QA scenario';
  assert.notEqual(sampleDetails(selected.id, selected).memories[0].source.originalText, copy.memories[0].source.originalText);
});
