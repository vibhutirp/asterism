import { useCallback, useEffect, useRef, useState } from 'react';
import type { Repository, Topic, TopicDetail, Update } from './models.ts';
import { createRequestGate, observedUpdates } from './knowledge.ts';
import { fixtureUpdates } from './fixtures.ts';

const message = (e: unknown) => e instanceof Error ? e.message : 'Stored context could not be loaded.';
export function useKnowledge(repository: Repository) {
  const [topics, setTopics] = useState<Topic[]>([]);
  const [loaded, setLoaded] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<TopicDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState('');
  const [updates, setUpdates] = useState<Update[]>([]);
  const [announcement, setAnnouncement] = useState('');
  const previous = useRef<Topic[] | null>(null);
  const listGate = useRef(createRequestGate());
  const detailGate = useRef(createRequestGate());

  const refreshTopics = useCallback(async () => {
    const request = listGate.current.begin();
    setLoading(true);
    try {
      const next = await repository.list(request.signal);
      if (!request.isCurrent()) return;
      if (previous.current && repository.mode === 'api') {
        const changed = observedUpdates(previous.current, next);
        if (changed.length) {
          setUpdates(old => [...changed, ...old.filter(u => !changed.some(c => c.topicId === u.topicId))].slice(0, 5));
          setAnnouncement(`${changed.length} ${changed.length === 1 ? 'topic updated' : 'topics updated'}.`);
        }
      }
      if (!previous.current && repository.mode === 'fixture') setUpdates(fixtureUpdates);
      previous.current = next; setTopics(next); setLoaded(true); setError('');
      setUpdates(old => old.filter(u => next.some(t => t.id === u.topicId)));
    } catch (e) { if (request.isCurrent()) setError(message(e)); }
    finally { if (request.isCurrent()) setLoading(false); }
  }, [repository]);

  const refreshDetail = useCallback(async () => {
    if (!selectedId) return;
    const request = detailGate.current.begin();
    setDetailLoading(true);
    try {
      const next = await repository.detail(selectedId, request.signal);
      if (request.isCurrent()) { setDetail(next); setDetailError(''); }
    } catch (e) { if (request.isCurrent()) setDetailError(message(e)); }
    finally { if (request.isCurrent()) setDetailLoading(false); }
  }, [repository, selectedId]);

  const select = useCallback((id: string | null) => {
    if (id === selectedId) return;
    detailGate.current.cancel(); setDetail(null); setDetailError(''); setDetailLoading(!!id); setSelectedId(id);
  }, [selectedId]);
  useEffect(() => { void refreshTopics(); return () => listGate.current.cancel(); }, [refreshTopics]);
  useEffect(() => { void refreshDetail(); return () => detailGate.current.cancel(); }, [refreshDetail]);
  useEffect(() => {
    const refresh = () => { if (document.visibilityState === 'visible') { void refreshTopics(); void refreshDetail(); } };
    const visibility = () => {
      if (document.visibilityState === 'visible') refresh();
      else { listGate.current.cancel(); detailGate.current.cancel(); }
    };
    const timer = window.setInterval(refresh, 10000);
    document.addEventListener('visibilitychange', visibility);
    window.addEventListener('focus', refresh);
    return () => { clearInterval(timer); document.removeEventListener('visibilitychange', visibility); window.removeEventListener('focus', refresh); };
  }, [refreshTopics, refreshDetail]);

  return { topics, loaded, loading, error, selectedId, detail, detailLoading, detailError,
    updates, announcement, select, refreshTopics, refreshDetail };
}
