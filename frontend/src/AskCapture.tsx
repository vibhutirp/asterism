import { useState } from 'react';
import { MessageCirclePlus, Send, Sparkle } from 'lucide-react';
import { ask, sendMessage } from './actions.ts';
import type { AskResult } from './actions.ts';

// Minimal write/ask wiring for API mode: save messages into memory, ask grounded questions.
export function AskCapture({ workspace, onIngested }: { workspace: string; onIngested: () => void }) {
  const [text, setText] = useState('');
  const [busy, setBusy] = useState<'save' | 'ask' | null>(null);
  const [status, setStatus] = useState('');
  const [statusError, setStatusError] = useState(false);
  const [answer, setAnswer] = useState<AskResult | null>(null);

  const trimmed = text.trim();

  async function save() {
    if (!trimmed || busy) return;
    setBusy('save'); setAnswer(null); setStatus(''); setStatusError(false);
    try {
      const result = await sendMessage(workspace, trimmed);
      setStatus(result.duplicate
        ? 'That message was already saved.'
        : result.memoriesCreated === 0
          ? 'Nothing memorable was found in that message.'
          : `Saved ${result.memoriesCreated} ${result.memoriesCreated === 1 ? 'memory' : 'memories'} into: ${result.topicNames.join(', ')}`);
      setText('');
      onIngested();
    } catch (e) {
      setStatus(e instanceof Error ? e.message : 'The message could not be saved.'); setStatusError(true);
    } finally { setBusy(null); }
  }

  async function submitAsk() {
    if (!trimmed || busy) return;
    setBusy('ask'); setStatus(''); setStatusError(false); setAnswer(null);
    try {
      setAnswer(await ask(workspace, trimmed));
    } catch (e) {
      setStatus(e instanceof Error ? e.message : 'The question could not be answered.'); setStatusError(true);
    } finally { setBusy(null); }
  }

  return <section className="ask-capture" aria-label="Save a message or ask a question" data-scene-obstacle>
    <label className="sr-only" htmlFor="ask-capture-input">Message or question</label>
    <textarea id="ask-capture-input" rows={2} placeholder="Write a message to remember, or ask a question…"
      value={text} onChange={e => setText(e.target.value)}
      onKeyDown={e => { if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) { e.preventDefault(); void save(); } }} />
    <div className="ask-capture-actions">
      <button className="secondary-button" disabled={!trimmed || !!busy} onClick={() => void save()}>
        <MessageCirclePlus size={16} aria-hidden="true" />{busy === 'save' ? 'Saving…' : 'Save memory'}
      </button>
      <button className="secondary-button" disabled={!trimmed || !!busy} onClick={() => void submitAsk()}>
        <Send size={16} aria-hidden="true" />{busy === 'ask' ? 'Asking…' : 'Ask'}
      </button>
    </div>
    {status && <p className={`ask-capture-status ${statusError ? 'error' : ''}`} role="status">{status}</p>}
    {answer && <div className="ask-capture-answer" role="status">
      {answer.insufficientContext
        ? <p className="insufficient"><Sparkle size={16} aria-hidden="true" />Not enough stored context to answer that yet. Save some related memories first.</p>
        : <>
          <p>{answer.answer}</p>
          <span className="answer-sources">Grounded in {answer.sourceCount} {answer.sourceCount === 1 ? 'stored memory' : 'stored memories'}</span>
        </>}
    </div>}
  </section>;
}
