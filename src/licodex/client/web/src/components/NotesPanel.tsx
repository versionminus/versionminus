import React, { useCallback, useState } from 'react';
// Use root export for all SDK types; deep import `@licodex/sdk/lib/types` breaks because of path mapping.
import type { Note, AsyncState } from '@licodex/sdk';

interface Props {
  notesState: AsyncState<Note[]>;
  selected?: string;
  onSelect: (n: Note) => void;
  onCreate: (content: string) => Promise<void>;
  onUpdate: (id: string, content: string) => Promise<void>;
  onDelete: (id: string) => Promise<void>;
}

export function NotesPanel({ notesState, selected, onSelect, onCreate, onUpdate, onDelete }: Props) {
  const [editorContent, setEditorContent] = useState('');
  const [editingId, setEditingId] = useState<string | null>(null);

  const startEdit = useCallback((n: Note) => { setEditingId(n.id); setEditorContent(n.content); }, []);
  const cancelEdit = useCallback(() => { setEditingId(null); setEditorContent(''); }, []);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div className="terminal-titlebar"><span style={{ opacity: .7 }}>notes</span></div>
      <div style={{ padding: 8, display: 'flex', flexDirection: 'column', gap: 8, flex: 1, overflow: 'hidden' }}>
        <div style={{ display: 'flex', gap: 8 }}>
          <button className="btn primary" onClick={() => { setEditingId('new'); setEditorContent(''); }}>+ note</button>
          {editingId && <button className="btn" onClick={cancelEdit}>cancel</button>}
          {editingId && editingId !== 'new' && <button className="btn danger" onClick={() => { void onDelete(editingId); cancelEdit(); }}>delete</button>}
        </div>
        <div style={{ display: 'flex', gap: 8, flex: 1, overflow: 'hidden' }}>
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 8, overflow: 'hidden' }}>
            <div className="note-list scrollbar-thin" style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {notesState.loading && <div className="fade-text">loading notes...</div>}
              {/* Only show the error if we actually have some existing notes data. If there are none, treat as normal empty state. */}
              {notesState.error && (notesState.data?.length || 0) > 0 && (
                <div className="fade-text" style={{ color: 'var(--danger)' }}>error loading notes</div>
              )}
              {notesState.data?.map(n => (
                <div
                  key={n.id}
                  className={`note-item ${selected === n.id ? 'active' : ''}`}
                  onClick={() => { onSelect(n); startEdit(n); }}
                >
                  <div className="note-title">{(n.content.split('\n')[0] || 'Untitled').slice(0,80)}</div>
                  <div className="note-content-snippet">{n.content.slice(0, 60)}</div>
                </div>
              ))}
              {!notesState.loading && !(notesState.data?.length) && <div className="fade-text">no notes yet</div>}
            </div>
          </div>
          <div style={{ flex: 2, display: 'flex', flexDirection: 'column' }}>
            {editingId && (
              <>
                <textarea
                  style={{ flex: 1, resize: 'none', fontSize: 12, lineHeight: 1.4 }}
                  value={editorContent}
                  onChange={e => setEditorContent(e.target.value)}
                  placeholder="Write your note here..."
                  className="scrollbar-thin"
                />
                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 6 }}>
                  {editingId === 'new' ? (
                    <button className="btn primary" disabled={!editorContent.trim()} onClick={() => { void onCreate(editorContent); cancelEdit(); }}>save</button>
                  ) : (
                    <button className="btn primary" disabled={!editorContent.trim()} onClick={() => { void onUpdate(editingId, editorContent); cancelEdit(); }}>update</button>
                  )}
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
