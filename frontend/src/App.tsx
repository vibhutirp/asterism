import { lazy, Suspense, useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react';
import type { ReactNode } from 'react';
import { Activity, ArrowRight, CheckCircle2, ChevronDown, ChevronRight, ExternalLink, FileText, Info, List, Search, Sparkle, TriangleAlert, X } from 'lucide-react';
import type { Memory, Repository, Topic, Update } from './models.ts';
import { filterTopics, formatReceived, memoryTypeLabel } from './knowledge.ts';
import { makeRepository } from './repository.ts';
import { useKnowledge } from './useKnowledge.ts';
import { IconControl } from './IconControl.tsx';
import { AskCapture } from './AskCapture.tsx';

const configuredMode = import.meta.env.VITE_DATA_MODE || 'fixture';
const scenario = import.meta.env.DEV && configuredMode === 'fixture' ? new URLSearchParams(window.location.search).get('fixture') || '' : '';
const workspaceId = import.meta.env.VITE_WORKSPACE_ID || 'demo';
const repository = makeRepository(configuredMode === 'api' ? 'api' : 'fixture', workspaceId, scenario);
const CloudUniverse = lazy(() => import('./CloudUniverse.tsx'));
type Select = (id: string, element: HTMLElement) => void;

export function App() {
  if (!['fixture', 'api'].includes(configuredMode)) return <main className="configuration-error"><TriangleAlert /><h1>Data mode is not configured</h1><p>Set VITE_DATA_MODE to fixture or api before starting the reader.</p></main>;
  return <Workspace repository={repository} />;
}
function useCompact() {
  const [compact, setCompact] = useState(() => matchMedia('(max-width: 1023px)').matches);
  useEffect(() => { const q = matchMedia('(max-width: 1023px)'); const change = () => setCompact(q.matches);
    q.addEventListener('change', change); return () => q.removeEventListener('change', change); }, []);
  return compact;
}
function Workspace({ repository }: { repository: Repository }) {
  const state = useKnowledge(repository);
  const compact = useCompact();
  const [view, setView] = useState<'universe' | 'list'>(compact ? 'list' : 'universe');
  const [query, setQuery] = useState('');
  const [searchFocused, setSearchFocused] = useState(false);
  const viewSwitchRef = useRef<HTMLDivElement>(null);
  const [helpOpen, setHelpOpen] = useState(false);
  const helpButtonRef = useRef<HTMLButtonElement>(null);
  const opener = useRef<HTMLElement | null>(null);
  const searchRef = useRef<HTMLInputElement>(null);
  const headingRef = useRef<HTMLHeadingElement>(null);
  const [updatesOpen, setUpdatesOpen] = useState(false);
  const [sceneError, setSceneError] = useState('');
  const updatesButton = useRef<HTMLButtonElement>(null);
  const sceneFailed = useCallback(() => { setSceneError('3D exploration is unavailable on this device. You can still explore every topic in List.'); setView('list'); }, []);
  const visibleTopics = useMemo(() => filterTopics(state.topics, query), [state.topics, query]);
  const selectedTopic = state.topics.find(t => t.id === state.selectedId);
  const totalMemories = state.topics.reduce((n, t) => n + t.memoryCount, 0);
  const knowledgeLabel = state.loaded ? `${state.topics.length} ${state.topics.length === 1 ? 'topic' : 'topics'} · ${totalMemories} ${totalMemories === 1 ? 'memory' : 'memories'}` : state.loading ? 'Loading saved context…' : 'Saved context unavailable';
  const hasStatus = !!sceneError || !!state.error || !state.loaded || state.topics.length === 0 || visibleTopics.length === 0;
  const closeHelp = () => { setHelpOpen(false); helpButtonRef.current?.focus({ preventScroll: true }); };
  const switchView = (next: 'universe' | 'list') => { setHelpOpen(false); setView(next); };
  const select: Select = (id, element) => { opener.current = element; setUpdatesOpen(false); state.select(id); };
  const close = () => {
    const element = opener.current;
    // Focus first so the scene can retain the invoking label as selection clears.
    if (element?.isConnected && element.getClientRects().length && !element.closest('[hidden],[aria-hidden="true"]') && element.tabIndex >= 0) element.focus({ preventScroll: true });
    else searchRef.current?.focus({ preventScroll: true });
    state.select(null);
  };
  useEffect(() => { if (compact) { setView('list'); setHelpOpen(false); } }, [compact]);
  useLayoutEffect(() => {
    if (!state.selectedId) return;
    headingRef.current?.focus({ preventScroll: true });
    if (compact) {
      const frame = requestAnimationFrame(() => headingRef.current?.closest('.inspector')?.scrollIntoView({ block: 'start', behavior: 'instant' }));
      return () => cancelAnimationFrame(frame);
    }
  }, [state.selectedId, compact]);
  useEffect(() => { const escape = (event: KeyboardEvent) => {
    if (event.key !== 'Escape' || event.defaultPrevented) return;
    if (updatesOpen) { event.preventDefault(); setUpdatesOpen(false); updatesButton.current?.focus(); return; }
    if (helpOpen) { event.preventDefault(); closeHelp(); return; }
    if (state.selectedId) { event.preventDefault(); close(); }
  };
    window.addEventListener('keydown', escape); return () => window.removeEventListener('keydown', escape);
  });

  return <div className="app-shell" data-reduced-motion={import.meta.env.DEV && configuredMode === 'fixture' && new URLSearchParams(location.search).get('motion') === 'reduce' || undefined}>
    <a href="#topic-search" className="skip-link">Skip to topic search</a>
    <header className="app-header">
      <div className="brand"><span className="wordmark">Universe</span><span className="brand-rule" /><span className="header-counts">{knowledgeLabel}{state.loading && state.loaded && <span className="header-refresh">Refreshing…</span>}</span></div>
      <div className="workspace-status"><span className="origin-badge">{repository.mode === 'fixture' ? 'Sample data' : 'Connected data'}</span>
        <span className="connection-status"><Info size={16} aria-hidden="true" />{repository.mode === 'fixture' ? 'Demo workspace' : 'Connection status unavailable'}</span>
        <IconControl label="Recent updates" tipSide="below" ref={updatesButton} aria-expanded={updatesOpen} aria-controls="updates-popover" onClick={() => { setHelpOpen(false); setUpdatesOpen(v => !v); }}><Activity size={20} aria-hidden="true" /></IconControl>
      </div>
      {updatesOpen && <div id="updates-popover" className="updates-popover" data-scene-obstacle>
        <button className="icon-button popover-close" aria-label="Close recent updates" onClick={() => { setUpdatesOpen(false); updatesButton.current?.focus(); }}><X size={18} aria-hidden="true" /></button>
        <RecentUpdates updates={state.updates} onSelect={select} />
      </div>}
    </header>
    <main className={`workspace spatial-workspace ${state.selectedId ? 'has-selection' : ''} ${view === 'list' ? 'list-mode' : ''}`}>
      {!sceneError && <Suspense fallback={<div className="scene-starting" role="status">Preparing 3D exploration…</div>}><CloudUniverse topics={state.topics} visibleTopics={visibleTopics} selectedId={state.selectedId} updates={state.updates} onSelect={select} active={view === 'universe'} compact={compact} onFailure={sceneFailed} helpOpen={helpOpen} onHelpToggle={() => { setUpdatesOpen(false); setHelpOpen(v => !v); }} onHelpClose={closeHelp} helpButtonRef={helpButtonRef} /></Suspense>}
      <section className="explorer overlay-frame" aria-label="Explore your knowledge">
        <h1 className="sr-only">Your knowledge</h1>
        <div className="view-switch" role="group" aria-label="Knowledge view" ref={viewSwitchRef} data-scene-obstacle>
          <button aria-pressed={view === 'universe'} onClick={() => switchView('universe')} disabled={!!sceneError}><Sparkle size={16} aria-hidden="true" />Universe</button>
          <button aria-pressed={view === 'list'} onClick={() => switchView('list')}><List size={16} aria-hidden="true" />List</button>
        </div>
        <div className={`search-field floating-search ${searchFocused || query.length ? 'expanded' : ''}`} data-scene-obstacle
          onClick={() => searchRef.current?.focus()} onFocusCapture={() => setSearchFocused(true)}
          onBlurCapture={event => { if (!event.currentTarget.contains(event.relatedTarget)) setSearchFocused(false); }}
          onKeyDown={event => {
            if (event.key !== 'Escape') return;
            event.preventDefault(); event.stopPropagation();
            if (query.length) { setQuery(''); searchRef.current?.focus(); }
            else { setSearchFocused(false); viewSwitchRef.current?.querySelector<HTMLButtonElement>('[aria-pressed="true"]')?.focus(); }
          }}>
          <Search className="luminous-icon" size={18} aria-hidden="true" /><label className="sr-only" htmlFor="topic-search">Find topics by name</label>
          <input id="topic-search" ref={searchRef} aria-label="Find topics by name" placeholder="Search topics" value={query} onChange={e => setQuery(e.target.value)} autoComplete="off" />
          {query && <button type="button" className="icon-button clear-search" aria-label="Clear topic search" onClick={() => { setQuery(''); searchRef.current?.focus(); }}><X size={16} aria-hidden="true" /></button>}
        </div>
        <div className="workspace-content">
          {hasStatus && <div className="status-stack" data-scene-obstacle>
            {sceneError && <Notice error>{sceneError}</Notice>}
            {state.error && <Notice error action={() => void state.refreshTopics()}>{state.loaded ? `Showing previously loaded context. ${state.error}` : state.error}</Notice>}
            {!state.loaded ? <div className="explorer-empty">{state.loading ? <><Sparkle className="luminous-icon" size={28} /><h2>Loading your knowledge</h2><p>Reading saved topics and memories.</p></> : <><FileText size={28} /><h2>Knowledge is unavailable</h2><p>Your saved context will appear here when it can be loaded.</p></>}</div> : state.topics.length === 0 ?
              <div className="explorer-empty"><Sparkle className="luminous-icon" size={32} /><h2>No memories yet</h2><p>Memories appear here after conversations are saved through Slack or a connected service.</p></div> : visibleTopics.length === 0 ?
              <div className="explorer-empty"><Search size={28} /><h2>No topics match this name</h2><p>Try a different topic name or clear your search.</p><button className="secondary-button" onClick={() => { setQuery(''); searchRef.current?.focus(); }}>Clear search</button></div> : null}
          </div>}
          {state.loaded && visibleTopics.length > 0 && view === 'list' && <TopicList topics={visibleTopics} selectedId={state.selectedId} onSelect={select} updates={state.updates} />}
        </div>
      </section>
      {repository.mode === 'api' && <AskCapture workspace={workspaceId} onIngested={() => void state.refreshTopics()} />}
      {state.selectedId && <aside className="inspector" aria-label="Topic inspector" data-scene-obstacle>
        <>
          <div className="inspector-top"><span className="eyebrow">Topic details</span><button className="icon-button" aria-label="Close topic details" onClick={close}><X size={24} /></button></div>
          <h2 className="topic-title" tabIndex={-1} ref={headingRef}>{selectedTopic?.name || state.detail?.topic.name || 'Topic details'}</h2>
          {selectedTopic && <p className="topic-metadata"><span className={`category-mark ${selectedTopic.category.toLowerCase() === 'personal' ? 'personal' : ''}`} /><span>{selectedTopic.category}</span><span>·</span><span>{state.detail?.topic.memoryCount ?? selectedTopic.memoryCount} {(state.detail?.topic.memoryCount ?? selectedTopic.memoryCount) === 1 ? 'memory' : 'memories'}</span></p>}
          {state.detailError && <Notice error action={() => void state.refreshDetail()}>{state.detail ? `Showing previously loaded memories. ${state.detailError}` : state.detailError}</Notice>}
          {state.detailLoading && !state.detail && <div className="detail-loading" role="status"><FileText size={20} />Loading memories…</div>}
          {state.detail && <>
            <p className="source-summary"><FileText className="luminous-icon" size={22} aria-hidden="true" />From {Array.from(new Set(state.detail.memories.map(m => m.source.service))).join(', ') || 'sources not available'}</p>
            <section className="overview"><h3>{state.detail.summaryKind}</h3><p>{state.detail.summary || 'Overview unavailable'}</p></section>
            <div className="memory-list" aria-label="Memories">{state.detail.memories.map(memory => <MemoryRow memory={memory} key={memory.id} />)}
              {state.detail.memories.length === 0 && <p className="no-memories">No memories are available for this topic.</p>}
            </div>
          </>}
          <div className="inspector-footer"><Info size={20} aria-hidden="true" /><div><p>Memories arrive through Slack and connected services.</p><span>Previously saved context remains available.</span></div></div>
        </>
      </aside>}
    </main>
    <div className="sr-only" role="status" aria-live="polite">{state.announcement}</div>
  </div>;
}

function Notice({ children, error = false, action }: { children: ReactNode; error?: boolean; action?: () => void }) {
  return <div className={`notice ${error ? 'notice-error' : ''}`} role={error ? 'alert' : 'status'}><TriangleAlert size={18} aria-hidden="true" /><span>{children}</span>{action && <button className="text-button" onClick={action}>Try again</button>}</div>;
}

function TopicList({ topics, selectedId, onSelect, updates }: { topics: Topic[]; selectedId: string | null; onSelect: Select; updates: Update[] }) {
  return <div className="topic-list" aria-label="Topic list">{topics.map(t => <button className={`topic-list-row ${selectedId === t.id ? 'selected' : ''}`} key={t.id} aria-pressed={selectedId === t.id} onClick={e => onSelect(t.id, e.currentTarget)}>
    <Sparkle className={`list-star ${t.category.toLowerCase() === 'personal' ? 'personal' : ''}`} size={20} aria-hidden="true" />
    <span className="list-topic-text"><span>{t.name}</span><span className="list-metadata">{t.category} · {t.memoryCount} {t.memoryCount === 1 ? 'memory' : 'memories'}</span></span>
    {updates.some(u => u.topicId === t.id) && <span className="update-badge">{updates.find(u => u.topicId === t.id)?.label}</span>}<ChevronRight size={18} aria-hidden="true" />
  </button>)}</div>;
}
function RecentUpdates({ updates, onSelect }: { updates: Update[]; onSelect: Select }) {
  return <section className="recent-updates"><h2>Recent updates</h2>{updates.length ? updates.slice(0, 3).map(update => <div className="update-row" key={update.topicId}>
    <CheckCircle2 className="saved-icon" size={28} aria-hidden="true" /><div><p>{update.topicName} {update.label.toLowerCase()}</p><span>{update.note}</span></div>
    <button className="text-button" onClick={e => onSelect(update.topicId, e.currentTarget)}>View topic <ArrowRight size={18} aria-hidden="true" /></button>
  </div>) : <p className="updates-empty">New topic updates will appear here as they are observed.</p>}</section>;
}
function MemoryRow({ memory }: { memory: Memory }) {
  const [expanded, setExpanded] = useState(false);
  const sourceId = `source-${memory.id}`;
  const source = memory.source;
  return <article className="memory-row">
    <span className="memory-type">{memoryTypeLabel(memory.type)}</span><p className="memory-text">{memory.text}</p>
    <p className="memory-attribution">{[source.author, source.service].filter(Boolean).join(' · ')}<span>Received {formatReceived(source.receivedAt)}</span></p>
    {source.originalText ? <>
      <button className="disclosure" aria-expanded={expanded} aria-controls={sourceId} onClick={() => setExpanded(x => !x)}><ChevronDown className={expanded ? 'expanded' : ''} size={18} aria-hidden="true" />{expanded ? 'Hide original' : 'View original'}</button>
      {expanded && <div className="original-source" id={sourceId}><h4><FileText size={18} className="luminous-icon" aria-hidden="true" />Original message</h4>
        <p className="source-attribution">{[source.author, source.channel || source.service].filter(Boolean).join(' · ')}<span>Received {formatReceived(source.receivedAt)}</span></p>
        <blockquote>{source.originalText}</blockquote><span className="sample-source">{source.sample ? 'Sample source' : 'Original source'}</span>
      </div>}
    </> : <p className="source-unavailable"><Info size={16} aria-hidden="true" />Original text unavailable</p>}
    {source.url && <a className="source-link" href={source.url} target="_blank" rel="noopener noreferrer">Open in {source.service}<ExternalLink size={15} aria-hidden="true" /><span className="sr-only"> (opens in a new tab)</span></a>}
  </article>;
}
