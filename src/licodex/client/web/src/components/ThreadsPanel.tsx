import React, { useCallback, useState } from 'react';
import { Icon } from './Icon';
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
    <div className="flex-col-full">
      <div className="terminal-titlebar gap-6">
        <span className="muted">threads</span>
        <div className="actions-row">
          <button className="btn" title="New thread" onClick={startNew}><Icon name="plus" /></button>
          {editingId && <button className="btn outline" title="Cancel" onClick={cancel}><Icon name="x" /></button>}
          {editingId && editingId !== 'new' && <button className="btn danger" title="Delete" onClick={() => { void onDelete(editingId); cancel(); }}><Icon name="trash" /></button>}
        </div>
      </div>
      <div className="panel-body">
        <div className="scrollbar-thin scroll-flex-col">
          {loading && <div className="fade-text">loading threads...</div>}
            {error && <div className="fade-text" style={{ color: 'var(--danger)' }}>error loading threads</div>}
          {threads?.map(t => (
            <div
              key={t.id}
              className={`note-item thread-item ${selected === t.id ? 'active' : ''}`}
              onClick={() => onSelect(t)}
              onDoubleClick={() => startRename(t)}
            >
              <div className="note-title">{t.title || 'Untitled thread'}</div>
            </div>
          ))}
          {!loading && !(threads?.length) && <div className="fade-text">no threads yet</div>}
        </div>
        {editingId && (
          <div className="btn-row" style={{ width: '100%' }}>
            <input
              className="input"
              placeholder={editingId === 'new' ? 'New thread title' : 'Rename thread'}
              value={draft}
              onChange={e => setDraft(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); void save(); } }}
              autoFocus
              style={{ flex: 1 }}
            />
            <button className="btn" title="Save" disabled={!draft.trim()} onClick={() => { void save(); }}><Icon name="check" /></button>
          </div>
        )}
      </div>
    </div>
  );
}
