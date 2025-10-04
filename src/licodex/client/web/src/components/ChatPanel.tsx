import React, { useCallback, useEffect, useRef, useState } from 'react';
import type { UseLicodexReturn } from '@licodex/sdk/lib/hooks/useLicodex';
import type { Note } from '@licodex/sdk';

interface ChatLine { role: 'user' | 'assistant'; content: string; ts: number; }

interface Props { licodex: UseLicodexReturn; selectedNote: Note | null }

export function ChatPanel({ licodex, selectedNote }: Props) {
  const [input, setInput] = useState('');
  const [history, setHistory] = useState<ChatLine[]>([]);
  const bottomRef = useRef<HTMLDivElement | null>(null);

  const append = useCallback((line: ChatLine) => setHistory(h => [...h, line]), []);

  const send = useCallback(async () => {
    if (!input.trim()) return;
    const q = input.trim();
    append({ role: 'user', content: q, ts: Date.now() });
    setInput('');
    const answer = await licodex.ask({ question: q, noteIds: selectedNote ? [selectedNote.id] : undefined });
    if (answer) {
      append({ role: 'assistant', content: answer.answer, ts: Date.now() });
    }
  }, [append, input, licodex, selectedNote]);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }); });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div className="terminal-titlebar">
        <div className="window-dot red" />
        <div className="window-dot amber" />
        <div className="window-dot green" />
        <span style={{ opacity: .7 }}>licodex / chat</span>
      </div>
      <div className="chat-history scrollbar-thin">
        {history.map(l => (
          <div key={l.ts} className={l.role === 'user' ? 'chat-line-user' : 'chat-line-bot'}>
            {l.role === 'user' ? 'you > ' : 'licodex > '}{l.content}
          </div>
        ))}
        {licodex.asking && <div className="chat-line-bot fade-text">thinking...</div>}
        <div ref={bottomRef} />
      </div>
      <div className="chat-prompt">
        <input
          className="input prompt-input"
          placeholder={selectedNote ? `Ask about: ${selectedNote.title}` : 'Ask a question...'}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); void send(); } }}
        />
        <button className="btn primary" onClick={() => void send()} disabled={!input.trim() || licodex.asking}>Send</button>
      </div>
    </div>
  );
}
