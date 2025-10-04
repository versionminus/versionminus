import React, { useCallback, useState } from 'react';
import type { Thread } from '@licodex/sdk';

interface Props {
  threads: Thread[] | undefined;
  loading: boolean;
  error?: Error;
  selected?: string | null;
  onSelect: (t: Thread) => void;
  onCreate: (title: string) => Promise<void>;
  onRename: (id: string, title: string) => Promise<void>;
  onDelete: (id: string) => Promise<void>;
}

export function ThreadsPanel({ threads, loading, error, selected, onSelect, onCreate, onRename, onDelete }: Props) {
  const [editingId, setEditingId] = useState<string | null>(null);
  const [draft, setDraft] = useState('');

  const startNew = useCallback(() => { setEditingId('new'); setDraft(''); }, []);
  const startRename = useCallback((t: Thread) => { setEditingId(t.id); setDraft(t.title); }, []);
  const cancel = useCallback(() => { setEditingId(null); setDraft(''); }, []);

  const save = useCallback(async () => {
    if (!draft.trim()) return;
    if (editingId === 'new') {
      await onCreate(draft.trim());
    } else if (editingId) {
      await onRename(editingId, draft.trim());
    }
    cancel();
  }, [draft, editingId, onCreate, onRename, cancel]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div className="terminal-titlebar"><span style={{ opacity: .7 }}>threads</span></div>
      <div style={{ padding: 8, display: 'flex', flexDirection: 'column', gap: 8, flex: 1, overflow: 'hidden' }}>
        <div style={{ display: 'flex', gap: 8 }}>
          <button className="btn primary" onClick={startNew}>+ thread</button>
          {editingId && <button className="btn" onClick={cancel}>cancel</button>}
          {editingId && editingId !== 'new' && <button className="btn danger" onClick={() => { void onDelete(editingId); cancel(); }}>delete</button>}
        </div>
        <div className="scrollbar-thin" style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 6, overflowY: 'auto' }}>
          {loading && <div className="fade-text">loading threads...</div>}
            {error && <div className="fade-text" style={{ color: 'var(--danger)' }}>error loading threads</div>}
          {threads?.map(t => (
            <div
              key={t.id}
              className={`note-item ${selected === t.id ? 'active' : ''}`}
              onClick={() => onSelect(t)}
              onDoubleClick={() => startRename(t)}
            >
              <div className="note-title">{t.title || 'Untitled thread'}</div>
            </div>
          ))}
          {!loading && !(threads?.length) && <div className="fade-text">no threads yet</div>}
        </div>
        {editingId && (
          <div style={{ display: 'flex', gap: 6 }}>
            <input
              className="input"
              placeholder={editingId === 'new' ? 'New thread title' : 'Rename thread'}
              value={draft}
              onChange={e => setDraft(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); void save(); } }}
              autoFocus
              style={{ flex: 1 }}
            />
            <button className="btn primary" disabled={!draft.trim()} onClick={() => { void save(); }}>save</button>
          </div>
        )}
      </div>
    </div>
  );
}
