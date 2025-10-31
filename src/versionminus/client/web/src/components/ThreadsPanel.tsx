import React, { useCallback, useState } from 'react';
import { Icon, ICON_SIZE } from './Icon';
import type { Thread } from '@versionminus/sdk';

interface Props {
  threads: Thread[] | undefined;
  loading: boolean;
  error?: Error;
  selected?: string | null;
  onSelect: (t: Thread) => void;
  onCreate: (title: string) => Promise<void>;
  onRename: (id: string, title: string) => Promise<void>;
  onDelete: (id: string) => Promise<void>;
  onToggleList?: () => void;
  listVisible?: boolean;
}

export function ThreadsPanel({
  threads,
  loading,
  error,
  selected,
  onSelect,
  onCreate,
  onRename,
  onDelete,
  onToggleList,
  listVisible,
}: Props) {
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
        <span className="muted">think</span>
        <div className="actions-row">
          <button className="btn" title="New thinking session" onClick={startNew}><Icon name="plus" size={ICON_SIZE} /></button>
          {onToggleList && (
            <button
              className="btn outline"
              title={listVisible ? 'Hide thinking sessions' : 'Show thinking sessions'}
              onClick={onToggleList}
            >
              <Icon name="think" size={ICON_SIZE} />
            </button>
          )}
          {editingId && <button className="btn outline" title="Cancel" onClick={cancel}><Icon name="x" size={ICON_SIZE} /></button>}
        </div>
      </div>
      <div className="panel-body" style={{ padding: 0 }}>
        <div className="scrollbar-thin scroll-flex-col" style={{ gap: 0 }}>
          {loading && <div className="fade-text">loading thinking sessions...</div>}
            {error && <div className="fade-text" style={{ color: 'var(--danger)' }}>error loading thinking sessions</div>}
          {threads?.map(t => (
            <div
              key={t.id}
              className={`note-item thread-item ${selected === t.id ? 'active' : ''}`}
              onClick={() => onSelect(t)}
              onDoubleClick={() => startRename(t)}
              title={t.title || 'Untitled session'}
            >
              <div className="note-title">{t.title || 'Untitled session'}</div>
            </div>
          ))}
          {!loading && !(threads?.length) && <div className="fade-text">no thinking sessions yet</div>}
        </div>
        {editingId && (
          <div className="btn-row" style={{ width: '100%' }}>
            <input
              className="input"
              placeholder={editingId === 'new' ? 'New thinking session' : 'Rename thinking session'}
              value={draft}
              onChange={e => setDraft(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); void save(); } }}
              autoFocus
              style={{ flex: 1 }}
            />
            {editingId !== 'new' && (
              <button
                className="btn danger"
                title="Delete"
                onClick={() => { void onDelete(editingId); cancel(); }}
              >
                <Icon name="trash" size={ICON_SIZE} />
              </button>
            )}
            <button className="btn" title="Save" disabled={!draft.trim()} onClick={() => { void save(); }}><Icon name="check" size={ICON_SIZE} /></button>
          </div>
        )}
      </div>
    </div>
  );
}
