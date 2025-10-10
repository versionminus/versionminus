import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Icon, ICON_SIZE } from './Icon';
// Import from package root; deep path '@licodex/sdk/lib/hooks/useLicodex' does not exist in published package.
import type { UseLicodexReturn, Note, Message } from '@licodex/sdk';

interface ChatLine { role: 'user' | 'assistant'; content: string; ts: number; }

interface Props {
  licodex: UseLicodexReturn;
  selectedNote: Note | null;
  selectedThreadId: string | null;
  onThreadDeleted?: (id: string) => void;
  onOpenNote?: (noteId: string) => void; // open note in editor (from source click)
}
export function ChatPanel({ licodex, selectedNote, selectedThreadId, onThreadDeleted, onOpenNote }: Props) {
  const [input, setInput] = useState('');
  const [resetting, setResetting] = useState(false);
  // Local optimistic lines for instant UX before reload (persisted history comes from licodex.messages)
  const [localPending, setLocalPending] = useState<ChatLine[]>([]);
  const bottomRef = useRef<HTMLDivElement | null>(null);
  const appendLocal = useCallback((line: ChatLine) => setLocalPending(h => [...h, line]), []);
  const [openSourcesFor, setOpenSourcesFor] = useState<string | null>(null);
  const [dots, setDots] = useState('');
  const toggleSources = useCallback(async (m: Message) => {
    if (!m.source) return;
    if (openSourcesFor === m.id) { setOpenSourcesFor(null); return; }
    // load sources if not already cached
    if (!licodex.sourcesByGroup[m.source]) {
      await licodex.loadSources(m.source);
    }
    setOpenSourcesFor(m.id);
  }, [licodex, openSourcesFor]);

  const send = useCallback(async () => {
    if (!input.trim() || !selectedThreadId) return;
    const q = input.trim();
    appendLocal({ role: 'user', content: q, ts: Date.now() });
    setInput('');
    await licodex.sendChatMessage(selectedThreadId, q);
  }, [appendLocal, input, licodex, selectedThreadId]);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }); });

  // Determine if there is a pending assistant response (latest message without response)
  const pendingMessage = (() => {
    const msgs = licodex.messages.data?.filter(m => m.thread_id === selectedThreadId) || [];
    for (let i = msgs.length - 1; i >= 0; i--) {
      const m = msgs[i];
      if (!m.response || m.response.trim() === '') return m;
    }
    return null;
  })();

  // Animate thinking dots while pending
  useEffect(() => {
    if (pendingMessage) {
      const id = setInterval(() => setDots(d => (d.length >= 3 ? '' : d + '.')), 400);
      return () => clearInterval(id);
    } else {
      setDots('');
    }
  }, [pendingMessage]);

  // Clear local pending lines when their persisted counterpart (with response) arrives
  useEffect(() => {
    if (!localPending.length) return;
    const msgs = licodex.messages.data?.filter(m => m.thread_id === selectedThreadId) || [];
    // If every local user line has a persisted message (regardless of response), drop optimistic copies
    const allMatched = localPending.every(lp => msgs.some(m => m.content === lp.content));
    if (allMatched) {
      // Keep them until at least one matched message has a response to maintain waiting state
      const anyResponded = msgs.some(m => localPending.some(lp => lp.content === m.content) && m.response && m.response.trim() !== '');
      if (anyResponded) setLocalPending([]);
    }
  }, [licodex.messages.data, localPending, selectedThreadId]);

  const waiting = localPending.length > 0 || !!pendingMessage;

  const thread = licodex.threads.data?.find(t => t.id === selectedThreadId);

  const renameThread = useCallback(async () => {
    if (!thread) return;
    const current = thread.title || '';
    const title = window.prompt('Rename thread', current);
    if (title && title.trim() && title !== current) {
      await licodex.updateThread(thread.id, { title: title.trim(), user_id: thread.user_id });
    }
  }, [licodex, thread]);

  const deleteThread = useCallback(async () => {
    if (!thread) return;
    if (!window.confirm('Delete this thread and all its messages?')) return;
    await licodex.deleteThread(thread.id);
    onThreadDeleted?.(thread.id);
  }, [licodex, onThreadDeleted, thread]);

  const resetThread = useCallback(async () => {
    if (!thread) return;
    if (!window.confirm('Delete ALL messages in this thread (reset conversation)?')) return;
    try {
      setResetting(true);
      // Ensure we have latest messages loaded
      await licodex.loadMessages(thread.id);
      const msgs = licodex.messages.data?.filter(m => m.thread_id === thread.id) || [];
      // Delete sequentially to avoid hammering backend; order doesn't matter
      for (const m of msgs) {
        try { await licodex.client.deleteMessage(m.id); } catch (e) { console.error(e); }
      }
      await licodex.loadMessages(thread.id);
    } finally {
      setResetting(false);
    }
  }, [licodex, thread]);

  if (!selectedThreadId) return null; // Only render when a thread is active (Quotes or Note editor shown elsewhere otherwise)

  return (
    <div className="flex-col-full">
      <div className="terminal-titlebar gap-8">
        <span className="muted-grow">{thread?.title || (selectedNote ? 'note' : '')}</span>
        {thread && (
          <div className="btn-row">
            <button className="btn outline small" title="Rename thread" onClick={() => void renameThread()}><Icon name="edit" size={ICON_SIZE} /></button>
            <button className="btn outline small" title="Reset messages" disabled={resetting || licodex.messages.loading} onClick={() => void resetThread()}><Icon name="refresh" size={ICON_SIZE} /></button>
            <button className="btn danger small" title="Delete thread" onClick={() => void deleteThread()}><Icon name="trash" size={ICON_SIZE} /></button>
          </div>
        )}
      </div>
      {selectedThreadId && (
        <>
          <div className="chat-history scrollbar-thin">
            {/* Persisted messages from backend */}
            {licodex.messages.data?.map((m: Message) => {
              const sourcesId = m.source;
              const cached = sourcesId ? licodex.sourcesByGroup[sourcesId] : undefined;
              return (
                <div key={m.id + m.response}>
                  <div className='chat-line-user'>you &gt; {m.content}</div>
                  {m.response && (
                    <div className='chat-line-bot'>
                      licodex &gt; {m.response}
                      {sourcesId && (
                        <button
                          className='btn tiny outline ml-4'
                          style={{ marginLeft: 8 }}
                          title={openSourcesFor === m.id ? 'Hide sources' : 'Show sources'}
                          onClick={() => void toggleSources(m)}
                        >
                          <Icon name='expand' size={12} />
                        </button>
                      )}
                    </div>
                  )}
                  {openSourcesFor === m.id && sourcesId && (
                    <div className='terminal-box mt-2'>
                      {!cached && <div className='fade-text'>loading sources...</div>}
                      {cached && cached.map(s => {
                        const dist = typeof s.distance === 'number' ? s.distance.toFixed(3) : undefined;
                        return (
                          <div key={s.note_id} className='source-line'>
                            <span
                              className='source-note-id'
                              title='Open note (click)'
                              onClick={() => onOpenNote?.(s.note_id)}
                            >
                              {s.note_id}
                            </span>
                            {dist && (
                              <span className='badge distance-badge' title='Vector distance (lower is closer)'>
                                {dist}
                              </span>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              );
            })}
            {/* Optimistic local lines not yet persisted */}
            {localPending.map(l => (
              <div key={l.ts} className={l.role === 'user' ? 'chat-line-user' : 'chat-line-bot'}>
                {l.role === 'user' ? 'you \u003e ' : 'licodex \u003e '}{l.content}
              </div>
            ))}
            {licodex.messages.loading && <div className="chat-line-bot fade-text">loading...</div>}
            {/* Thinking animation for pending assistant response */}
            {(waiting) && (
              <div className='chat-line-bot thinking-line'>
                licodex &gt; <span className='thinking-dots'>{dots}</span><span className='cursor-block' />
              </div>
            )}
            {/* Inline prompt (terminal style) only when not waiting for assistant */}
            {!waiting && (
              <div className='chat-line-user prompt-line'>
                <span>you &gt; </span>
                <input
                  className='prompt-input-inline'
                  autoFocus
                  value={input}
                  placeholder=''
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey && selectedThreadId) { e.preventDefault(); void send(); } }}
                />
                <button
                  className='btn outline inline-send'
                  title='Send'
                  onClick={() => void send()}
                  disabled={!input.trim() || !selectedThreadId}
                >
                  <Icon name='send' size={ICON_SIZE} />
                </button>
              </div>
            )}
            <div ref={bottomRef} />
          </div>
        </>
      )}
    </div>
  );
}
