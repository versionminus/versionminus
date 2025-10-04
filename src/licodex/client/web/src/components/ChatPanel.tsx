import React, { useCallback, useEffect, useRef, useState } from 'react';
// Import from package root; deep path '@licodex/sdk/lib/hooks/useLicodex' does not exist in published package.
import type { UseLicodexReturn, Note, Message } from '@licodex/sdk';

interface ChatLine { role: 'user' | 'assistant'; content: string; ts: number; }

interface Props { licodex: UseLicodexReturn; selectedNote: Note | null; selectedThreadId: string | null }

export function ChatPanel({ licodex, selectedNote, selectedThreadId }: Props) {
  const [input, setInput] = useState('');
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

  if (!selectedThreadId) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', flexDirection: 'column', opacity: 0.7 }}>
        <div style={{ fontSize: 14 }}>Select a thread from the left sidebar to start chatting.</div>
        <div style={{ fontSize: 12, marginTop: 8 }}>Create a new thread to begin a stateful conversation.</div>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div className="terminal-titlebar">
        <div className="window-dot red" />
        <div className="window-dot amber" />
        <div className="window-dot green" />
        <span style={{ opacity: .7 }}>licodex / chat</span>
      </div>
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
          placeholder={selectedNote ? `Ask about: ${selectedNote.title}` : 'Ask a question...'}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey && selectedThreadId) { e.preventDefault(); void send(); } }}
        />
        <button className="btn primary" onClick={() => void send()} disabled={!input.trim() || !selectedThreadId}>Send</button>
      </div>
    </div>
  );
}
