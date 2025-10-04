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
}
export function ChatPanel({ licodex, selectedNote, selectedThreadId, onThreadDeleted }: Props) {
  const [input, setInput] = useState('');
  const [resetting, setResetting] = useState(false);
  // Local optimistic lines for instant UX before reload (persisted history comes from licodex.messages)
  const [localPending, setLocalPending] = useState<ChatLine[]>([]);
  const bottomRef = useRef<HTMLDivElement | null>(null);
  const appendLocal = useCallback((line: ChatLine) => setLocalPending(h => [...h, line]), []);

  const send = useCallback(async () => {
    if (!input.trim() || !selectedThreadId) return;
    const q = input.trim();
    appendLocal({ role: 'user', content: q, ts: Date.now() });
    setInput('');
    await licodex.sendChatMessage(selectedThreadId, q);
    setTimeout(() => setLocalPending([]), 200);
  }, [appendLocal, input, licodex, selectedThreadId]);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }); });

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
            {licodex.messages.data?.map((m: Message) => (
              <div key={m.id + m.response}>
                <div className='chat-line-user'>you &gt; {m.content}</div>
                {m.response && <div className='chat-line-bot'>licodex &gt; {m.response}</div>}
              </div>
            ))}
            {/* Optimistic local lines not yet persisted */}
            {localPending.map(l => (
              <div key={l.ts} className={l.role === 'user' ? 'chat-line-user' : 'chat-line-bot'}>
                {l.role === 'user' ? 'you \u003e ' : 'licodex \u003e '}{l.content}
              </div>
            ))}
            {licodex.messages.loading && <div className="chat-line-bot fade-text">loading...</div>}
            <div ref={bottomRef} />
          </div>
          <div className="chat-prompt">
            <input
              className="input prompt-input"
              placeholder='Ask a question...'
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey && selectedThreadId) { e.preventDefault(); void send(); } }}
            />
            <button className="btn" title="Send" onClick={() => void send()} disabled={!input.trim() || !selectedThreadId}><Icon name="send" size={ICON_SIZE} /></button>
          </div>
        </>
      )}
    </div>
  );
}
